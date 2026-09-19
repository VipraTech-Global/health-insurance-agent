from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from apps.adviser_v2.models import (
    EvidenceSpan,
    KnowledgeChannel,
    KnowledgeReleaseRule,
    PolicyRule,
    PolicyRuleEvidence,
    PolicyVersion,
    PolicyVersionDocument,
    Product,
)
from apps.adviser_v2.selectors.catalogue import catalogue_readiness
from apps.adviser_v2.services.releases import build_release, publish_release
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


@pytest.mark.django_db
def test_five_product_partial_release_is_published_as_development_alpha(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture = public_html_capture()
    span = EvidenceSpan.objects.create(
        source_capture=capture,
        section_label="eligibility",
        quote="This exact passage supports the test eligibility rule.",
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
    applicability = {
        "schema_version": 1,
        "predicate": {"node": "constant", "value": "true"},
        "event_basis": ["issue"],
        "source_span_ids": [str(span.id)],
        "unresolved": [],
    }
    policy_ids: list[str] = []
    rule_ids: list[str] = []
    for index in range(5):
        product = Product.objects.create(
            insurer=capture.discovery_run.insurer,
            name=f"Alpha product {index}",
            benefit_type="medical_indemnity",
            lifecycle_status="open",
            recommendation_role="primary_policy",
            identity_evidence=span,
        )
        policy = PolicyVersion.objects.create(
            product=product,
            uin=f"ALPHA-UIN-{index}",
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
        rule = PolicyRule.objects.create(
            policy_version=policy,
            rule_key=f"eligibility-{index}",
            rule_type="eligibility",
            body=_rule_body(span.id),
            review_status="verified",
        )
        PolicyRuleEvidence.objects.create(
            policy_rule=rule,
            evidence_span=span,
            role="supports",
        )
        policy_ids.append(str(policy.id))
        rule_ids.append(str(rule.id))

    manifest_sha256 = "f" * 64
    manifest = {
        "manifest_sha256": manifest_sha256,
        "products": [{"policy_version_id": item} for item in policy_ids],
    }
    report = {
        "ready": True,
        "blockers": [],
        "products": [
            {
                "policy_version_id": policy_id,
                "verified_rule_ids": [rule_id],
                "covered_inventory_categories": ["eligibility"],
                "missing_inventory_categories": ["waiting_periods"],
                "coverage": 0.1,
                "warnings": ["reconciliation_version_stale:test-wording"],
            }
            for policy_id, rule_id in zip(policy_ids, rule_ids, strict=True)
        ],
    }
    monkeypatch.setattr(
        "apps.adviser_v2.services.releases.load_captured_manifest", lambda _path: manifest
    )
    monkeypatch.setattr(
        "apps.adviser_v2.services.releases.validate_five_product_manifest",
        lambda _path: report,
    )
    monkeypatch.setattr(
        "apps.adviser_v2.services.releases.find_captured_manifest",
        lambda _sha256: Path("captured.json"),
    )

    release, build_report = build_release(Path("captured.json"))
    published = publish_release(release.id)

    assert build_report["ready"] is True
    assert published.state == "published"
    assert published.release_label == "development_alpha"
    assert published.supported_scope["state"] == "conditional"
    assert published.readiness["incomplete_comparison"] is True
    assert len(published.readiness["products"]) == 5
    assert published.readiness["products"][0]["warnings"] == [
        "reconciliation_version_stale:test-wording"
    ]
    assert KnowledgeReleaseRule.objects.filter(knowledge_release=published).count() == 5
    assert KnowledgeChannel.objects.get(name="live").current_release_id == published.id


@pytest.mark.django_db
def test_three_product_demo_release_publishes_only_ready_manifest_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture = public_html_capture()
    span = EvidenceSpan.objects.create(
        source_capture=capture,
        section_label="eligibility",
        quote="This exact passage supports the three-product demo rule.",
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
    applicability = {
        "schema_version": 1,
        "predicate": {"node": "constant", "value": "true"},
        "event_basis": ["issue"],
        "source_span_ids": [str(span.id)],
        "unresolved": [],
    }
    policies: list[PolicyVersion] = []
    rule_ids: list[str] = []
    for index in range(5):
        product = Product.objects.create(
            insurer=capture.discovery_run.insurer,
            name=f"Demo product {index}",
            benefit_type="medical_indemnity",
            lifecycle_status="open",
            recommendation_role="primary_policy",
            identity_evidence=span,
        )
        policy = PolicyVersion.objects.create(
            product=product,
            uin=f"DEMO-UIN-{index}",
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
        rule = PolicyRule.objects.create(
            policy_version=policy,
            rule_key=f"demo-eligibility-{index}",
            rule_type="eligibility",
            body=_rule_body(span.id),
            review_status="verified",
        )
        PolicyRuleEvidence.objects.create(
            policy_rule=rule,
            evidence_span=span,
            role="supports",
        )
        policies.append(policy)
        rule_ids.append(str(rule.id))

    manifest = {
        "manifest_sha256": "3" * 64,
        "products": [
            {"policy_version_id": str(policy.id)} for policy in policies
        ],
    }
    report_products = [
        {
            "policy_version_id": str(policy.id),
            "ready": index < 3,
            "blockers": [] if index < 3 else ["policy_index_stage_missing"],
            "verified_rule_ids": [rule_ids[index]] if index < 3 else [],
            "covered_inventory_categories": ["eligibility"] if index < 3 else [],
            "missing_inventory_categories": ["waiting_periods"],
            "coverage": 0.1 if index < 3 else 0.0,
            "warnings": [],
        }
        for index, policy in enumerate(policies)
    ]
    full_report = {
        "ready": False,
        "blockers": [
            "product-4:policy_index_stage_missing",
            "product-5:policy_index_stage_missing",
        ],
        "warnings": [],
        "products": report_products,
    }
    monkeypatch.setattr(
        "apps.adviser_v2.services.releases.load_captured_manifest", lambda _path: manifest
    )
    monkeypatch.setattr(
        "apps.adviser_v2.services.releases.validate_five_product_manifest",
        lambda _path: full_report,
    )
    monkeypatch.setattr(
        "apps.adviser_v2.services.releases.find_captured_manifest",
        lambda _sha256: Path("captured.json"),
    )

    release, build_report = build_release(
        Path("captured.json"), comparison_product_count=3
    )
    published = publish_release(release.id)

    assert build_report["ready"] is True
    assert published.state == "published"
    assert published.release_label == "development_alpha_3_product"
    assert published.readiness["demo_subset"] is True
    assert published.readiness["catalogue_product_count"] == 5
    assert published.readiness["comparison_product_count"] == 3
    assert len(published.readiness["products"]) == 3
    assert KnowledgeReleaseRule.objects.filter(knowledge_release=published).count() == 3
    assert PolicyVersion.objects.filter(
        id__in=[policy.id for policy in policies[:3]], publication_status="published"
    ).count() == 3
    assert PolicyVersion.objects.filter(
        id__in=[policy.id for policy in policies[3:]], publication_status="draft"
    ).count() == 2
    assert KnowledgeChannel.objects.get(name="live").current_release_id == published.id
    readiness = catalogue_readiness()
    assert readiness["ready"] is True
    assert readiness["catalogue_limit"] == 3
    assert "3 of 5 products available" in readiness["comparison_label"]
    assert sum(item["included_in_current_release"] for item in readiness["products"]) == 3
