"""Use an unspent criterion correction for a completed independent source review."""

from typing import Any

from apps.adviser_v2.schemas import PolicyRuleReviewV1

from research_workspace.legacy_v2.processing.criterion_evidence import Criterion


def request_review_correction(
    criterion: Criterion, state: dict[str, Any], review: PolicyRuleReviewV1
) -> None:
    if state["validation_attempts"] >= 2 or state["transport_failures"] > 2:
        return
    failures = [
        f"{item.rule_key}: {item.material_issue or item.verdict}"
        for item in review.reviews
        if item.verdict != "agree"
    ]
    if review.missing_rules:
        failures.append(
            "Independent review found omitted source rules: "
            + "; ".join(rule.model_dump_json() for rule in review.missing_rules)
        )
    if not failures:
        return
    feedback = f"Independent source validation failed for {criterion.key}: " + "; ".join(failures)
    state.update(complete=False, last_error=feedback)
    if "needs_prospectus:" in feedback and not state["prospectus_used"]:
        state.update(prospectus_used=True, prospectus_reason=feedback)


def has_remaining_correction(progress: dict[str, Any]) -> bool:
    return any(not state["complete"] for state in progress["criteria"].values())
