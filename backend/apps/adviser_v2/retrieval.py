"""Hybrid-ready retrieval over public rules and encrypted conversation messages."""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass
from typing import cast

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import F, Q, Value
from pgvector.django import CosineDistance

from .crypto import commitment
from .embedding import embed_texts, policy_index_version, qualified_embedding_status
from .models import (
    ConversationMessageChunk,
    KnowledgeRelease,
    KnowledgeReleaseRule,
    Message,
    PolicyRuleEvidence,
    PolicyRuleLink,
    PolicySearchChunk,
    PolicyVersionDocument,
)

INDEX_VERSION = "coverguide-message-lexical/1"
RRF_CONSTANT = 60


@dataclass(frozen=True)
class PolicyRetrievalContext:
    chunks: tuple[PolicySearchChunk, ...]
    rule_ids: tuple[uuid.UUID, ...]


def _reciprocal_rank_fusion(
    rankings: list[list[PolicySearchChunk]], limit: int
) -> list[PolicySearchChunk]:
    if limit < 1:
        raise ValueError("Policy retrieval limit must be positive.")
    scores: defaultdict[uuid.UUID, float] = defaultdict(float)
    chunks: dict[uuid.UUID, PolicySearchChunk] = {}
    for ranking in rankings:
        for rank, chunk in enumerate(ranking, 1):
            chunks[chunk.id] = chunk
            scores[chunk.id] += 1 / (RRF_CONSTANT + rank)
    ordered_ids = sorted(scores, key=lambda item: (-scores[item], str(item)))[:limit]
    return [chunks[item] for item in ordered_ids]


def _linked_release_rule_ids(
    release_rule_ids: set[uuid.UUID], seed_rule_ids: set[uuid.UUID]
) -> tuple[uuid.UUID, ...]:
    expanded = seed_rule_ids & release_rule_ids
    frontier = set(expanded)
    while frontier:
        links = PolicyRuleLink.objects.filter(
            Q(from_policy_rule_id__in=frontier) | Q(to_policy_rule_id__in=frontier)
        ).values_list("from_policy_rule_id", "to_policy_rule_id")
        discovered = {
            rule_id for pair in links for rule_id in pair if rule_id in release_rule_ids
        } - expanded
        if not discovered:
            break
        expanded.update(discovered)
        frontier = discovered
    return tuple(sorted(expanded, key=str))


def index_message(message: Message) -> ConversationMessageChunk:
    text = message.content
    chunk, created = ConversationMessageChunk.objects.get_or_create(
        owner_id=message.owner_id,
        conversation_id=message.conversation_id,
        message=message,
        chunk_index=0,
        index_revision=INDEX_VERSION,
        defaults={
            "start_offset": 0,
            "end_offset": len(text),
            "lexical_vector": SearchVector(Value(text), config="english"),
            "content_commitment": commitment(text),
        },
    )
    if created:
        # Force expression evaluation before this object is ever serialized.
        chunk.refresh_from_db()
    if chunk.content_commitment != commitment(text):
        raise ValueError("An immutable message index commitment does not match its source.")
    return chunk


def conversation_context(
    owner_id: uuid.UUID,
    conversation_id: uuid.UUID,
    query_text: str,
    *,
    recent_count: int = 12,
    historical_count: int = 6,
) -> list[Message]:
    recent = list(
        Message.objects.filter(owner_id=owner_id, conversation_id=conversation_id).order_by(
            "-sequence"
        )[:recent_count]
    )
    recent_ids = {item.id for item in recent}
    query = SearchQuery(query_text, search_type="websearch", config="english")
    historical_ids = list(
        ConversationMessageChunk.objects.filter(
            owner_id=owner_id,
            conversation_id=conversation_id,
            invalidated_at__isnull=True,
        )
        .exclude(message_id__in=recent_ids)
        .annotate(rank=SearchRank(F("lexical_vector"), query))
        .filter(rank__gt=0)
        .order_by("-rank")
        .values_list("message_id", flat=True)[:historical_count]
    )
    older = list(Message.objects.filter(owner_id=owner_id, id__in=historical_ids))
    combined = {item.id: item for item in [*recent, *older]}
    return sorted(combined.values(), key=lambda item: item.sequence)


def policy_chunks(
    query_text: str, document_version_ids: list[uuid.UUID], limit: int = 24
) -> list[PolicySearchChunk]:
    query = SearchQuery(query_text, search_type="websearch", config="english")
    return list(
        PolicySearchChunk.objects.filter(document_version_id__in=document_version_ids)
        .annotate(rank=SearchRank(F("lexical_vector"), query))
        .filter(rank__gt=0)
        .order_by("-rank")[:limit]
    )


def retrieve_policy_context(
    query_text: str,
    release: KnowledgeRelease,
    *,
    limit: int = 24,
) -> PolicyRetrievalContext:
    """Fuse lexical and dense rankings, then expand their reviewed rule graph."""

    if not query_text.strip():
        raise ValueError("Policy retrieval requires non-empty customer context.")
    if limit < 1:
        raise ValueError("Policy retrieval limit must be positive.")
    release_rule_ids = set(
        KnowledgeReleaseRule.objects.filter(knowledge_release=release).values_list(
            "policy_rule_id", flat=True
        )
    )
    if not release_rule_ids:
        raise ValueError("The pinned knowledge release has no policy rules.")
    policy_version_ids = set(
        KnowledgeReleaseRule.objects.filter(knowledge_release=release).values_list(
            "policy_rule__policy_version_id", flat=True
        )
    )
    document_version_ids = list(
        PolicyVersionDocument.objects.filter(policy_version_id__in=policy_version_ids).values_list(
            "document_version_id", flat=True
        )
    )
    if not document_version_ids:
        raise ValueError("The pinned knowledge release has no policy documents.")
    embedding_ready, reason, qualification = qualified_embedding_status()
    if not embedding_ready or qualification is None:
        raise RuntimeError(reason)
    pool_size = limit * 4
    base = PolicySearchChunk.objects.filter(
        document_version_id__in=document_version_ids,
        index_version=policy_index_version(qualification),
    )
    query = SearchQuery(query_text, search_type="websearch", config="english")
    lexical = cast(
        list[PolicySearchChunk],
        list(
            base.annotate(retrieval_rank=SearchRank(F("lexical_vector"), query))
            .filter(retrieval_rank__gt=0)
            .order_by("-retrieval_rank", "id")[:pool_size]
        ),
    )
    query_vector = embed_texts([query_text])[0]
    semantic = cast(
        list[PolicySearchChunk],
        list(
            base.filter(embedding__isnull=False)
            .annotate(retrieval_distance=CosineDistance("embedding", query_vector))
            .order_by("retrieval_distance", "id")[:pool_size]
        ),
    )
    chunks = _reciprocal_rank_fusion([lexical, semantic], limit)
    if not chunks:
        raise ValueError("The pinned knowledge release returned no policy evidence chunks.")
    evidence_span_ids = {
        uuid.UUID(str(span_id)) for chunk in chunks for span_id in chunk.evidence_span_ids
    }
    seed_rule_ids = set(
        PolicyRuleEvidence.objects.filter(
            policy_rule_id__in=release_rule_ids,
            evidence_span_id__in=evidence_span_ids,
        ).values_list("policy_rule_id", flat=True)
    )
    return PolicyRetrievalContext(
        chunks=tuple(chunks),
        rule_ids=_linked_release_rule_ids(release_rule_ids, seed_rule_ids),
    )
