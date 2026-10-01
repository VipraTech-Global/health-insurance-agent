"""Manifest-v2 cited facts, through the existing extraction/review processing stages.

The qualified wire schemas and routes are unchanged. Text-definition carriers are
descriptive only and never promoted to executable rules. Prior rule validation is
retained separately. Every model call and progress artifact remains auditable.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings

from apps.adviser.ai import RelayFailure

from ..model_gateway import call_model
from ..models import ModelAttempt, PolicyRule, ProcessingJob
from ..schemas import PolicyRuleExtractionV1, PolicyRuleReviewV1
from .artifacts import read_artifact
from .cited_facts import (
    FACT_PROTOCOL,
    FACT_SYSTEM,
    REVIEW_SYSTEM,
    CitedFact,
    carrier_fact,
    fact_carrier,
    fact_instruction,
    fact_problems,
    review_disposition,
)
from .clause_citations import store_clause
from .criterion_attempts import TRANSPORT_FAILURES, extract_criterion, new_criterion_state
from .criterion_evidence import CRITERIA, PROGRESS_KEY, request_bytes_with_headroom
from .manifest_v2 import raw_bundle_passages

log = logging.getLogger(__name__)
SEED = Path(__file__).resolve().parents[4] / "data/manifests/star-three-plan-retained-facts.json"


def _encoded(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _checkpoint(job: ProcessingJob, progress: dict[str, Any]) -> None:
    from ..pipeline import _finish_job

    _finish_job(job, job.lease_token, state="running", result={PROGRESS_KEY: progress},
                issues=job.issues, expected_erasure_generation=None)


def _progress(job: ProcessingJob, policy_id: str, core: list[dict[str, Any]]) -> dict[str, Any]:
    digest = hashlib.sha256(_encoded(core).encode()).hexdigest()
    previous = ProcessingJob.objects.filter(
        source_capture=job.source_capture, result_storage_key__isnull=False,
    ).exclude(pk=job.pk).order_by("-created_at")
    prior_validation = None
    for old in previous:
        artifact = read_artifact(old)
        progress = artifact.get(PROGRESS_KEY)
        if progress and progress.get("protocol") == FACT_PROTOCOL:
            if progress["policy_version_id"] != policy_id or progress["core_evidence_sha256"] != digest:
                raise ValueError("Retained cited facts do not match this exact source bundle.")
            return progress
        if prior_validation is None and old.stage == "validate":
            prior_validation = old
    progress = {
        "protocol": FACT_PROTOCOL, "policy_version_id": policy_id,
        "core_evidence_sha256": digest, "criteria": {},
        "prior_validation_id": str(prior_validation.id) if prior_validation else None,
    }
    # Only the three previously accepted Comprehensive criteria are projected.
    # Failed criteria start the newly authorized fact run with one correction.
    seeds = json.loads(SEED.read_text()) if SEED.exists() else {}
    if seeds.get("policy_version_id") == policy_id:
        if prior_validation is None or str(prior_validation.id) != seeds["validation_job_id"]:
            raise ValueError("Accepted fact projection no longer matches its reviewed validation.")
        baseline = read_artifact(prior_validation)
        for criterion in CRITERIA:
            if criterion.key not in seeds["criteria"]:
                continue
            old_status = next(row for row in baseline["criteria"] if row["criterion"] == criterion.key)
            if old_status["status"] != "supported" or not old_status["rule_ids"]:
                raise ValueError("Only accepted criteria may reuse the prior independent review.")
            if PolicyRule.objects.filter(id__in=old_status["rule_ids"], review_status="verified").count() != len(old_status["rule_ids"]):
                raise ValueError("Retained rule review has changed.")
            fact = CitedFact.model_validate(seeds["criteria"][criterion.key])
            result = PolicyRuleExtractionV1(schema_version=1, policy_version_id=policy_id,
                rules=[fact_carrier(criterion, fact)], omitted_inventory_categories=[], material_issues=[])
            problems = fact_problems(policy_id, criterion, result, core)
            if problems:
                raise ValueError("Retained accepted fact projection: " + "; ".join(problems))
            state = new_criterion_state()
            state.update(complete=True, result=result.model_dump(mode="json"), reused_validation_id=str(prior_validation.id),
                rule_ids=old_status["rule_ids"], review_blockers=[], review_notes=["Reused accepted extraction and independent review; quotations narrowed to exact clauses."], review_complete=True)
            progress["criteria"][criterion.key] = state
    return progress


def _messages(version: Any, passages: list[dict[str, Any]], criterion: Any, *, candidate: Any = None, feedback: str = "") -> list[dict[str, str]]:
    from .stages import _selected_variant_name

    result = [
        {"role": "system", "content": REVIEW_SYSTEM if candidate is not None else FACT_SYSTEM},
        {"role": "user", "content": f"Policy version {version.id}, UIN {version.uin}. Selected variant: {_selected_variant_name(version)}. Complete raw bundle: " + _encoded(passages)},
        {"role": "system", "content": fact_instruction(criterion)},
    ]
    if candidate is not None:
        result.append({"role": "user", "content": "Review this candidate against the full bundle: " + candidate.model_dump_json()})
    if feedback:
        result.append({"role": "system", "content": feedback})
    return result


def run_criterion_extraction(job: ProcessingJob) -> dict[str, Any]:
    from . import stages

    version = stages._policy_version(job)
    core = raw_bundle_passages(version)
    progress = _progress(job, str(version.id), core)
    full = None
    deadline = time.monotonic() + stages.RULE_STAGE_TIMEOUT_SECONDS

    def supplement() -> list[dict[str, Any]]:
        nonlocal full
        if full is None:
            full = raw_bundle_passages(version, include_prospectus=True)
        return full

    for criterion in CRITERIA:
        state = progress["criteria"].setdefault(criterion.key, new_criterion_state())
        if criterion.key in {"sum_insured", "eligibility"} and not state["complete"]:
            state.update(prospectus_used=True, prospectus_reason="Required on first call for sum insured and eligibility by the reviewed fact protocol.")

        def invoke(pages: list[dict[str, Any]], feedback: str, criterion: Any = criterion, state: dict[str, Any] = state) -> PolicyRuleExtractionV1:
            before = set(ModelAttempt.objects.filter(processing_job=job).values_list("id", flat=True))
            messages = _messages(version, pages, criterion, feedback=feedback)
            size = request_bytes_with_headroom(settings.COVERGUIDE_POLICY_EXTRACTION_MODEL, messages, PolicyRuleExtractionV1.model_json_schema())
            log.info("Cited-fact extraction %s: %s bytes, %s full pages, prospectus=%s", criterion.key, size, len(pages), state["prospectus_used"])
            stages._renew_rule_lease(job)
            state.pop("review_complete", None)
            try:
                return call_model(model=settings.COVERGUIDE_POLICY_EXTRACTION_MODEL, schema_name="policy_extraction",
                    output_type=PolicyRuleExtractionV1, messages=messages, processing_job=job,
                    remaining_seconds=stages._remaining_rule_seconds(deadline), reuse_successful_processing_result=True,
                    reasoning_effort=settings.COVERGUIDE_POLICY_EXTRACTION_REASONING_EFFORT,
                    max_output_tokens=settings.COVERGUIDE_POLICY_EXTRACTION_MAX_OUTPUT_TOKENS)
            finally:
                state["attempt_ids"].extend(str(pk) for pk in ModelAttempt.objects.filter(processing_job=job).exclude(id__in=before).values_list("id", flat=True))

        extract_criterion(policy_id=str(version.id), criterion=criterion, core=core, supplement=supplement,
            state=state, invoke=invoke, checkpoint=lambda: _checkpoint(job, progress), validate=fact_problems)
    # The wire envelope is retained, but carriers never enter executable validation.
    results = [PolicyRuleExtractionV1.model_validate(s["result"]) for s in progress["criteria"].values()]
    return {**PolicyRuleExtractionV1(schema_version=1, policy_version_id=str(version.id),
        rules=[r for result in results for r in result.rules],
        omitted_inventory_categories=sorted({c for result in results for c in result.omitted_inventory_categories}),
        material_issues=[i for result in results for i in result.material_issues]).model_dump(mode="json"), PROGRESS_KEY: progress}


def run_criterion_review(job: ProcessingJob) -> dict[str, Any]:
    from . import stages
    from .criterion_pipeline import CRITERION_FAILURES

    version = stages._policy_version(job)
    progress = read_artifact(job.parent_job)[PROGRESS_KEY]
    core = raw_bundle_passages(version)
    full = None
    deadline = time.monotonic() + stages.RULE_STAGE_TIMEOUT_SECONDS
    for criterion in CRITERIA:
        state = progress["criteria"][criterion.key]
        if state.get("review_complete"):
            continue
        extraction = PolicyRuleExtractionV1.model_validate(state["result"])
        if state["result_prospectus_used"] and full is None:
            full = raw_bundle_passages(version, include_prospectus=True)
        pages = full if state["result_prospectus_used"] else core
        blockers = fact_problems(str(version.id), criterion, extraction, pages)
        blockers.extend(extraction.material_issues)
        notes = []
        if not blockers and extraction.rules:
            messages = _messages(version, pages, criterion, candidate=extraction)
            request_bytes_with_headroom(settings.COVERGUIDE_POLICY_REVIEW_MODEL, messages, PolicyRuleReviewV1.model_json_schema())
            try:
                for transport_attempt in range(3):
                    stages._renew_rule_lease(job)
                    try:
                        review = call_model(model=settings.COVERGUIDE_POLICY_REVIEW_MODEL, schema_name="policy_review",
                            output_type=PolicyRuleReviewV1, messages=messages, processing_job=job,
                            remaining_seconds=stages._remaining_rule_seconds(deadline), reuse_successful_processing_result=True,
                            reasoning_effort="high")
                        state["review"] = review.model_dump(mode="json")
                        blockers, notes = review_disposition(review, extraction, criterion)
                        break
                    except RelayFailure as exc:
                        if exc.code not in TRANSPORT_FAILURES or transport_attempt == 2:
                            raise
                        state["review_transport_failures"] = state.get("review_transport_failures", 0) + 1
                        _checkpoint(job, progress)
            except RelayFailure as exc:
                if exc.code not in CRITERION_FAILURES:
                    raise
                blockers = [f"Independent fact review failed: {exc.code}."]
                state["review_technical_failure"] = True
        state.update(review_blockers=blockers, review_notes=notes, review_complete=True)
        if blockers and state["validation_attempts"] < 2 and not state.get("review_technical_failure") and state["transport_failures"] <= 2:
            state.update(complete=False, last_error="Independent fact validation: " + "; ".join(blockers))
            if "needs_prospectus:" in state["last_error"]:
                state.update(prospectus_used=True, prospectus_reason=state["last_error"])
        _checkpoint(job, progress)
    return {"schema_version": 1, "policy_version_id": str(version.id), "inventory_categories": sorted({c.category for c in CRITERIA}),
        "reviews": [], "missing_rules": [], PROGRESS_KEY: progress}


def validate_facts(job: ProcessingJob) -> dict[str, Any]:
    from . import stages

    version = stages._policy_version(job)
    progress = read_artifact(job.parent_job)[PROGRESS_KEY]
    pages = raw_bundle_passages(version, include_prospectus=True)
    by_id = {p["evidence_span_id"]: p for p in pages}
    previous = read_artifact(ProcessingJob.objects.get(pk=progress["prior_validation_id"])) if progress["prior_validation_id"] else {}
    statuses = []
    for criterion in CRITERIA:
        state = progress["criteria"][criterion.key]
        result = PolicyRuleExtractionV1.model_validate(state["result"])
        reasons = fact_problems(str(version.id), criterion, result, pages)
        reasons.extend(state.get("review_blockers", ["Independent source review is missing."]))
        reasons.extend(result.material_issues)
        fact = carrier_fact(result.rules[0]) if result.rules and not reasons else None
        citations = []
        if fact:
            for clause in fact.citations:
                try:
                    span = store_clause(clause, by_id[clause.page_span_id])
                except ValueError as exc:
                    reasons.append("Clause citation failed validation: " + str(exc))
                    continue
                citations.append({"evidence_span_id": str(span.id), "document_key": by_id[clause.page_span_id]["document_key"],
                    "document_version_id": by_id[clause.page_span_id]["document_version_id"], "page": span.page.page_number,
                    "quote": span.quote, "context": span.context, "locator": span.locator})
        old = next((row for row in previous.get("criteria", []) if row["criterion"] == criterion.key), {})
        rule_ids = old.get("rule_ids", [])
        statuses.append({
            "criterion": criterion.key, "status": "supported" if fact and not reasons else "unknown",
            "value": fact.value if fact else None, "value_kind": fact.value_kind if fact else None,
            "conditions": [c.model_dump() for c in fact.conditions] if fact else [],
            "quantities": [q.model_dump() for q in fact.quantities] if fact else [],
            "notes": [*(fact.notes if fact else []), *state.get("review_notes", [])],
            "citations": citations, "unknown_reasons": list(dict.fromkeys(reasons)), "rule_ids": rule_ids,
            "rule_status": "executable" if state.get("reused_validation_id") else "rule not executable",
            "rule_reasons": [] if state.get("reused_validation_id") else [
                "The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.",
                *old.get("unknown_reasons", []),
            ],
            "reused_validation_id": state.get("reused_validation_id"),
        })
    unresolved = sum(row["status"] == "unknown" for row in statuses)
    artifact = {
        "schema_version": 1, "policy_version_id": str(version.id),
        "manifest_processing_version": FACT_PROTOCOL, "extraction_retry_protocol": FACT_PROTOCOL,
        "criteria": statuses, "criterion_count": 13, "unresolved_criterion_count": unresolved,
        "verified_rule_ids": previous.get("verified_rule_ids", []),
        "prospectus_criteria": [k for k, s in progress["criteria"].items() if s["prospectus_used"]],
        "prospectus_reasons": {k: s["prospectus_reason"] for k, s in progress["criteria"].items() if s["prospectus_used"]},
        "timeout_call_count": ModelAttempt.objects.filter(processing_job__source_capture=job.source_capture, status="timeout").count(),
        "budget": {"status": "unavailable", "reason": "No approved premium table or quote is available for this base variant."},
        "issues": [], "index_pending": False, "review_checkpoint_only": True,
        PROGRESS_KEY: progress,
    }
    copay = next(row for row in statuses if row["criterion"] == "copay")
    rates = sorted({Decimal(q["value"]) for q in copay["quantities"] if q["unit"] == "ratio"})
    artifact["no_copay"] = {
        "status": "derived" if copay["status"] == "supported" and rates else "unknown",
        "value": ("No copay where the quoted zero rate applies. " if rates == [0] else "No copay is not unconditional. ") + copay["value"] if copay["status"] == "supported" and rates else None,
        "conditions": copay["conditions"], "citations": copay["citations"],
        "rate_results": [{"copay_rate": str(rate), "no_copay": rate == 0} for rate in rates],
        "unknown_reasons": [] if copay["status"] == "supported" and rates else ["A supported copay fact with quoted normalized rates is required."],
        "rule_ids": [], "rule_status": "rule not executable",
    }
    if unresolved >= 7:
        artifact["issues"].append(stages.issue("criterion_stop_threshold", f"STOP: {unresolved} of 13 cited facts remain unresolved.", material=True, retry_instruction="Present the unresolved criteria for human review."))
    return artifact
