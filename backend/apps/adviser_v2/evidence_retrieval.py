"""Plan-scoped original-text Okapi retrieval; independent of dense qualification."""

from __future__ import annotations

import hashlib
import math
import re
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Any

import tiktoken
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import F, Value

from .models import PolicySearchChunk, PolicyVersion
from .processing.manifest_v2 import raw_bundle_passages

RAW_INDEX_VERSION = "poppler-raw-o200k-1024-overlap128/1"


@lru_cache(maxsize=1)
def tokenizer() -> Any:
    return tiktoken.get_encoding("o200k_base")


def token_count(text: str) -> int:
    return len(tokenizer().encode(text, disallowed_special=()))


@dataclass(frozen=True)
class RawChunk:
    id: str
    policy_version_id: str
    document_version_id: str
    text: str
    tokens: int
    segments: tuple[dict[str, Any], ...]

    @property
    def evidence_span_ids(self) -> list[str]:
        return [s["page_span_id"] for s in self.segments]


@dataclass(frozen=True)
class EvidencePacket:
    policy_version_id: str
    chunks: tuple[RawChunk, ...]
    tokens: int
    budget: int
    omitted_chunks: int
    method: str
    unavailable_reason: str | None = None

    def payload(self) -> dict[str, Any]:
        return asdict(self)


def raw_chunks(policy_id: str, pages: list[dict[str, Any]]) -> list[RawChunk]:
    documents: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in pages:
        documents[page["document_version_id"]].append(page)
    chunks = []
    for document_id, document_pages in sorted(documents.items()):
        document_pages.sort(key=lambda p: p["physical_page"])
        text = "\f".join(p["passage"] for p in document_pages)
        tokens = tokenizer().encode(text, disallowed_special=())
        decoded, offsets = tokenizer().decode_with_offsets(tokens)
        if decoded != text:
            raise ValueError("Tokenization changed the raw source text.")
        offsets.append(len(text))
        for first in range(0, len(tokens), 896):
            last = min(first + 1024, len(tokens))
            start, end = offsets[first], offsets[last]
            original = text[start:end]
            segments = []
            for page in document_pages:
                left = max(start, page["document_char_start"])
                right = min(end, page["document_char_start"] + len(page["passage"]))
                if left < right:
                    a, b = left - page["document_char_start"], right - page["document_char_start"]
                    segments.append(
                        {
                            "page_span_id": page["evidence_span_id"],
                            "document_key": page["document_key"],
                            "page": page["physical_page"],
                            "start": a,
                            "end": b,
                            "document_start": left,
                            "document_end": right,
                            "text": page["passage"][a:b],
                        }
                    )
            key = f"{RAW_INDEX_VERSION}:{document_id}:{start}:{end}:{hashlib.sha256(original.encode()).hexdigest()}"
            chunks.append(
                RawChunk(
                    str(uuid.uuid5(uuid.NAMESPACE_URL, key)),
                    policy_id,
                    document_id,
                    original,
                    token_count(original),
                    tuple(segments),
                )
            )
            if last == len(tokens):
                break
    return chunks


def plan_chunks(policy_id: str) -> list[RawChunk]:
    version = PolicyVersion.objects.get(pk=policy_id)
    return raw_chunks(policy_id, raw_bundle_passages(version, include_prospectus=True))


def index_raw_chunks(chunks: list[RawChunk]) -> None:
    for chunk in chunks:
        digest = hashlib.sha256((chunk.id + chunk.text).encode()).hexdigest()
        stored, _created = PolicySearchChunk.objects.get_or_create(
            id=chunk.id,
            defaults={
                "document_version_id": chunk.document_version_id,
                "index_version": RAW_INDEX_VERSION,
                "text": chunk.text,
                "evidence_span_ids": chunk.evidence_span_ids,
                "lexical_vector": SearchVector(Value(chunk.text), config="english"),
                "chunk_sha256": digest,
            },
        )
        if (
            stored.text != chunk.text
            or stored.chunk_sha256 != digest
            or stored.evidence_span_ids != chunk.evidence_span_ids
        ):
            raise ValueError("Stored raw chunk differs from its original source.")


def lexical_terms(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold())


class BM25:
    """Okapi BM25, k1=1.5, b=.75, positive Robertson IDF."""

    def __init__(self, chunks: list[RawChunk]):
        self.chunks = chunks
        self.frequencies = [Counter(lexical_terms(c.text)) for c in chunks]
        self.lengths = [sum(f.values()) for f in self.frequencies]
        self.average = sum(self.lengths) / len(chunks) if chunks else 1
        self.df = Counter(term for counts in self.frequencies for term in counts)

    def rank(self, query: str) -> list[RawChunk]:
        if not query.strip():
            raise ValueError("Retrieval needs the customer's question text.")
        scores = []
        for i, counts in enumerate(self.frequencies):
            score = 0.0
            for term in set(lexical_terms(query)):
                frequency = counts[term]
                if frequency:
                    idf = math.log(
                        1 + (len(self.chunks) - self.df[term] + 0.5) / (self.df[term] + 0.5)
                    )
                    score += (
                        idf
                        * frequency
                        * 2.5
                        / (frequency + 1.5 * (0.25 + 0.75 * self.lengths[i] / self.average))
                    )
            scores.append((score, self.chunks[i]))
        return [c for _score, c in sorted(scores, key=lambda pair: (-pair[0], pair[1].id))]


def fts_rank(query: str, chunks: list[RawChunk]) -> list[RawChunk]:
    by_id = {c.id: c for c in chunks}
    ranked = (
        PolicySearchChunk.objects.filter(id__in=by_id)
        .annotate(
            rank=SearchRank(
                F("lexical_vector"), SearchQuery(query, search_type="websearch", config="english")
            ),
        )
        .filter(rank__gt=0)
        .order_by("-rank", "id")
    )
    # Mirrors the current positive-rank FTS candidate path; no invented BM25 tail.
    return [by_id[str(row.id)] for row in ranked]


def pack(policy_id: str, ranked: list[RawChunk], *, budget: int, method: str) -> EvidencePacket:
    if budget < 1:
        raise ValueError("Evidence budget must be positive.")
    selected, used, seen = [], 0, set()
    for chunk in ranked:
        if chunk.policy_version_id != policy_id:
            raise ValueError("Wrong-plan evidence cannot enter a packet.")
        if chunk.id in seen:
            continue
        seen.add(chunk.id)
        if used + chunk.tokens <= budget:
            selected.append(chunk)
            used += chunk.tokens
    return EvidencePacket(
        policy_id, tuple(selected), used, budget, len(seen) - len(selected), method
    )


def retrieve_plan(query: str, policy_id: str, *, budget: int = 16000, turn=None) -> EvidencePacket:
    from django.conf import settings

    from apps.adviser.ai import RelayFailure

    method = settings.COVERGUIDE_EVIDENCE_RETRIEVAL
    if method == "pageindex":
        from .pageindex_evidence import rank_pages
        try:
            version = PolicyVersion.objects.get(pk=policy_id)
            pages = raw_bundle_passages(version, include_prospectus=True)
            return pack(policy_id, rank_pages(query, policy_id, pages, turn=turn), budget=budget, method=method)
        except (ValueError, OSError, RelayFailure) as exc:
            return EvidencePacket(policy_id, (), 0, budget, 0, method,
                "Original source evidence could not be retrieved: " + str(exc))
    if method != "bm25":
        raise ValueError(f"Unsupported policy-evidence retrieval setting: {method}")
    return pack(policy_id, BM25(plan_chunks(policy_id)).rank(query), budget=budget, method=method)
