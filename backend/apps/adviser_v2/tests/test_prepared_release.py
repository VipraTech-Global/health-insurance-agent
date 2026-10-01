import uuid

import pytest
from django.db import DatabaseError, connection, transaction
from django.utils import timezone

from apps.adviser_v2.models import (
    EvidenceSpan,
    KnowledgeRelease,
    KnowledgeReleaseFact,
    KnowledgeReleaseRule,
    PolicyRule,
    PolicyRuleEvidence,
    PolicyVersion,
    PolicyVersionDocument,
    ProcessingJob,
    Product,
)
from apps.adviser_v2.prepared_facts import FACT_RELEASE_VERSION, digest, facts_for_release
from apps.adviser_v2.processing.criterion_evidence import CRITERIA
from apps.adviser_v2.tests.test_pipeline import public_html_capture
from apps.adviser_v2.tests.test_releases import _rule_body


def prepared_fixture():
    capture = public_html_capture()
    span = EvidenceSpan.objects.create(
        source_capture=capture,
        quote="Test-only policy evidence.",
        section_label="test",
        method="html",
        verification="reviewed",
        context={"span_ids": [], "notes": []},
        locator={
            "schema_version": 1,
            "blob_sha256": capture.original_file.sha256,
            "resolver_version": "test/1",
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
    release = KnowledgeRelease.objects.create(
        release_number=1,
        state="ready",
        manifest_sha256="a" * 64,
        release_label="development_alpha_3_product",
        readiness={
            "demo_subset": True,
            "catalogue_product_count": 3,
            "comparison_product_count": 3,
            "fact_release_version": FACT_RELEASE_VERSION,
        },
        supported_scope={
            "intent_kinds": ["product_comparison"],
            "insurer_ids": [str(capture.discovery_run.insurer_id)],
            "rule_keys": [],
            "state": "conditional",
            "unresolved": [],
        },
    )
    for i in range(3):
        product = Product.objects.create(
            insurer=capture.discovery_run.insurer,
            name=f"Prepared plan {i}",
            benefit_type="medical_indemnity",
            lifecycle_status="open",
            comparison_role="primary_policy",
            identity_evidence=span,
        )
        version = PolicyVersion.objects.create(
            product=product,
            uin=f"FACT-{i}",
            version_label="test",
            applicability=applicability,
            publication_status="published",
        )
        PolicyVersionDocument.objects.create(
            policy_version=version,
            document_version=capture.document_version,
            role="base_wording",
            required_for_policy=True,
            applicability=applicability,
        )
        job = ProcessingJob.objects.create(
            source_capture=capture,
            stage="validate",
            adapter_version="test",
            input_commitment=uuid.uuid4().hex * 2,
            state="succeeded",
            result_storage_key="test.json",
            result_storage_sha256="b" * 64,
        )
        for criterion in CRITERIA:
            fact = {
                "criterion": criterion.key,
                "status": "supported",
                "value": "Test policy fact.",
                "citations": [{"evidence_span_id": str(span.id)}],
                "unknown_reasons": [],
                "rule_status": "rule not executable",
                "rule_ids": [],
            }
            KnowledgeReleaseFact.objects.create(
                knowledge_release=release,
                policy_version=version,
                validation_job=job,
                validation_sha256="b" * 64,
                criterion=criterion.key,
                fact=fact,
                fact_sha256=digest(fact),
            )
    return release, span


def publish(release):
    release.state = "published"
    release.published_at = timezone.now()
    release.save(update_fields=["state", "published_at"])
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")


@pytest.mark.django_db
def test_fact_release_needs_all_39_and_published_snapshot_is_immutable():
    release, _span = prepared_fixture()
    assert [len(v) for v in facts_for_release(release).values()] == [13] * 3
    member = KnowledgeReleaseFact.objects.filter(knowledge_release=release).first()
    with transaction.atomic():
        member.delete()
        with pytest.raises(DatabaseError, match="thirteen|count"), transaction.atomic():
            publish(release)
        transaction.set_rollback(True)
    publish(release)
    with pytest.raises(DatabaseError, match="immutable|published"), transaction.atomic():
        KnowledgeReleaseFact.objects.filter(knowledge_release=release).update(fact_sha256="c" * 64)
    with pytest.raises(DatabaseError, match="immutable"), transaction.atomic():
        release.readiness = {}
        release.save(update_fields=["readiness"])


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", ["hash", "unknown", "wrong_criterion", "pending_job"])
def test_database_fact_gate_rejects_invalid_validation_membership(mutation):
    release, _span = prepared_fixture()
    member = KnowledgeReleaseFact.objects.filter(knowledge_release=release).first()
    if mutation == "hash":
        member.validation_sha256 = "f" * 64
    elif mutation == "unknown":
        member.fact["status"] = "unknown"
    elif mutation == "wrong_criterion":
        member.fact["criterion"] = "other"
    else:
        ProcessingJob.objects.filter(pk=member.validation_job_id).update(state="blocked")
    member.save()
    with pytest.raises(DatabaseError, match="source validation"), transaction.atomic():
        publish(release)


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["verified", "unreviewed"])
def test_fact_release_cannot_execute_a_descriptive_fact(status):
    release, span = prepared_fixture()
    member = KnowledgeReleaseFact.objects.filter(knowledge_release=release).first()
    rule = PolicyRule.objects.create(
        policy_version=member.policy_version,
        rule_key="test",
        rule_type="eligibility",
        review_status=status,
        body=_rule_body(span.id),
    )
    PolicyRuleEvidence.objects.create(policy_rule=rule, evidence_span=span, role="supports")
    with (
        pytest.raises(
            DatabaseError, match="executable-rule scope|verified-rule|verified unsuperseded"
        ),
        transaction.atomic(),
    ):
        KnowledgeReleaseRule.objects.create(knowledge_release=release, policy_rule=rule)
        publish(release)
