"""Owner-scoped customer and conversation queries."""

from __future__ import annotations

import uuid
from typing import Any

from django.db.models import QuerySet

from ..models import (
    Conversation,
    CustomerFact,
    CustomerProfileRevision,
    CustomerRequirement,
    CustomerStatement,
    Message,
    Person,
    Turn,
    TurnEvent,
)


def conversations_for(owner_id: uuid.UUID) -> QuerySet[Conversation]:
    return Conversation.objects.filter(owner_id=owner_id).order_by("-updated_at", "-created_at")


def messages_for(owner_id: uuid.UUID, conversation_id: uuid.UUID) -> QuerySet[Message]:
    return Message.objects.filter(owner_id=owner_id, conversation_id=conversation_id).order_by(
        "sequence"
    )


def turn_for(owner_id: uuid.UUID, turn_id: uuid.UUID) -> Turn:
    return Turn.objects.get(owner_id=owner_id, pk=turn_id)


def events_after(
    owner_id: uuid.UUID, turn_id: uuid.UUID, after_sequence: int
) -> QuerySet[TurnEvent]:
    return TurnEvent.objects.filter(
        owner_id=owner_id, turn_id=turn_id, sequence__gt=after_sequence
    ).order_by("sequence")


def current_profile_payload(owner_id: uuid.UUID, conversation_id: uuid.UUID) -> dict[str, Any]:
    conversation = Conversation.objects.select_related("current_profile_revision").get(
        pk=conversation_id, owner_id=owner_id
    )
    revision = conversation.current_profile_revision
    if revision is None:
        raise CustomerProfileRevision.DoesNotExist
    facts = _current_assertions(
        CustomerFact.objects.filter(
            owner_id=owner_id,
            introduced_in_revision__conversation_id=conversation_id,
            introduced_in_revision__revision__lte=revision.revision,
        ).select_related("source_statement", "source_statement__subject_person"),
        "logical_key",
    )
    requirements = _current_assertions(
        CustomerRequirement.objects.filter(
            owner_id=owner_id,
            introduced_in_revision__conversation_id=conversation_id,
            introduced_in_revision__revision__lte=revision.revision,
        ).select_related("source_statement", "subject_person"),
        "logical_key",
    )
    subject_ids = CustomerStatement.objects.filter(
        owner_id=owner_id,
        source_message__conversation_id=conversation_id,
        subject_person_id__isnull=False,
    ).values("subject_person_id")
    people = Person.objects.filter(owner_id=owner_id, id__in=subject_ids)
    return {
        "id": str(revision.id),
        "revision": revision.revision,
        "created_at": revision.created_at,
        "people": [
            {"id": str(person.id), "display_name": person.display_name} for person in people
        ],
        "facts": [
            {
                "id": str(item.id),
                "logical_key": str(item.logical_key),
                "fact_type": item.fact_type,
                "value": item.value,
                "status": item.status,
                "subject_person_id": (
                    str(item.source_statement.subject_person_id)
                    if item.source_statement.subject_person_id
                    else None
                ),
            }
            for item in facts
            if item.status != "retracted"
        ],
        "requirements": [
            {
                "id": str(item.id),
                "logical_key": str(item.logical_key),
                "criterion": item.criterion,
                "operator": item.operator,
                "target_value": item.target_value,
                "priority": item.priority,
                "scope": item.scope,
                "status": item.status,
                "subject_person_id": (
                    str(item.subject_person_id) if item.subject_person_id else None
                ),
            }
            for item in requirements
            if item.status != "withdrawn"
        ],
    }


def _current_assertions(queryset: QuerySet[Any], key: str) -> list[Any]:
    latest: dict[object, Any] = {}
    for item in queryset.order_by("introduced_in_revision__revision", "created_at"):
        latest[getattr(item, key)] = item
    return list(latest.values())
