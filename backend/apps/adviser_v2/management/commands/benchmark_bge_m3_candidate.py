"""Measure a candidate INT8 ONNX artifact without qualifying it for runtime use."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.adviser_v2.embedding import (
    BGE_MODEL_NAME,
    MIN_NDCG_AT_10,
    MIN_QUALIFICATION_CASES,
    MIN_TOP_10_OVERLAP,
    FullModelReferenceV1,
    RankingCaseResult,
    embed_texts_from_onnx,
    ndcg_at_10,
    sha256_file,
)


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


class Command(BaseCommand):
    help = "Benchmark a quantized BGE-M3 candidate against the frozen full-model rankings."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("reference", type=Path)
        parser.add_argument("candidate", type=Path)
        parser.add_argument("tokenizer", type=Path)
        parser.add_argument("--output", type=Path)

    def handle(self, *args: Any, **options: Any) -> None:
        reference_path: Path = options["reference"].resolve()
        candidate_path: Path = options["candidate"].resolve()
        tokenizer_path: Path = options["tokenizer"].resolve()
        try:
            payload = reference_path.read_bytes()
            reference = FullModelReferenceV1.model_validate_json(payload)
        except (OSError, ValueError) as exc:
            raise CommandError(f"Full-model reference is invalid: {exc}") from exc
        if reference.schema_version != 1 or reference.model_name != BGE_MODEL_NAME:
            raise CommandError("The reference must be a BAAI/bge-m3 schema-version 1 corpus.")
        if not candidate_path.is_file() or not tokenizer_path.is_file():
            raise CommandError("Candidate model and tokenizer files are required.")
        identifiers = [item.id for item in reference.passages]
        try:
            passage_vectors = embed_texts_from_onnx(
                candidate_path,
                tokenizer_path,
                [item.text for item in reference.passages],
            )
            query_vectors = embed_texts_from_onnx(
                candidate_path,
                tokenizer_path,
                [item.query for item in reference.cases],
            )
        except (RuntimeError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        results: list[RankingCaseResult] = []
        for case, query_vector in zip(reference.cases, query_vectors, strict=True):
            observed = [
                identifier
                for _score, identifier in sorted(
                    (
                        (_dot(query_vector, vector), identifier)
                        for identifier, vector in zip(identifiers, passage_vectors, strict=True)
                    ),
                    key=lambda item: (-item[0], item[1]),
                )
            ]
            expected = case.full_model_ranking
            results.append(
                RankingCaseResult(
                    query_sha256=hashlib.sha256(case.query.encode()).hexdigest(),
                    ndcg_at_10=ndcg_at_10(expected, observed),
                    top_10_overlap=len(set(expected[:10]) & set(observed[:10]))
                    / max(1, len(expected[:10])),
                )
            )
        mean_ndcg = sum(item.ndcg_at_10 for item in results) / len(results)
        mean_overlap = sum(item.top_10_overlap for item in results) / len(results)
        passed = (
            len(results) >= MIN_QUALIFICATION_CASES
            and min(item.ndcg_at_10 for item in results) >= MIN_NDCG_AT_10
            and min(item.top_10_overlap for item in results) >= MIN_TOP_10_OVERLAP
            and mean_ndcg >= MIN_NDCG_AT_10
            and mean_overlap >= MIN_TOP_10_OVERLAP
        )
        report = {
            "schema_version": 1,
            "candidate_sha256": sha256_file(candidate_path),
            "candidate_byte_count": candidate_path.stat().st_size,
            "reference_sha256": hashlib.sha256(payload).hexdigest(),
            "case_results": [item.model_dump(mode="json") for item in results],
            "mean_ndcg_at_10": mean_ndcg,
            "mean_top_10_overlap": mean_overlap,
            "minimum_ndcg_at_10": min(item.ndcg_at_10 for item in results),
            "minimum_top_10_overlap": min(item.top_10_overlap for item in results),
            "passed": passed,
        }
        encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
        output = options.get("output")
        if output is not None:
            output = output.resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(encoded, encoding="utf-8")
        self.stdout.write(encoded.rstrip())
        if not passed:
            raise CommandError("Candidate did not meet every fixed BGE-M3 ranking gate.")
