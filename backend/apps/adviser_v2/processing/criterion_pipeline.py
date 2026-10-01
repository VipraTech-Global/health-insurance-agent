"""Version-2 orchestration inside the existing extraction/review contracts."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

from apps.adviser.ai import RelayFailure

from ..contracts import validate_contract
from ..models import ModelAttempt, PolicyRule, PolicyRuleEvidence, PolicyRuleLink, ProcessingJob
from ..rule_validation import rule_link_references, rule_semantic_problems
from ..schemas import PolicyRuleExtractionV1, PolicyRuleReviewV1, ReviewedPolicyRule
from .artifacts import read_artifact
from .criterion_attempts import TRANSPORT_FAILURES, extract_criterion, new_criterion_state
from .criterion_corrections import request_review_correction
from .criterion_evidence import (
    CRITERIA,
    PROCESSING_VERSION,
    PROGRESS_KEY,
    RETRY_PROTOCOL,
    Criterion,
    criterion_for_key,
    criterion_rule_problems,
    extraction_payload,
    has_copay_value,
    no_copay_body,
)
from .manifest_v2 import raw_bundle_passages

# These failures produce an explicit criterion unknown after its bounded attempt(s).
# Route/identity/qualification/quota failures still stop the pipeline itself.
CRITERION_FAILURES = {
    "provider_timeout",
    "provider_transport",
    "provider_unavailable",
    "invalid_structured_output",
    "incomplete_response",
    "malformed_response",
    "context_limit",
}


def _encoded(passages: list[dict[str, Any]]) -> str:
    return json.dumps(passages, ensure_ascii=False, separators=(",", ":"))


def _progress(job: ProcessingJob, policy_id: str, core: list[dict[str, Any]]) -> dict[str, Any]:
    digest = hashlib.sha256(_encoded(core).encode()).hexdigest()
    prior = (
        ProcessingJob.objects.filter(
            source_capture=job.source_capture,
            stage__in=("extract", "independent_review"),
            state__in=("cancelled", "failed", "blocked", "succeeded"),
            result_storage_key__isnull=False,
        )
        .exclude(pk=job.pk)
        .order_by("-created_at")
    )
    for previous in prior:
        progress = read_artifact(previous).get(PROGRESS_KEY)
        if progress is None:
            continue
        if (
            progress.get("protocol") != RETRY_PROTOCOL
            or progress.get("policy_version_id") != policy_id
            or progress.get("core_evidence_sha256") != digest
        ):
            raise ValueError(
                "Retained extraction progress differs from the approved source or retry protocol."
            )
        return progress
    return {
        "protocol": RETRY_PROTOCOL,
        "policy_version_id": policy_id,
        "core_evidence_sha256": digest,
        "criteria": {},
    }


def run_criterion_extraction(job: ProcessingJob) -> dict[str, Any]:
    from . import stages

    version = stages._policy_version(job)
    core = raw_bundle_passages(version)
    complete: list[dict[str, Any]] | None = None
    progress = _progress(job, str(version.id), core)
    deadline = time.monotonic() + stages.RULE_STAGE_TIMEOUT_SECONDS
    results = []

    def checkpoint() -> None:
        from ..pipeline import _finish_job

        _finish_job(
            job,
            job.lease_token,
            state="running",
            result={PROGRESS_KEY: progress},
            issues=job.issues,
            expected_erasure_generation=None,
        )

    def supplement() -> list[dict[str, Any]]:
        nonlocal complete
        if complete is None:
            complete = raw_bundle_passages(version, include_prospectus=True)
        return complete

    for criterion in CRITERIA:
        state = progress["criteria"].setdefault(criterion.key, new_criterion_state())

        def invoke(
            supplied: list[dict[str, Any]],
            feedback: str,
            criterion: Criterion = criterion,
            state: dict[str, Any] = state,
        ) -> PolicyRuleExtractionV1:
            before = set(
                ModelAttempt.objects.filter(processing_job=job).values_list("id", flat=True)
            )
            logging.getLogger(__name__).info(
                "Version-2 evidence %s: %s documents, %s pages, prospectus=%s, roles=%s",
                criterion.key,
                len({p["document_key"] for p in supplied}),
                len(supplied),
                state["prospectus_used"],
                sorted({p["document_role"] for p in supplied}),
            )
            try:
                return stages._run_extraction_batch(
                    job=job,
                    policy_version=version,
                    encoded_passages=_encoded(supplied),
                    categories=(criterion.category,),
                    evidence_batch_label="1/1",
                    deadline=deadline,
                    criterion=criterion,
                    max_attempts=1,
                    correction_context=feedback,
                )
            finally:
                state["attempt_ids"].extend(
                    str(pk)
                    for pk in ModelAttempt.objects.filter(processing_job=job)
                    .exclude(id__in=before)
                    .order_by("started_at")
                    .values_list("id", flat=True)
                )

        result = extract_criterion(
            policy_id=str(version.id),
            criterion=criterion,
            core=core,
            supplement=supplement,
            state=state,
            invoke=invoke,
            checkpoint=checkpoint,
        )
        supplied = supplement() if state["result_prospectus_used"] else core
        rules = []
        reasons = list(result.material_issues)
        seen = set()
        for rule in result.rules:
            problems = criterion_rule_problems(rule, criterion, supplied)
            problems.extend(stages._rule_table_targets(rule))
            if rule.rule_key in seen:
                problems.append("Duplicate rule key.")
            seen.add(rule.rule_key)
            if problems:
                reasons.append(
                    f"{criterion.category}: {criterion.key}: {rule.rule_key}: "
                    + "; ".join(problems)
                )
            else:
                rules.append(rule)
        if not rules and not reasons:
            reasons.append(
                f"{criterion.category}: {criterion.key}: No supported rule or source-specific explanation survived the bounded extraction."
            )
        result = PolicyRuleExtractionV1(
            schema_version=1,
            policy_version_id=str(version.id),
            rules=rules,
            omitted_inventory_categories=[criterion.category] if not rules else [],
            material_issues=[
                reason
                if criterion.key + ":" in reason
                else f"{criterion.category}: {criterion.key}: {reason}"
                for reason in reasons
            ],
        )
        results.append(((criterion.category,), result))
    return {
        **stages._combine_extraction_batches(str(version.id), results).model_dump(mode="json"),
        PROGRESS_KEY: progress,
    }


def run_criterion_review(job: ProcessingJob) -> dict[str, Any]:
    from . import stages

    version = stages._policy_version(job)
    extraction_artifact = read_artifact(stages._ancestor(job, "extract"))
    extraction = PolicyRuleExtractionV1.model_validate(extraction_payload(extraction_artifact))
    progress = extraction_artifact[PROGRESS_KEY]
    core = raw_bundle_passages(version)
    core_ids = {item["evidence_span_id"] for item in core}
    complete: list[dict[str, Any]] | None = None
    deadline = time.monotonic() + stages.RULE_STAGE_TIMEOUT_SECONDS
    results = []
    for criterion in CRITERIA:
        candidates = tuple(
            rule for rule in extraction.rules if criterion_for_key(rule.rule_key) == criterion
        )
        ids = {
            pk
            for rule in candidates
            for pk in [*rule.evidence_span_ids, *rule.body.get("source_span_ids", [])]
        }
        supplied = core
        if progress["criteria"][criterion.key]["prospectus_used"] or not ids.issubset(core_ids):
            if complete is None:
                complete = raw_bundle_passages(version, include_prospectus=True)
            supplied = complete
        try:
            for transport_attempt in range(3):
                try:
                    result = stages._run_review_batch(
                        job=job,
                        policy_version=version,
                        encoded_passages=_encoded(supplied),
                        categories=(criterion.category,),
                        candidates=candidates,
                        evidence_batch_label="1/1",
                        deadline=deadline,
                        criterion=criterion,
                        max_attempts=1,
                    )
                    break
                except RelayFailure as exc:
                    if exc.code not in TRANSPORT_FAILURES or transport_attempt == 2:
                        raise
            problems = stages._review_batch_targets(
                str(version.id), (criterion.category,), result, candidates
            )
            candidate_keys = {rule.rule_key for rule in candidates}
            reviewed_keys = [review.rule_key for review in result.reviews]
            if (
                len(reviewed_keys) != len(set(reviewed_keys))
                or set(reviewed_keys) != candidate_keys
            ):
                problems.append("Independent review must cover exactly every candidate key once.")
            missing_keys = [rule.rule_key for rule in result.missing_rules]
            if len(missing_keys) != len(set(missing_keys)) or candidate_keys.intersection(
                missing_keys
            ):
                problems.append("Independent missing-rule inventory repeats an existing rule key.")
            if any(criterion_for_key(rule.rule_key) != criterion for rule in result.missing_rules):
                problems.append("Independent missing-rule inventory is outside this criterion.")
            if problems:
                raise ValueError("; ".join(problems))
            request_review_correction(criterion, progress["criteria"][criterion.key], result)
        except (RelayFailure, ValueError) as exc:
            if isinstance(exc, RelayFailure) and exc.code not in CRITERION_FAILURES:
                raise
            result = PolicyRuleReviewV1(
                schema_version=1,
                policy_version_id=str(version.id),
                inventory_categories=[criterion.category],
                reviews=[
                    ReviewedPolicyRule(
                        rule_key=rule.rule_key,
                        verdict="ambiguous",
                        independent_body=None,
                        evidence_span_ids=[],
                        material_issue=f"Independent review failed: {exc}",
                    )
                    for rule in candidates
                ],
                missing_rules=[],
            )
        results.append(((criterion.category,), result))
    return {
        **stages._combine_review_batches(str(version.id), results).model_dump(mode="json"),
        PROGRESS_KEY: progress,
    }


def validated_criteria(
    extraction: PolicyRuleExtractionV1,
    review: PolicyRuleReviewV1,
    verified: list[Any],
    issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Account for exactly 13 source criteria, retaining partial values and unknown reasons."""
    by_key = {rule.rule_key: rule for rule in verified}
    results = []
    for criterion in CRITERIA:
        candidates = [
            rule for rule in extraction.rules if criterion_for_key(rule.rule_key) == criterion
        ]
        supported = [by_key[rule.rule_key] for rule in candidates if rule.rule_key in by_key]
        reasons = [reason for reason in extraction.material_issues if criterion.key + ":" in reason]
        for candidate in candidates:
            if candidate.rule_key in by_key:
                continue
            reasons.extend(
                str(issue["description"])
                for issue in issues
                if candidate.rule_key in str(issue.get("description", ""))
            )
            reasons.extend(
                item.material_issue or f"Independent verdict: {item.verdict}."
                for item in review.reviews
                if item.rule_key == candidate.rule_key and item.verdict != "agree"
            )
            if not reasons:
                reasons.append(
                    f"{candidate.rule_key}: independent agreement and deterministic validation were not both established."
                )
        missing = [
            rule.rule_key
            for rule in review.missing_rules
            if criterion_for_key(rule.rule_key) == criterion
        ]
        if missing:
            reasons.append(
                "Independent review found additional source-supported rules missing from extraction: "
                + ", ".join(missing)
            )
        if not candidates and not reasons:
            reasons.append(
                "The complete core evidence and any applicable prospectus supplement yielded no validated rule for this criterion."
            )
        results.append(
            {
                "criterion": criterion.key,
                "status": "supported"
                if supported and len(supported) == len(candidates) and not reasons
                else "unknown",
                "rule_ids": [str(rule.id) for rule in supported],
                "unknown_reasons": list(dict.fromkeys(reasons)),
            }
        )
    return results


