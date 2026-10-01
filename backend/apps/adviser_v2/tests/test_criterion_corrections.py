from copy import deepcopy

import pytest

from apps.adviser_v2.processing.criterion_attempts import new_criterion_state
from apps.adviser_v2.processing.criterion_corrections import request_review_correction
from apps.adviser_v2.processing.criterion_evidence import CRITERIA, PROGRESS_KEY, extraction_payload
from apps.adviser_v2.schemas import PolicyRuleReviewV1, ReviewedPolicyRule


@pytest.mark.parametrize(
    "attempts,transport,should_correct", [(1, 0, True), (1, 2, True), (2, 0, False), (1, 3, False)]
)
def test_independent_source_failure_cannot_expand_either_retry_budget(
    attempts, transport, should_correct
):
    criterion = CRITERIA[0]
    state = new_criterion_state()
    state.update(
        validation_attempts=attempts,
        transport_failures=transport,
        complete=True,
        result={"untouched": "retained response"},
    )
    original = deepcopy(state["result"])
    review = PolicyRuleReviewV1(
        schema_version=1,
        policy_version_id="policy",
        inventory_categories=[criterion.category],
        reviews=[
            ReviewedPolicyRule(
                rule_key="sum_insured_choices.coverage.sum_insured_choice",
                verdict="disagree",
                independent_body=None,
                evidence_span_ids=[],
                material_issue="needs_prospectus: The cited treatment sublimit table does not establish purchase options.",
            )
        ],
        missing_rules=[],
    )
    request_review_correction(criterion, state, review)
    assert state["complete"] is not should_correct
    assert state["validation_attempts"] == attempts
    assert state["transport_failures"] == transport
    assert state["result"] == original
    assert state["prospectus_used"] is should_correct
    if should_correct:
        assert "purchase options" in state["last_error"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "v2,correction,next_stage",
    [(True, True, "extract"), (True, False, "validate"), (False, False, "validate")],
)
def test_review_schedules_only_unspent_v2_corrections_before_validation(
    monkeypatch, v2, correction, next_stage
):
    from apps.adviser_v2 import pipeline
    from apps.adviser_v2.models import ProcessingJob
    from apps.adviser_v2.processing.artifacts import read_artifact
    from apps.adviser_v2.processing.criterion_evidence import RETRY_PROTOCOL
    from apps.adviser_v2.tests.test_pipeline import public_html_capture

    capture = public_html_capture()
    monkeypatch.setattr(pipeline, "manifest_product", lambda _: {} if v2 else None)
    reconcile = ProcessingJob.objects.create(
        source_capture=capture,
        stage="reconcile",
        state="succeeded",
        adapter_version="test",
        input_commitment="a" * 64,
    )
    extraction = ProcessingJob.objects.create(
        source_capture=capture,
        parent_job=reconcile,
        stage="extract",
        state="succeeded",
        adapter_version="test",
        input_commitment="b" * 64,
    )
    review = pipeline.enqueue_stage(
        stage="independent_review", source_capture=capture, parent_job=extraction
    )
    result = PolicyRuleReviewV1(
        schema_version=1,
        policy_version_id="policy",
        inventory_categories=[],
        reviews=[],
        missing_rules=[],
    ).model_dump(mode="json")
    if v2:
        result[PROGRESS_KEY] = {
            "protocol": RETRY_PROTOCOL,
            "criteria": {"copay": {"complete": not correction}},
        }
    monkeypatch.setitem(pipeline.STAGE_RUNNERS, "independent_review", lambda _: result)
    pipeline.process_job(review.id)
    queued = ProcessingJob.objects.get(source_capture=capture, state="queued")
    assert queued.stage == next_stage
    assert queued.parent_job_id == (reconcile.id if correction else review.id)
    assert queued.attempt_number == (2 if correction else 1)
    review.refresh_from_db()
    assert review.state == "succeeded"
    PolicyRuleReviewV1.model_validate(extraction_payload(read_artifact(review)))
