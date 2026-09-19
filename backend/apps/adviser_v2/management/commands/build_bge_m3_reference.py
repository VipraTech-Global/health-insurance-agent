"""Build frozen full-precision BGE-M3 rankings from the curated corpus."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.adviser_v2.embedding import BGE_MODEL_NAME, embed_texts_from_onnx, sha256_file
from apps.adviser_v2.models import EvidenceSpan
from apps.adviser_v2.readiness import load_captured_manifest

SOURCE_MODEL_SHA256 = "f84251230831afb359ab26d9fd37d5936d4d9bb5d1d5410e66442f630f24435b"
SOURCE_DATA_SHA256 = "1eebfb28493f67bba03ce0ef64bfdc7fc5a3bd9d7493f818bb1d78cd798416b4"
SOURCE_TOKENIZER_SHA256 = "6710678b12670bc442b99edc952c4d996ae309a7020c1fa0096dd245c2faf790"
HINDI_QUALIFICATION_PROBES = (
    "मैं 35 वर्ष का हूं और पहली स्वास्थ्य बीमा पॉलिसी खरीदना चाहता हूं।",
    "मधुमेह के लिए पहले से मौजूद बीमारी की प्रतीक्षा अवधि कितनी है?",
    "मैं अपनी 70 वर्षीय मां के लिए बिना सह-भुगतान वाला बीमा चाहता हूं।",
    "दो बच्चों वाले परिवार के लिए फैमिली फ्लोटर की पात्रता क्या है?",
    "कमरे के किराये की सीमा से दावे में कितनी कटौती हो सकती है?",
    "सह-भुगतान और डिडक्टिबल में क्या अंतर है?",
    "मातृत्व और नवजात शिशु का लाभ कब शुरू होता है?",
    "बीमा राशि खत्म होने पर रिस्टोरेशन लाभ कैसे लागू होता है?",
    "मेरे शहर में कैशलेस अस्पताल नेटवर्क उपलब्ध है या नहीं?",
    "पुरानी पॉलिसी की निरंतरता के साथ पोर्टेबिलिटी कैसे मिलेगी?",
)


def _queries(path: Path, count: int) -> list[str]:
    values = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(values) < count:
        raise CommandError(f"Query source has {len(values)} usable lines; {count} are required.")
    english_count = count - len(HINDI_QUALIFICATION_PROBES)
    selected = [values[index * len(values) // english_count] for index in range(english_count)]
    return selected + list(HINDI_QUALIFICATION_PROBES)


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _round_robin_spans(capture_ids: list[str], maximum: int) -> list[EvidenceSpan]:
    grouped: dict[str, list[EvidenceSpan]] = {}
    for span in EvidenceSpan.objects.filter(
        source_capture_id__in=capture_ids,
        verification__in=["text_verified", "visually_verified", "reviewed"],
    ).order_by("source_capture_id", "page__page_number", "created_at"):
        grouped.setdefault(str(span.source_capture_id), []).append(span)
    selected: list[EvidenceSpan] = []
    offset = 0
    while len(selected) < maximum:
        progressed = False
        for capture_id in capture_ids:
            values = grouped.get(capture_id, [])
            if offset < len(values):
                selected.append(values[offset])
                progressed = True
                if len(selected) == maximum:
                    break
        if not progressed:
            break
        offset += 1
    return selected


class Command(BaseCommand):
    help = "Create a frozen full-model BGE-M3 ranking reference from verified manifest spans."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("manifest", type=Path)
        parser.add_argument("--queries", type=Path, default=Path("research/seeds/scenarios.txt"))
        parser.add_argument("--output", type=Path, required=True)
        parser.add_argument("--model-root", type=Path)
        parser.add_argument("--case-count", type=int, default=50)
        parser.add_argument("--max-passages", type=int, default=256)

    def handle(self, *args: Any, **options: Any) -> None:
        manifest_path: Path = options["manifest"].resolve()
        query_path: Path = options["queries"].resolve()
        output_path: Path = options["output"].resolve()
        case_count = int(options["case_count"])
        max_passages = int(options["max_passages"])
        if case_count < 50:
            raise CommandError("BGE-M3 qualification requires at least 50 frozen cases.")
        if max_passages < 10:
            raise CommandError("BGE-M3 qualification requires at least 10 passages.")
        configured_root = options.get("model_root") or settings.COVERGUIDE_EMBEDDING_MODEL_PATH
        if not configured_root:
            raise CommandError("Pass --model-root or configure COVERGUIDE_EMBEDDING_MODEL_PATH.")
        model_root = Path(configured_root).resolve()
        model_path = model_root / "source/model.onnx"
        data_path = model_root / "source/model.onnx_data"
        tokenizer_path = model_root / "tokenizer.json"
        expected = (
            (model_path, SOURCE_MODEL_SHA256),
            (data_path, SOURCE_DATA_SHA256),
            (tokenizer_path, SOURCE_TOKENIZER_SHA256),
        )
        for path, digest in expected:
            if not path.is_file() or sha256_file(path) != digest:
                raise CommandError(f"Pinned full-model artifact is missing or mismatched: {path}")
        try:
            manifest = load_captured_manifest(manifest_path)
            queries = _queries(query_path, case_count)
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        capture_ids = list(
            dict.fromkeys(
                str(document["capture_id"])
                for product in manifest["products"]
                for document in product["documents"]
            )
        )
        spans = _round_robin_spans(capture_ids, max_passages)
        if len(spans) < 10:
            raise CommandError("The curated manifest has fewer than 10 verified passages.")
        passages = [{"id": str(span.id), "text": span.quote[:20_000]} for span in spans]
        try:
            passage_vectors = embed_texts_from_onnx(
                model_path, tokenizer_path, [item["text"] for item in passages]
            )
            query_vectors = embed_texts_from_onnx(model_path, tokenizer_path, queries)
        except (RuntimeError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        identifiers = [item["id"] for item in passages]
        cases = []
        for query, query_vector in zip(queries, query_vectors, strict=True):
            ranked = [
                identifier
                for _score, identifier in sorted(
                    (
                        (_dot(query_vector, vector), identifier)
                        for identifier, vector in zip(identifiers, passage_vectors, strict=True)
                    ),
                    key=lambda item: (-item[0], item[1]),
                )
            ]
            cases.append({"query": query, "full_model_ranking": ranked})
        payload = {
            "schema_version": 1,
            "model_name": BGE_MODEL_NAME,
            "passages": passages,
            "cases": cases,
        }
        encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        output_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = output_path.with_suffix(output_path.suffix + ".tmp")
        temporary.write_text(encoded, encoding="utf-8")
        temporary.replace(output_path)
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        self.stdout.write(
            self.style.SUCCESS(
                f"Wrote {len(cases)} full-model cases over {len(passages)} passages; "
                f"SHA-256 {digest}."
            )
        )
