from __future__ import annotations

import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.adviser_v2.engine import _lock_active_turn, _terminal
from apps.adviser_v2.errors import TurnCancellationRequested, TurnLeaseLost
from apps.adviser_v2.models import (
    AuditEvent,
    CustomerUploadedDocument,
    OriginalFile,
    Outbox,
    ProcessingJob,
    Turn,
    TurnEvent,
)
from apps.adviser_v2.pipeline import enqueue_stage
from apps.adviser_v2.services.customer import create_conversation, submit_message
from apps.adviser_v2.services.outbox import dispatch_pending_outbox, recover_expired_work


def queued_turn(user: User) -> Turn:
    conversation = create_conversation(user.id)
    submitted = submit_message(
        user.id,
        conversation.id,
        request_id=uuid.uuid4(),
        text="Compare the five reviewed products.",
        expected_profile_revision=1,
    )
    return submitted.turn


@pytest.mark.django_db
def test_pending_turn_outbox_is_dispatched_once(v2_user: User) -> None:
    turn = queued_turn(v2_user)

    with patch("apps.adviser_v2.services.outbox.current_app.send_task") as send_task:
        assert dispatch_pending_outbox(limit=10) == 1
        assert dispatch_pending_outbox(limit=10) == 0

    send_task.assert_called_once_with(
        "adviser_v2.process_adviser_turn",
        args=[str(turn.id)],
        queue="conversation",
    )
    outbox = Outbox.objects.get(turn=turn)
    assert outbox.state == "delivered"
    assert outbox.attempt_count == 1
    assert outbox.lease_until is None
    assert outbox.last_error_code is None

    Outbox.objects.filter(pk=outbox.pk).update(available_at=timezone.now())
    with patch("apps.adviser_v2.services.outbox.current_app.send_task") as redelivery:
        assert dispatch_pending_outbox(limit=10) == 1
    redelivery.assert_called_once()
    outbox.refresh_from_db()
    assert outbox.attempt_count == 2

    Turn.objects.filter(pk=turn.pk).update(
        state="running",
        lease_token=uuid.uuid4(),
        lease_until=timezone.now() + timedelta(minutes=1),
    )
    Outbox.objects.filter(pk=outbox.pk).update(available_at=timezone.now())
    with patch("apps.adviser_v2.services.outbox.current_app.send_task") as duplicate:
        assert dispatch_pending_outbox(limit=10) == 0
    duplicate.assert_not_called()


@pytest.mark.django_db
def test_broker_failure_is_visible_and_retryable(v2_user: User) -> None:
    turn = queued_turn(v2_user)

    with patch(
        "apps.adviser_v2.services.outbox.current_app.send_task",
        side_effect=RuntimeError("broker unavailable"),
    ) as send_task:
        assert dispatch_pending_outbox(limit=10) == 1
        assert dispatch_pending_outbox(limit=10) == 0

    assert send_task.call_count == 1
    outbox = Outbox.objects.get(turn=turn)
    assert outbox.state == "failed"
    assert outbox.attempt_count == 1
    assert outbox.available_at > timezone.now()
    assert outbox.lease_until is None
    assert outbox.last_error_code == "broker_dispatch_failed"

    Outbox.objects.filter(pk=outbox.pk).update(available_at=timezone.now())
    with patch("apps.adviser_v2.services.outbox.current_app.send_task") as retry:
        assert dispatch_pending_outbox(limit=10) == 1
    retry.assert_called_once()
    outbox.refresh_from_db()
    assert outbox.state == "delivered"
    assert outbox.attempt_count == 2
    assert outbox.last_error_code is None


@pytest.mark.django_db(transaction=True)
def test_expired_running_turn_fails_closed_and_can_be_explicitly_retried(
    v2_user: User,
) -> None:
    turn = queued_turn(v2_user)
    Turn.objects.filter(pk=turn.pk).update(
        state="running",
        lease_token=uuid.uuid4(),
        lease_until=timezone.now() - timedelta(seconds=1),
    )

    assert recover_expired_work(limit=10) == {"turns": 1, "processing_jobs": 0}

    turn.refresh_from_db()
    assert turn.state == "failed"
    assert turn.error_code == "worker_lease_expired"
    assert turn.lease_token is None
    assert turn.lease_until is None
    assert TurnEvent.objects.filter(
        turn=turn,
        event_type="failed",
        payload={
            "schema_version": 1,
            "kind": "failed",
            "error_code": "worker_lease_expired",
        },
    ).exists()
    outbox = Outbox.objects.get(turn=turn)
    assert outbox.state == "delivered"


