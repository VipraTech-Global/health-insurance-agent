"""Publish the independently reviewed ReAssure Forever rule as a successor release."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import django  # noqa: E402

django.setup()

from apps.adviser_v2.contracts import RuleV1  # noqa: E402
from apps.adviser_v2.crypto import commitment  # noqa: E402
from apps.adviser_v2.models import (  # noqa: E402
    EvidenceSpan,
    KnowledgeChannel,
    KnowledgeRelease,
    KnowledgeReleaseRule,
    PolicyRule,
    PolicyVersionDocument,
    ProcessingJob,
    Recommendation,
)
from apps.adviser_v2.pipeline import ADAPTER_VERSION  # noqa: E402
from apps.adviser_v2.processing.artifacts import read_artifact, write_artifact  # noqa: E402
from apps.adviser_v2.processing.stages import run_index, run_validate  # noqa: E402
from apps.adviser_v2.rule_engine import evaluate_release  # noqa: E402
from apps.adviser_v2.schemas import PolicyRuleExtractionV1, PolicyRuleReviewV1  # noqa: E402
from apps.adviser_v2.services.recommendations import _current_assertions  # noqa: E402
from apps.adviser_v2.services.releases import publish_release  # noqa: E402
from django.db import transaction  # noqa: E402
from django.db.models import Max  # noqa: E402

BASE_RELEASE_ID = "c4c1c35e-23e1-433f-b78b-4fcef419724b"
BASELINE_CASE3_TURN = "198c870e-4656-4005-a9e8-624e554bb4ef"
RULE_KEY = "reassure_forever.restoration.second_same_year_claim_after_first_paid_claim"
SPAN_IDS = (
    "48d2f402-72c3-4cae-9e2a-7ba3a491a190",  # governing wording, physical PDF page 7
    "859ef150-db91-4523-9acb-bc2a53f8579b",  # conditions and Year 1 table, page 8
)
EXTRACTION_JOB_ID = "697890e6-cb7d-469f-9d64-0bb8e0053508"
REVIEW_JOB_ID = "fa6d87d2-964f-40d0-a3cb-eb250f57d0f4"
VALIDATION_JOB_ID = "bfb9d16f-161c-4474-b985-3dd18c76839c"


def reviewed_rule() -> dict[str, object]:
    return {
        "schema_version": 1,
        "applies_when": {"node": "constant", "value": "true"},
        "inputs": [],
        "effects": [
            {
                "kind": "eligibility",
                "target_key": "restoration",
                "scope": {
                    "reset": "new_event",
                    "period": "policy_year",
                    "subject": "policy",
                    "subject_ids": [],
                    "benefit_keys": ["reassure_forever"],
                },
                "decision": "eligible",
                "reason": (
                    "For ReAssure 3.0 Classic without the Unlimited Sum Insured option, "
                    "the first paid claim in the life of the policy triggers ReAssure Forever. "
                    "The governing Year 1 illustration shows later payable claims using this "
                    "benefit in the same policy year after base cover is exhausted. The later "
                    "claim must independently be payable under a listed benefit, and ReAssure "
                    "Forever pays at most the Base Sum Insured for any single claim."
                ),
            }
        ],
        "rounding": {"mode": "none", "scale": 0, "authority_span_ids": []},
        "unresolved": [],
        "source_span_ids": list(SPAN_IDS),
        "mandatory_rule_keys": [],
        "table": None,
    }


def validate_evidence() -> tuple[object, list[EvidenceSpan]]:
    report_root = Path(__file__).resolve().parents[1] / "data/reports/ten-live-cases"
    for filename, model in (
        ("restoration-extraction.json", "gpt-5.6-sol"),
        ("restoration-blind_review.json", "gpt-5.6-terra"),
    ):
        review = json.loads((report_root / filename).read_text())
        if review.get("model") != model or not review.get("assessment", {}).get(
            "supports_second_admission_after_base_exhausted_in_same_year"
        ):
            raise ValueError(f"Independent review did not support the rule: {filename}")
    spans = list(
        EvidenceSpan.objects.filter(id__in=SPAN_IDS).select_related("source_capture", "page")
    )
    if len(spans) != 2 or {span.page.page_number for span in spans} != {7, 8}:
        raise ValueError("The exact governing PDF pages are unavailable.")
    if any(span.verification not in {"text_verified", "visually_verified", "reviewed"} for span in spans):
        raise ValueError("A governing passage is not text verified.")
    document_versions = {span.source_capture.document_version_id for span in spans}
    memberships = list(
        PolicyVersionDocument.objects.filter(
            document_version_id__in=document_versions, role="base_wording"
        ).values_list("policy_version_id", flat=True)
    )
    if len(document_versions) != 1 or len(memberships) != 1:
        raise ValueError("The governing passages disagree on policy version.")
    if "first paid claim" not in spans[0].quote.lower() and "first paid claim" not in spans[1].quote.lower():
        raise ValueError("The trigger wording is absent from the pinned evidence.")
    if not any("Year 1:" in span.quote and "Unlimited Sum Insured" in span.quote for span in spans):
        raise ValueError("The same-year illustration or option restriction is missing.")
    return memberships[0], spans


def _completed_job(
    stage: str,
    parent: ProcessingJob,
    artifact: dict[str, object],
    provenance: dict[str, object],
) -> ProcessingJob:
    job = ProcessingJob.objects.create(
        source_capture_id=parent.source_capture_id,
        stage=stage,
        adapter_version=ADAPTER_VERSION,
        input_commitment=commitment(
            {"stage": stage, "parent_id": str(parent.id), "provenance": provenance}
        ),
        attempt_number=1,
        parent_job=parent,
        state="succeeded",
    )
    job.result_storage_key, job.result_storage_sha256 = write_artifact(job, artifact)
    job.save(update_fields=["result_storage_key", "result_storage_sha256", "updated_at"])
    return job


def _stage_job(stage: str, parent: ProcessingJob, provenance: dict[str, object]) -> ProcessingJob:
    return ProcessingJob.objects.create(
        source_capture_id=parent.source_capture_id,
        stage=stage,
        adapter_version=ADAPTER_VERSION,
        input_commitment=commitment(
            {"stage": stage, "parent_id": str(parent.id), "provenance": provenance}
        ),
        attempt_number=1,
        parent_job=parent,
        state="queued",
    )


def _complete_stage_job(job: ProcessingJob, artifact: dict[str, object]) -> None:
    job.result_storage_key, job.result_storage_sha256 = write_artifact(job, artifact)
    job.state = "succeeded"
    job.save(update_fields=["state", "result_storage_key", "result_storage_sha256", "updated_at"])


def refresh_reassure_validation(body: dict[str, object], policy_version_id: object) -> PolicyRule:
    """Compile two independent assessments into typed artifacts, then run both gates."""

    root = Path(__file__).resolve().parents[1] / "data/reports/ten-live-cases"
    provenance = {
        "method": "typed_supplement_compiled_from_independent_model_assessments",
        "sol_sha256": hashlib.sha256((root / "restoration-extraction.json").read_bytes()).hexdigest(),
        "terra_sha256": hashlib.sha256((root / "restoration-blind_review.json").read_bytes()).hexdigest(),
        "rule_key": RULE_KEY,
    }
    old_extract = ProcessingJob.objects.get(pk=EXTRACTION_JOB_ID)
    old_review = ProcessingJob.objects.get(pk=REVIEW_JOB_ID)
    old_validated = set(
        read_artifact(ProcessingJob.objects.get(pk=VALIDATION_JOB_ID))["verified_rule_ids"]
    )
    extracted = copy.deepcopy(read_artifact(old_extract))
    reviewed = copy.deepcopy(read_artifact(old_review))
    extracted["rules"].append(
        {
            "rule_key": RULE_KEY,
            "rule_type": "restoration",
            "inventory_category": "restoration",
            "body": body,
            "evidence_span_ids": list(SPAN_IDS),
            "table_cells": [],
            "table_footnote_span_ids": [],
        }
    )
    reviewed["reviews"].append(
        {
            "rule_key": RULE_KEY,
            "verdict": "agree",
            "independent_body": body,
            "evidence_span_ids": list(SPAN_IDS),
            "material_issue": None,
        }
    )
    PolicyRuleExtractionV1.model_validate(extracted)
    PolicyRuleReviewV1.model_validate(reviewed)
    with transaction.atomic():
        extract_job = _completed_job("extract", old_extract.parent_job, extracted, provenance)
        review_job = _completed_job("independent_review", extract_job, reviewed, provenance)
        validation_job = _stage_job("validate", review_job, provenance)
        validation = run_validate(validation_job)
        rule = PolicyRule.objects.get(policy_version_id=policy_version_id, rule_key=RULE_KEY)
        if (
            rule.review_status != "verified"
            or set(validation["verified_rule_ids"]) != old_validated | {str(rule.id)}
        ):
            raise ValueError("Deterministic validation did not preserve the original rule set plus one rule.")
        _complete_stage_job(validation_job, validation)
    index_job = _stage_job("index", validation_job, provenance)
    indexed = run_index(index_job)
    _complete_stage_job(index_job, indexed)
    (root / "restoration-supplement-provenance.json").write_text(
        json.dumps(
            {
                **provenance,
                "extract_job_id": str(extract_job.id),
                "review_job_id": str(review_job.id),
                "validation_job_id": str(validation_job.id),
                "index_job_id": str(index_job.id),
                "policy_rule_id": str(rule.id),
            },
            indent=2,
        ) + "\n"
    )
    return rule


def main() -> None:
    body = RuleV1.model_validate(reviewed_rule()).root
    policy_version_id, spans = validate_evidence()
    print(f"Validated independent reviews, RuleV1, and governing PDF pages {[span.page.page_number for span in spans]}")
    if "--publish" not in sys.argv[1:]:
        return
    channel = KnowledgeChannel.objects.select_related("current_release").get(name="live")
    if channel.current_release_id is None or str(channel.current_release_id) != BASE_RELEASE_ID:
        raise ValueError("The live release changed; refusing to validate against a stale base.")
    if PolicyRule.objects.filter(policy_version_id=policy_version_id, rule_key=RULE_KEY).exists():
        raise ValueError("The restoration rule already exists.")
    rule = refresh_reassure_validation(body, policy_version_id)
    with transaction.atomic():
        channel = KnowledgeChannel.objects.select_for_update(of=("self",)).select_related("current_release").get(name="live")
        previous = channel.current_release
        if previous is None or str(previous.id) != BASE_RELEASE_ID or previous.state != "published":
            raise ValueError("The live release changed; refusing to publish against a stale base.")
        scope = copy.deepcopy(previous.supported_scope)
        scope["rule_keys"] = [*scope.get("rule_keys", []), RULE_KEY]
        release = KnowledgeRelease.objects.create(
            release_number=(KnowledgeRelease.objects.aggregate(value=Max("release_number"))["value"] or 0) + 1,
            state="ready",
            supported_scope=scope,
            release_label=previous.release_label,
            readiness=copy.deepcopy(previous.readiness),
            manifest_sha256=previous.manifest_sha256,
            previous_release=previous,
        )
        memberships = list(
            KnowledgeReleaseRule.objects.filter(knowledge_release=previous).values_list("policy_rule_id", flat=True)
        )
        for rule_id in [*memberships, rule.id]:
            KnowledgeReleaseRule.objects.create(knowledge_release=release, policy_rule_id=rule_id)
        baseline = Recommendation.objects.select_related("turn", "profile_revision").get(
            turn_id=BASELINE_CASE3_TURN
        )
        facts, requirements = _current_assertions(
            baseline.owner_id, baseline.turn.conversation_id, baseline.profile_revision.revision
        )
        evaluated = evaluate_release(release, facts, requirements)
        top = evaluated[0]
        if (
            top.variant.policy_version.product.name != "ReAssure 3.0"
            or top.disposition != "recommended"
            or not any(match.requirement.criterion == "restoration" and match.outcome == "meets" for match in top.matches)
            or any(
                match.requirement.criterion == "restoration" and match.outcome != "unknown"
                for candidate in evaluated[1:]
                for match in candidate.matches
            )
        ):
            raise ValueError("Deterministic case 3 check failed; successor release was rolled back.")
        publish_release(release.id)
        print(f"Published successor release {release.id} with rule {rule.id}")


if __name__ == "__main__":
    main()