def finalize_criterion_validation(job: ProcessingJob, artifact: dict[str, Any]) -> dict[str, Any]:
    from . import stages

    extraction_artifact = read_artifact(stages._ancestor(job, "extract"))
    extraction = PolicyRuleExtractionV1.model_validate(extraction_payload(extraction_artifact))
    review = PolicyRuleReviewV1.model_validate(extraction_payload(read_artifact(job.parent_job)))
    rules = list(
        PolicyRule.objects.filter(id__in=artifact["verified_rule_ids"], review_status="verified")
    )
    statuses = validated_criteria(extraction, review, rules, artifact["issues"])
    unknown_count = sum(item["status"] == "unknown" for item in statuses)
    artifact.update(
        manifest_processing_version=PROCESSING_VERSION,
        criteria=statuses,
        criterion_count=13,
        unresolved_criterion_count=unknown_count,
        extraction_retry_protocol=RETRY_PROTOCOL,
        prospectus_criteria=[
            key
            for key, value in extraction_artifact[PROGRESS_KEY]["criteria"].items()
            if value["prospectus_used"]
        ],
        prospectus_reasons={
            key: value["prospectus_reason"]
            for key, value in extraction_artifact[PROGRESS_KEY]["criteria"].items()
            if value["prospectus_used"]
        },
        timeout_call_count=ModelAttempt.objects.filter(
            processing_job__source_capture=job.source_capture,
            status="timeout",
        ).count(),
        budget={
            "status": "unavailable",
            "reason": "No approved premium table or quote is available for this base variant.",
        },
    )
    derived_ids = []
    derived_reasons = []
    copay = next(item for item in statuses if item["criterion"] == "copay")
    if copay["status"] != "supported":
        derived_reasons.append(
            "Copay remains unresolved; no_copay cannot be inferred from missing evidence."
        )
    else:
        by_key = {rule.rule_key: rule for rule in rules}
        for source in [rule for rule in rules if str(rule.id) in copay["rule_ids"]]:
            if not has_copay_value(source.body):
                continue
            body = no_copay_body(source.rule_key, source.body)
            if body is None:
                derived_reasons.append(
                    f"{source.rule_key}: copay is not a supported literal rate or explicit non-application; no Boolean value was inferred."
                )
                continue
            validate_contract("RuleV1", body)
            problems = rule_semantic_problems(body)
            if problems:
                raise ValueError(
                    "Derived no_copay violates the existing rule contract: " + "; ".join(problems)
                )
            key = (
                "copay.definition.no_copay_"
                + hashlib.sha256(source.rule_key.encode()).hexdigest()[:16]
            )
            derived = stages._get_or_create_policy_rule_revision(
                policy_version=source.policy_version,
                rule_key=key,
                rule_type="definition",
                body=body,
                revalidate_derived_head=True,
            )
            for row in PolicyRuleEvidence.objects.filter(policy_rule=source):
                PolicyRuleEvidence.objects.get_or_create(
                    policy_rule=derived,
                    evidence_span=row.evidence_span,
                    role=row.role,
                    defaults={"is_required": row.is_required},
                )
            for dependency, link_type in rule_link_references(body):
                PolicyRuleLink.objects.get_or_create(
                    from_policy_rule=derived, to_policy_rule=by_key[dependency], link_type=link_type
                )
            derived.review_status = "verified"
            derived.save(update_fields=["review_status"])
            if derived.supersedes_id:
                PolicyRule.objects.filter(pk=derived.supersedes_id).update(
                    review_status="superseded"
                )
            derived_ids.append(str(derived.id))
        if not derived_ids and not derived_reasons:
            derived_reasons.append("No validated copay rate supports a Boolean no_copay result.")
    artifact["verified_rule_ids"].extend(derived_ids)
    artifact["no_copay"] = {
        "status": "derived" if derived_ids and not derived_reasons else "unknown",
        "rule_ids": derived_ids,
        "unknown_reasons": derived_reasons,
    }
    if unknown_count >= 7:
        artifact["issues"].append(
            stages.issue(
                "criterion_stop_threshold",
                f"STOP: {unknown_count} of this plan's 13 criteria remain unresolved after validation.",
                material=True,
                retry_instruction="Stop the slice and present the unresolved criteria for human review.",
            )
        )
        artifact["index_pending"] = False
    return artifact
