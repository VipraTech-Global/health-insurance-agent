from copy import deepcopy

import pytest
from research_workspace.legacy_relay import RelayFailure

from apps.adviser_v2.processing import criterion_attempts as module
from apps.adviser_v2.processing.criterion_evidence import (
    CRITERIA,
    PROGRESS_KEY,
    RETRY_PROTOCOL,
    extraction_payload,
)


def run_sequence(monkeypatch, sequence, state=None):
    criterion = CRITERIA[0]
    core = [{"document_role": "base_wording"}]
    full = core + [{"document_role": "prospectus"}]
    calls, snapshots = [], []
    state = state or module.new_criterion_state()
    monkeypatch.setattr(
        module,
        "extraction_problems",
        lambda *args: ["invalid quantity"] if args[2].material_issues == ["bad"] else [],
    )
    outcomes = iter(sequence)

    def invoke(pages, feedback):
        calls.append((deepcopy(pages), feedback))
        outcome = next(outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return module.unknown_result("policy", criterion, outcome).model_copy(
            update={"material_issues": [outcome]}
        )

    result = module.extract_criterion(
        policy_id="policy",
        criterion=criterion,
        core=core,
        supplement=lambda: full,
        state=state,
        invoke=invoke,
        checkpoint=lambda: snapshots.append(deepcopy(state)),
    )
    return result, state, calls, snapshots


def failure(code):
    return RelayFailure(code, "Safe error")


def test_transport_retries_preserve_the_validation_correction(monkeypatch):
    _, state, calls, snapshots = run_sequence(
        monkeypatch,
        [failure("provider_timeout"), failure("provider_transport"), "bad", "supported"],
    )
    assert state["validation_attempts"] == 2
    assert state["transport_failures"] == 2
    assert calls[0] == calls[1] == calls[2]
    assert "invalid quantity" in calls[3][1]
    assert all(len(pages) == 1 for pages, _ in calls)
    assert snapshots[-1]["complete"]


def test_three_transport_failures_stop_without_spending_correction(monkeypatch):
    result, state, calls, _ = run_sequence(monkeypatch, [failure("provider_timeout")] * 3)
    assert len(calls) == 3
    assert state["validation_attempts"] == 0
    assert "two separate transport retries" in result.material_issues[0]
    assert not state["prospectus_used"]


def test_schema_correction_can_retry_transport_separately(monkeypatch):
    _, state, calls, _ = run_sequence(
        monkeypatch,
        [failure("invalid_structured_output"), failure("provider_unavailable"), "supported"],
    )
    assert calls[1] == calls[2]
    assert state["validation_attempts"] == 2
    assert state["transport_failures"] == 1


def test_prospectus_only_follows_explicit_missing_core_evidence(monkeypatch):
    _, state, calls, _ = run_sequence(
        monkeypatch, ["needs_prospectus: Adult entry-age definition absent from core.", "supported"]
    )
    assert len(calls[0][0]) == 1
    assert len(calls[1][0]) == 2
    assert state["prospectus_used"] and state["result_prospectus_used"]
    assert "Adult entry-age" in state["prospectus_reason"]


def test_legitimate_unknown_never_automatically_adds_prospectus(monkeypatch):
    _, state, calls, _ = run_sequence(monkeypatch, ["Customer entry age is unknown."])
    assert len(calls) == 1
    assert not state["prospectus_used"]


def test_retained_response_reuses_completed_work(monkeypatch):
    _, state, _, _ = run_sequence(monkeypatch, ["supported"])
    state["complete"] = False
    _, _, calls, _ = run_sequence(monkeypatch, [], state)
    assert calls == []


def test_source_quote_failure_uses_only_the_remaining_correction(monkeypatch):
    _, state, _, _ = run_sequence(monkeypatch, ["supported"])
    state.update(
        complete=False, last_error="Quoted applicability includes II.25; the candidate omits it."
    )
    _, corrected, calls, _ = run_sequence(monkeypatch, ["corrected scope"], state)
    assert len(calls) == 1
    assert "II.25" in calls[0][1]
    assert corrected["validation_attempts"] == 2
    assert corrected["complete"] and corrected["last_error"] is None


def test_old_timeout_does_not_take_remaining_correction(monkeypatch):
    state = module.new_criterion_state()
    state.update(
        validation_attempts=1,
        transport_failures=1,
        result=module.unknown_result("policy", CRITERIA[0], "bad")
        .model_copy(update={"material_issues": ["bad"]})
        .model_dump(mode="json"),
    )
    _, state, calls, _ = run_sequence(monkeypatch, ["supported"], state)
    assert len(calls) == 1 and state["validation_attempts"] == 2


def test_internal_progress_is_not_added_to_model_contract():
    payload = module.unknown_result("policy", CRITERIA[0], "unknown").model_dump(mode="json")
    assert extraction_payload({**payload, PROGRESS_KEY: {"protocol": RETRY_PROTOCOL}}) == payload
    with pytest.raises(ValueError):
        extraction_payload({**payload, PROGRESS_KEY: {"protocol": "wrong"}})
