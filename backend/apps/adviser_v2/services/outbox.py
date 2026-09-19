"""Lease and deliver durable v2 outbox records without duplicating inference."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from celery import current_app
from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone

from ..models import AuditEvent, Outbox, ProcessingJob, Turn
from .customer import append_turn_event

logger = logging.getLogger(__name__)

OUTBOX_LEASE = timedelta(seconds=30)
OUTBOX_RETRY_MAX_DELAY = timedelta(minutes=5)
OUTBOX_REDELIVERY_DELAY = timedelta(minutes=1)


@dataclass(frozen=True)
class ClaimedOutbox:
    id: uuid.UUID
    event_type: str
    target_id: uuid.UUID
    lease_until: datetime
    attempt_count: int


def _eligible(now: datetime) -> Q:
    undelivered = Q(state__in=["pending", "failed"], available_at__lte=now) | Q(
        state="leased", lease_until__lte=now
    )
    stranded = Q(state="delivered", available_at__lte=now) & (
        Q(event_type="turn_dispatch", turn__state="queued")
        | Q(event_type="document_processing", processing_job__state="queued")
    )
    return undelivered | stranded


def _target_id(row: Outbox) -> uuid.UUID:
    values = [row.turn_id, row.processing_job_id, row.knowledge_release_id]
    targets = [value for value in values if value is not None]
    if len(targets) != 1:
        raise ValueError("Outbox record does not resolve to exactly one target.")
    return targets[0]


@transaction.atomic
def _claim_next(*, outbox_id: uuid.UUID | None = None) -> ClaimedOutbox | None:
    now = timezone.now()
    rows = Outbox.objects.select_for_update(of=("self",), skip_locked=True).filter(_eligible(now))
    if outbox_id is not None:
        rows = rows.filter(pk=outbox_id)
    row = rows.order_by("available_at", "created_at", "id").first()
    if row is None:
        return None
    lease_until = now + OUTBOX_LEASE
    row.state = "leased"
    row.lease_until = lease_until
    row.attempt_count += 1
    row.save(update_fields=["state", "lease_until", "attempt_count", "updated_at"])
    return ClaimedOutbox(
        id=row.id,
        event_type=row.event_type,
        target_id=_target_id(row),
        lease_until=lease_until,
        attempt_count=row.attempt_count,
    )


@transaction.atomic
def _mark_delivered(claim: ClaimedOutbox) -> None:
    row = (
        Outbox.objects.select_for_update()
        .filter(pk=claim.id, state="leased", lease_until=claim.lease_until)
        .first()
    )
    if row is None:
        return
    row.state = "delivered"
    row.available_at = timezone.now() + OUTBOX_REDELIVERY_DELAY
    row.lease_until = None
    row.last_error_code = None
    row.save(
        update_fields=[
            "state",
            "available_at",
            "lease_until",
            "last_error_code",
            "updated_at",
        ]
    )


@transaction.atomic
def _mark_failed(claim: ClaimedOutbox, error_code: str) -> None:
    row = (
        Outbox.objects.select_for_update()
        .filter(pk=claim.id, state="leased", lease_until=claim.lease_until)
        .first()
    )
    if row is None:
        return
    delay_seconds = min(
        int(OUTBOX_RETRY_MAX_DELAY.total_seconds()),
        2 ** min(claim.attempt_count, 8),
    )
    row.state = "failed"
    row.available_at = timezone.now() + timedelta(seconds=delay_seconds)
    row.lease_until = None
    row.last_error_code = error_code
    row.save(
        update_fields=[
            "state",
            "available_at",
            "lease_until",
            "last_error_code",
            "updated_at",
        ]
    )


def _task_route(claim: ClaimedOutbox) -> tuple[str, str] | None:
    if claim.event_type == "turn_dispatch":
        state = Turn.objects.filter(pk=claim.target_id).values_list("state", flat=True).get()
        return ("adviser_v2.process_adviser_turn", "conversation") if state == "queued" else None
    if claim.event_type == "document_processing":
        state = (
            ProcessingJob.objects.filter(pk=claim.target_id).values_list("state", flat=True).get()
        )
        return ("adviser_v2.process_document_job", "documents") if state == "queued" else None
    if claim.event_type == "knowledge_publication":
        return None
    raise ValueError(f"Unsupported outbox event type: {claim.event_type}")


def _deliver_claim(claim: ClaimedOutbox) -> None:
    try:
        route = _task_route(claim)
        if route is not None:
            task_name, queue = route
            current_app.send_task(task_name, args=[str(claim.target_id)], queue=queue)
    except Exception:
        logger.exception("Could not deliver v2 outbox record %s", claim.id)
        _mark_failed(claim, "broker_dispatch_failed")
    else:
        _mark_delivered(claim)


def dispatch_outbox_record(outbox_id: uuid.UUID) -> bool:
    """Attempt one eligible record; return whether this caller claimed it."""

    claim = _claim_next(outbox_id=outbox_id)
    if claim is None:
        return False
    _deliver_claim(claim)
    return True


def dispatch_pending_outbox(*, limit: int = 100) -> int:
    if limit < 1 or limit > 1_000:
        raise ValueError("Outbox dispatch limit must be between 1 and 1,000.")
    attempted = 0
    for _index in range(limit):
        claim = _claim_next()
        if claim is None:
            break
        _deliver_claim(claim)
        attempted += 1
    return attempted


def dispatch_turn_outbox(turn_id: uuid.UUID) -> bool:
    outbox_id = (
        Outbox.objects.filter(event_type="turn_dispatch", turn_id=turn_id)
        .values_list("id", flat=True)
        .first()
    )
    return dispatch_outbox_record(outbox_id) if outbox_id is not None else False


def dispatch_processing_outbox(job_id: uuid.UUID) -> bool:
    outbox_id = (
        Outbox.objects.filter(event_type="document_processing", processing_job_id=job_id)
        .values_list("id", flat=True)
        .first()
    )
    return dispatch_outbox_record(outbox_id) if outbox_id is not None else False


def _set_expired_lease_recovery() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('coverguide.recover_expired_lease', 'true', true)")


@transaction.atomic
def _recover_expired_turns(limit: int) -> int:
    now = timezone.now()
    turns = list(
        Turn.objects.select_for_update(skip_locked=True)
        .filter(state__in=["running", "cancel_requested"], lease_until__lte=now)
        .order_by("lease_until", "id")[:limit]
    )
    if not turns:
        return 0
    _set_expired_lease_recovery()
    for turn in turns:
        was_cancel_requested = turn.state == "cancel_requested"
        turn.state = "cancelled" if was_cancel_requested else "failed"
        turn.error_code = None if was_cancel_requested else "worker_lease_expired"
        if was_cancel_requested and turn.cancelled_at is None:
            turn.cancelled_at = now
        turn.lease_token = None
        turn.lease_until = None
        turn.save(
            update_fields=[
                "state",
                "error_code",
                "lease_token",
                "lease_until",
                "cancelled_at",
                "updated_at",
            ]
        )
        if was_cancel_requested:
            append_turn_event(turn, "cancelled", {"schema_version": 1, "kind": "cancelled"})
        else:
            append_turn_event(
                turn,
                "failed",
                {
                    "schema_version": 1,
                    "kind": "failed",
                    "error_code": "worker_lease_expired",
                },
            )
        Outbox.objects.filter(turn=turn, event_type="turn_dispatch").update(
            state="delivered",
            lease_until=None,
            last_error_code=None,
        )
    return len(turns)


@transaction.atomic
def _recover_expired_processing_jobs(limit: int) -> int:
    now = timezone.now()
    jobs = list(
        ProcessingJob.objects.select_for_update(skip_locked=True)
        .filter(state="running", lease_until__lte=now)
        .order_by("lease_until", "id")[:limit]
    )
    if not jobs:
        return 0
    _set_expired_lease_recovery()
    for job in jobs:
        job.state = "queued"
        job.lease_token = None
        job.lease_until = None
        job.save(update_fields=["state", "lease_token", "lease_until", "updated_at"])
        Outbox.objects.filter(processing_job=job, event_type="document_processing").update(
            state="pending",
            available_at=now,
            lease_until=None,
            last_error_code=None,
        )
        AuditEvent.objects.create(
            owner_id=job.owner_id,
            operation="processing_lease_recovered",
            object_kind="processing_job",
            object_id=job.id,
            outcome="succeeded",
            metadata={
                "error_code": "processing_lease_expired",
                "affected_count": 1,
                "authorization_basis_code": "expired_database_worker_fence",
            },
        )
    return len(jobs)


def recover_expired_work(*, limit: int = 100) -> dict[str, int]:
    """Fail expired customer turns and safely requeue deterministic document work."""

    if limit < 1 or limit > 1_000:
        raise ValueError("Lease recovery limit must be between 1 and 1,000.")
    turn_count = _recover_expired_turns(limit)
    processing_count = _recover_expired_processing_jobs(limit)
    return {"turns": turn_count, "processing_jobs": processing_count}
