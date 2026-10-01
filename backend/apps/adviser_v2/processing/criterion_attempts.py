"""Separate version-2 transport retries from the single validation correction."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from apps.adviser.ai import RelayFailure

from ..schemas import PolicyRuleExtractionV1
from .criterion_evidence import Criterion, criterion_rule_problems

TRANSPORT_FAILURES = {"provider_timeout", "provider_transport", "provider_unavailable"}
OUTPUT_FAILURES = {"invalid_structured_output", "incomplete_response", "malformed_response"}


def new_criterion_state() -> dict[str, Any]:
    return {
        "validation_attempts": 0,
        "transport_failures": 0,
        "prospectus_used": False,
        "prospectus_reason": None,
        "result_prospectus_used": False,
        "attempt_ids": [],
        "result": None,
        "last_error": None,
        "complete": False,
    }


def unknown_result(policy_id: str, criterion: Criterion, reason: str) -> PolicyRuleExtractionV1:
    return PolicyRuleExtractionV1(
        schema_version=1,
        policy_version_id=policy_id,
        rules=[],
        omitted_inventory_categories=[criterion.category],
        material_issues=[f"{criterion.category}: {criterion.key}: {reason}"],
    )


def extraction_problems(
    policy_id: str,
    criterion: Criterion,
    result: PolicyRuleExtractionV1,
    passages: list[dict[str, Any]],
) -> list[str]:
    from . import stages

    problems = stages._extraction_batch_targets(policy_id, (criterion.category,), result)
    for rule in result.rules:
        problems.extend(
            f"{rule.rule_key}: {problem}"
            for problem in criterion_rule_problems(rule, criterion, passages)
        )
    if not result.rules and not result.material_issues:
        problems.append("Provide a source-specific reason for this unknown criterion.")
    return problems


def extract_criterion(
    *,
    policy_id: str,
    criterion: Criterion,
    core: list[dict[str, Any]],
    supplement: Callable[[], list[dict[str, Any]]],
    state: dict[str, Any],
    invoke: Callable[[list[dict[str, Any]], str], PolicyRuleExtractionV1],
    checkpoint: Callable[[], None],
    validate: Callable[..., list[str]] | None = None,
) -> PolicyRuleExtractionV1:
    """Resume retained responses, allowing two transport retries and one correction.

    Transport failures never advance validation_attempts. Each retry keeps the
    exact request, including the selected complete documents and correction context.
    """

    def finish(result: PolicyRuleExtractionV1) -> PolicyRuleExtractionV1:
        state.update(result=result.model_dump(mode="json"), complete=True)
        checkpoint()
        return result

    if state["complete"]:
        return PolicyRuleExtractionV1.model_validate(state["result"])
    while True:
        result = (
            PolicyRuleExtractionV1.model_validate(state["result"])
            if state["result"] is not None
            else None
        )
        previous_pages = supplement() if state["result_prospectus_used"] else core
        problems = (
            (validate or extraction_problems)(policy_id, criterion, result, previous_pages) if result else []
        )
        missing_core = (
            [reason for reason in result.material_issues if "needs_prospectus:" in reason]
            if result
            else []
        )
        needs_prospectus = bool(missing_core) and not state["result_prospectus_used"]
        if result is not None and not problems and not needs_prospectus and not state["last_error"]:
            return finish(result)
        if state["validation_attempts"] >= 2:
            if state["last_error"] or result is None:
                return finish(
                    unknown_result(
                        policy_id,
                        criterion,
                        "Extraction output still failed validation after one corrective retry: "
                        + str(state["last_error"] or "no_valid_response")
                        + ".",
                    )
                )
            return finish(result)
        if state["transport_failures"] > 2:
            return finish(
                unknown_result(
                    policy_id,
                    criterion,
                    "Extraction transport failed after two separate transport retries: "
                    + str(state["last_error"])
                    + ". The corrective retry was not consumed by transport failures.",
                )
            )
        if needs_prospectus:
            state["prospectus_used"] = True
            state["prospectus_reason"] = "; ".join(missing_core)
            problems.append(
                "The core evidence leaves the identified part unanswered. The complete applicable prospectus is now supplied."
            )
        supplied = supplement() if state["prospectus_used"] else core
        feedback = ""
        if state["validation_attempts"]:
            feedback = (
                "This is the one corrective extraction retry for failed validation. "
                "Return a complete replacement for this criterion, retaining correct rules. "
                + ("Previous output: " + result.model_dump_json() + " " if result else "")
                + "Validation failures: "
                + "; ".join(problems or [str(state["last_error"])])
            )
        while True:
            try:
                returned = invoke(supplied, feedback)
            except RelayFailure as exc:
                state["last_error"] = exc.code
                if exc.code == "context_limit":
                    return finish(
                        unknown_result(
                            policy_id,
                            criterion,
                            "Complete evidence exceeds the request bound; no source text was truncated.",
                        )
                    )
                if exc.code in TRANSPORT_FAILURES:
                    state["transport_failures"] += 1
                    checkpoint()
                    if state["transport_failures"] <= 2:
                        continue
                    return finish(
                        unknown_result(
                            policy_id,
                            criterion,
                            f"Extraction transport failed after two separate transport retries: {exc.code}. "
                            "Transport failures did not consume the corrective retry.",
                        )
                    )
                if exc.code not in OUTPUT_FAILURES:
                    raise
                state["validation_attempts"] += 1
                checkpoint()
                break
            except ValueError as exc:
                return finish(
                    unknown_result(
                        policy_id,
                        criterion,
                        f"Complete extraction request validation failed: {exc}",
                    )
                )
            else:
                state["validation_attempts"] += 1
                state["result"] = returned.model_dump(mode="json")
                state["result_prospectus_used"] = state["prospectus_used"]
                state["last_error"] = None
                checkpoint()
                break
