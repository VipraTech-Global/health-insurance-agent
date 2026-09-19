"""Celery entry points for independently scalable v2 worker queues."""

from __future__ import annotations

import uuid

from celery import shared_task

from .engine import process_turn


@shared_task(  # type: ignore[misc]
    ignore_result=True, name="adviser_v2.process_adviser_turn", queue="conversation"
)
def process_adviser_turn(turn_id: str) -> None:
    process_turn(uuid.UUID(turn_id))


@shared_task(  # type: ignore[misc]
    ignore_result=True, name="adviser_v2.process_document_job", queue="documents"
)
def process_document_job(job_id: str) -> None:
    from .pipeline import process_job

    process_job(uuid.UUID(job_id))


@shared_task(  # type: ignore[misc]
    ignore_result=True, name="adviser_v2.dispatch_outbox", queue="conversation"
)
def dispatch_outbox() -> None:
    from .services.outbox import dispatch_pending_outbox

    dispatch_pending_outbox()


@shared_task(  # type: ignore[misc]
    ignore_result=True, name="adviser_v2.recover_expired_work", queue="conversation"
)
def recover_expired_work() -> None:
    from .services.outbox import recover_expired_work as recover

    recover()
