"""Transactional customer-message and turn lifecycle operations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone

from ..crypto import commitment, commitment_matches
from ..models import (
    Conversation,
    CustomerProfileRevision,
    Message,
    Outbox,
    Turn,
    TurnEvent,
)


class ConflictError(RuntimeError):
    pass


@dataclass(frozen=True)
class SubmittedTurn:
    message: Message
    turn: Turn
    created: bool


@transaction.atomic
def create_conversation(owner_id: uuid.UUID, title: str = "Insurance planning") -> Conversation:
    conversation = Conversation.objects.create(owner_id=owner_id, title=title)
    revision = CustomerProfileRevision.objects.create(
        owner_id=owner_id, conversation=conversation, revision=1
    )
    conversation.current_profile_revision = revision
    conversation.save(update_fields=["current_profile_revision", "updated_at"])
    return conversation


@transaction.atomic
def submit_message(
    owner_id: uuid.UUID,
    conversation_id: uuid.UUID,
    *,
    request_id: uuid.UUID,
    text: str,
    expected_profile_revision: int | None,
) -> SubmittedTurn:
    if not text or len(text) > 20_000:
        raise ValueError("Message text must contain between 1 and 20,000 characters.")
    conversation = (
        Conversation.objects.select_for_update(of=("self",))
        .select_related("current_profile_revision")
        .get(pk=conversation_id, owner_id=owner_id, status="open")
    )
    request_payload = {
        "conversation_id": str(conversation_id),
        "request_id": str(request_id),
        "text": text,
        "expected_profile_revision": expected_profile_revision,
    }
    payload_commitment = commitment(request_payload)
    existing = (
        Turn.objects.filter(owner_id=owner_id, request_id=request_id)
        .select_related("input_message")
        .first()
    )
    if existing is not None:
        if not commitment_matches(existing.input_message.payload_commitment, request_payload):
            raise ConflictError("This request ID was already used with a different payload.")
        return SubmittedTurn(existing.input_message, existing, False)
    current = conversation.current_profile_revision
    if expected_profile_revision is not None and (
        current is None or current.revision != expected_profile_revision
    ):
        raise ConflictError("The customer profile changed; refresh before submitting this message.")
    sequence = (
        Message.objects.filter(conversation=conversation).aggregate(value=Max("sequence"))["value"]
        or 0
    ) + 1
    now = timezone.now()
    message = Message.objects.create(
        owner_id=owner_id,
        conversation=conversation,
        sequence=sequence,
        role="customer",
        content=text,
        origin="text",
        client_request_id=request_id,
        payload_commitment=payload_commitment,
        submitted_at=now,
    )
    turn = Turn.objects.create(
        owner_id=owner_id,
        conversation=conversation,
        request_id=request_id,
        input_message=message,
        starting_profile_revision=current,
        deadline=now + timedelta(seconds=settings.AI_TURN_TIMEOUT_SECONDS),
    )
    append_turn_event(turn, "queued", {"schema_version": 1, "kind": "queued"})
    Outbox.objects.create(
        owner_id=owner_id,
        event_type="turn_dispatch",
        turn=turn,
        idempotency_key=f"turn:{turn.id}",
    )
    return SubmittedTurn(message, turn, True)


def append_turn_event(turn: Turn, event_type: str, payload: dict[str, Any]) -> TurnEvent:
    sequence = (
        TurnEvent.objects.filter(turn=turn).aggregate(value=Max("sequence"))["value"] or 0
    ) + 1
    return TurnEvent.objects.create(
        owner_id=turn.owner_id,
        turn=turn,
        sequence=sequence,
        event_type=event_type,
        payload=payload,
    )


@transaction.atomic
def cancel_turn(owner_id: uuid.UUID, turn_id: uuid.UUID) -> Turn:
    turn = Turn.objects.select_for_update().get(pk=turn_id, owner_id=owner_id)
    if turn.state in {"completed", "failed", "stale", "cancelled"}:
        raise ConflictError("The turn is already terminal.")
    turn.state = "cancel_requested" if turn.state == "running" else "cancelled"
    turn.cancelled_at = timezone.now()
    turn.save(update_fields=["state", "cancelled_at", "updated_at"])
    if turn.state == "cancelled":
        append_turn_event(turn, "cancelled", {"schema_version": 1, "kind": "cancelled"})
    return turn


@transaction.atomic
def retry_turn(owner_id: uuid.UUID, turn_id: uuid.UUID) -> SubmittedTurn:
    prior = (
        Turn.objects.select_for_update(of=("self",))
        .select_related("input_message", "conversation__current_profile_revision")
        .get(pk=turn_id, owner_id=owner_id)
    )
    if prior.state not in {"failed", "stale", "cancelled"}:
        raise ConflictError("Only failed, stale, or cancelled turns can be retried.")
    now = timezone.now()
    turn = Turn.objects.create(
        owner_id=owner_id,
        conversation_id=prior.conversation_id,
        request_id=uuid.uuid4(),
        input_message=prior.input_message,
        starting_profile_revision=prior.conversation.current_profile_revision,
        deadline=now + timedelta(seconds=settings.AI_TURN_TIMEOUT_SECONDS),
    )
    append_turn_event(turn, "queued", {"schema_version": 1, "kind": "queued"})
    Outbox.objects.create(
        owner_id=owner_id,
        event_type="turn_dispatch",
        turn=turn,
        idempotency_key=f"turn:{turn.id}",
    )
    return SubmittedTurn(prior.input_message, turn, True)


def safely_submit_message(*args: Any, **kwargs: Any) -> SubmittedTurn:
    try:
        return submit_message(*args, **kwargs)
    except IntegrityError as exc:
        raise ConflictError(
            "A concurrent request used this identifier; retry with a fresh ID."
        ) from exc
