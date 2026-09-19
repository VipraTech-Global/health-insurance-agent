from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any, cast

import pytest
from django.contrib.postgres.search import SearchVector
from django.db.models import Value

from apps.adviser_v2.embedding import BGE_DIMENSIONS, BgeM3QualificationV1, policy_index_version
from apps.adviser_v2.models import (
    EvidenceSpan,
    KnowledgeRelease,
    KnowledgeReleaseRule,
    PolicyRule,
    PolicyRuleEvidence,
    PolicyRuleLink,
    PolicySearchChunk,
    PolicyVersion,
    PolicyVersionDocument,
    Product,
)
from apps.adviser_v2.retrieval import _reciprocal_rank_fusion, retrieve_policy_context
from apps.adviser_v2.tests.test_pipeline import public_html_capture


def _rule_body(span_id: uuid.UUID) -> dict[str, object]:
    return {
        "schema_version": 1,
        "applies_when": {"node": "constant", "value": "true"},
        "inputs": [],
        "effects": [
            {
                "kind": "eligibility",
                "target_key": "policy_eligibility",
                "scope": {
                    "subject": "policy",
                    "subject_ids": [],
                    "period": "policy_term",
                    "benefit_keys": [],
                    "reset": "never",
                },
                "decision": "eligible",
                "reason": "Test-only exact policy evidence.",
            }
        ],
        "mandatory_rule_keys": [],
        "source_span_ids": [str(span_id)],
        "unresolved": [],
        "rounding": {"mode": "none", "scale": 0, "authority_span_ids": []},
    }


def test_reciprocal_rank_fusion_rewards_agreement_and_is_stable() -> None:
    first_id = uuid.UUID(int=1)
    second_id = uuid.UUID(int=2)
    first = cast(Any, SimpleNamespace(id=first_id))
    second = cast(Any, SimpleNamespace(id=second_id))

    assert _reciprocal_rank_fusion([[first, second], [second, first]], 2) == [first, second]
    with pytest.raises(ValueError, match="limit must be positive"):
        _reciprocal_rank_fusion([[first]], 0)


@pytest.mark.django_db
def test_policy_retrieval_fuses_search_and_expands_reviewed_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture = public_html_capture()
    first_span = EvidenceSpan.objects.create(
        source_capture=capture,
        section_label="waiting period",
        quote="Diabetes pre-existing disease waiting period.",
        context={"span_ids": [], "notes": []},
        method="html",
        verification="reviewed",
        locator={
            "schema_version": 1,
            "blob_sha256": capture.original_file.sha256,
            "resolver_version": "test-html/1",
            "kind": "html_element",
            "encoding": "utf-8",
            "selector": "body",
            "selector_language": "css",
            "occurrence": 0,
            "text_interpretation": "decoded_text_content",
            "attribute_name": None,
        },
    )
    second_span = EvidenceSpan.objects.create(
        source_capture=capture,
        section_label="exception",
        quote="The linked exception changes that waiting-period rule.",
        context={"span_ids": [], "notes": []},
        method="html",
        verification="reviewed",
        locator=first_span.locator,
    )
    applicability = {
        "schema_version": 1,
        "predicate": {"node": "constant", "value": "true"},
        "event_basis": ["issue"],
        "source_span_ids": [str(first_span.id)],
        "unresolved": [],
    }
    product = Product.objects.create(
        insurer=capture.discovery_run.insurer,
        name="Retrieval test policy",
        benefit_type="medical_indemnity",
        lifecycle_status="open",
        recommendation_role="primary_policy",
        identity_evidence=first_span,
    )
    policy = PolicyVersion.objects.create(
        product=product,
        uin="RETRIEVAL-TEST-UIN",
        version_label="Current",
        applicability=applicability,
    )
    PolicyVersionDocument.objects.create(
        policy_version=policy,
        document_version=capture.document_version,
        role="base_wording",
        required_for_policy=True,
        applicability=applicability,
    )
    first_rule = PolicyRule.objects.create(
        policy_version=policy,
        rule_key="waiting-period",
        rule_type="eligibility",
        body=_rule_body(first_span.id),
        review_status="verified",
    )
    second_rule = PolicyRule.objects.create(
        policy_version=policy,
        rule_key="waiting-period-exception",
        rule_type="exception",
        body=_rule_body(second_span.id),
        review_status="verified",
    )
    PolicyRuleEvidence.objects.create(
        policy_rule=first_rule,
        evidence_span=first_span,
        role="supports",
    )
    PolicyRuleEvidence.objects.create(
        policy_rule=second_rule,
        evidence_span=second_span,
        role="excepts",
    )
    PolicyRuleLink.objects.create(
        from_policy_rule=first_rule,
        to_policy_rule=second_rule,
        link_type="exception",
    )
    release = KnowledgeRelease.objects.create(
        release_number=1,
        state="ready",
        supported_scope={
            "intent_kinds": ["purchase_recommendation"],
            "insurer_ids": [str(product.insurer_id)],
            "rule_keys": [first_rule.rule_key, second_rule.rule_key],
            "state": "supported",
            "unresolved": [],
        },
        manifest_sha256="a" * 64,
    )
    KnowledgeReleaseRule.objects.bulk_create(
        [
            KnowledgeReleaseRule(knowledge_release=release, policy_rule=first_rule),
            KnowledgeReleaseRule(knowledge_release=release, policy_rule=second_rule),
        ]
    )
    qualification = BgeM3QualificationV1.model_construct(
        onnx_sha256="b" * 64,
        external_weights_sha256="d" * 64,
        tokenizer_sha256="c" * 64,
        config_sha256="e" * 64,
    )
    index_version = policy_index_version(qualification)
    first_vector = [0.0] * BGE_DIMENSIONS
    first_vector[0] = 1.0
    second_vector = [0.0] * BGE_DIMENSIONS
    second_vector[1] = 1.0
    for span, text, vector, digest in (
        (first_span, first_span.quote, first_vector, "1" * 64),
        (second_span, second_span.quote, second_vector, "2" * 64),
    ):
        PolicySearchChunk.objects.create(
            document_version=capture.document_version,
            evidence_span_ids=[str(span.id)],
            text=text,
            lexical_vector=SearchVector(Value(text), config="english"),
            embedding=vector,
            index_version=index_version,
            chunk_sha256=digest,
        )
    monkeypatch.setattr(
        "apps.adviser_v2.retrieval.qualified_embedding_status",
        lambda: (True, "qualified", qualification),
    )
    monkeypatch.setattr(
        "apps.adviser_v2.retrieval.embed_texts",
        lambda _texts: [first_vector],
    )

    result = retrieve_policy_context("diabetes waiting period", release, limit=1)

    assert result.chunks[0].evidence_span_ids == [str(first_span.id)]
    assert result.rule_ids == tuple(sorted((first_rule.id, second_rule.id), key=str))