@pytest.mark.django_db(transaction=True)
def test_expired_document_work_is_requeued_for_durable_dispatch(v2_user: User) -> None:
    original = OriginalFile.objects.create(
        owner=v2_user,
        sha256="b" * 64,
        storage_key=f"private/{v2_user.id}/document-recovery-test.cg2",
        byte_size=1,
        media_type="application/pdf",
    )
    upload = CustomerUploadedDocument.objects.create(
        owner=v2_user,
        original_file=original,
        kind="quote",
    )
    job = enqueue_stage(
        owner_id=v2_user.id,
        customer_uploaded_document_id=upload.id,
        stage="classify",
    )
    ProcessingJob.objects.filter(pk=job.pk).update(
        state="running",
        lease_token=uuid.uuid4(),
        lease_until=timezone.now() - timedelta(seconds=1),
    )
    Outbox.objects.filter(processing_job=job).update(state="delivered")

    assert recover_expired_work(limit=10) == {"turns": 0, "processing_jobs": 1}

    job.refresh_from_db()
    assert job.state == "queued"
    assert job.lease_token is None
    assert job.lease_until is None
    outbox = Outbox.objects.get(processing_job=job)
    assert outbox.state == "pending"
    assert outbox.available_at <= timezone.now()
    assert AuditEvent.objects.filter(
        operation="processing_lease_recovered",
        object_id=job.id,
        outcome="succeeded",
    ).exists()


@pytest.mark.django_db(transaction=True)
def test_customer_mutation_fence_rejects_wrong_expired_and_cancelled_workers(
    v2_user: User,
) -> None:
    turn = queued_turn(v2_user)
    token = uuid.uuid4()
    Turn.objects.filter(pk=turn.pk).update(
        state="running",
        lease_token=token,
        lease_until=timezone.now() + timedelta(minutes=1),
    )

    with transaction.atomic():
        assert _lock_active_turn(turn.id, token).id == turn.id
    with pytest.raises(TurnLeaseLost, match="turn_lease_lost"):
        with transaction.atomic():
            _lock_active_turn(turn.id, uuid.uuid4())

    Turn.objects.filter(pk=turn.pk).update(lease_until=timezone.now() - timedelta(seconds=1))
    with pytest.raises(TurnLeaseLost, match="turn_lease_lost"):
        with transaction.atomic():
            _lock_active_turn(turn.id, token)

    Turn.objects.filter(pk=turn.pk).update(state="cancel_requested")
    with pytest.raises(TurnCancellationRequested, match="turn_cancel_requested"):
        with transaction.atomic():
            _lock_active_turn(turn.id, token)


@pytest.mark.django_db(transaction=True)
def test_expired_or_recovered_turn_cannot_be_resurrected(v2_user: User) -> None:
    turn = queued_turn(v2_user)
    token = uuid.uuid4()
    Turn.objects.filter(pk=turn.pk).update(
        state="running",
        lease_token=token,
        lease_until=timezone.now() - timedelta(seconds=1),
    )

    assert _terminal(turn.id, token, "completed") is False
    turn.refresh_from_db()
    assert turn.state == "running"

    assert recover_expired_work(limit=10)["turns"] == 1
    assert _terminal(turn.id, token, "completed") is False
    turn.refresh_from_db()
    assert turn.state == "failed"
    assert turn.error_code == "worker_lease_expired"


@pytest.mark.django_db(transaction=True)
def test_expired_cancel_request_becomes_durably_cancelled(v2_user: User) -> None:
    turn = queued_turn(v2_user)
    Turn.objects.filter(pk=turn.pk).update(
        state="cancel_requested",
        cancelled_at=timezone.now(),
        lease_token=uuid.uuid4(),
        lease_until=timezone.now() - timedelta(seconds=1),
    )

    assert recover_expired_work(limit=10)["turns"] == 1

    turn.refresh_from_db()
    assert turn.state == "cancelled"
    assert turn.error_code is None
    assert turn.lease_token is None
    assert turn.lease_until is None
    assert TurnEvent.objects.filter(turn=turn, event_type="cancelled").exists()
