"""Conflict-checked append-only customer-profile corrections."""

from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from ..contracts import validate_contract
from ..crypto import commitment
from ..models import (
    Conversation,
    CustomerFact,
    CustomerProfileRevision,
    CustomerRequirement,
    CustomerStatement,
    Message,
    Person,
)
from ..registries import validate_fact_type, validate_requirement_type
from .customer import ConflictError

FACT_STATUSES = {"reported", "confirmed", "disputed", "retracted"}
REQUIREMENT_OPERATORS = {
    "equals",
    "not_equals",
    "less_than_or_equal",
    "greater_than_or_equal",
    "includes",
    "excludes",
    "is_available",
    "is_not_available",
    "minimize",
    "maximize",
}
REQUIREMENT_PRIORITIES = {"mandatory", "preferred", "informational"}
REQUIREMENT_SCOPES = {"entire_purchase", "all_intended_insured", "person"}
REQUIREMENT_STATUSES = {"reported", "confirmed", "disputed", "withdrawn"}


def _choice(item: dict[str, Any], field: str, default: str, allowed: set[str]) -> str:
    value = str(item.get(field, default))
    if value not in allowed:
        raise ValueError(f"{field} must be one of: {', '.join(sorted(allowed))}.")
    return value


def _uuid(value: object, label: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a UUID.") from exc


@transaction.atomic
def correct_profile(
    owner_id: uuid.UUID,
    conversation_id: uuid.UUID,
    *,
    expected_revision: int,
    correction_text: str,
    facts: list[dict[str, Any]],
    requirements: list[dict[str, Any]],
) -> CustomerProfileRevision:
    conversation = (
        Conversation.objects.select_for_update(of=("self",))
        .select_related("current_profile_revision")
        .get(pk=conversation_id, owner_id=owner_id, status="open")
    )
    current = conversation.current_profile_revision
    if current is None or current.revision != expected_revision:
        raise ConflictError("The customer profile changed; refresh before applying corrections.")
    if not correction_text or len(correction_text) > 20_000:
        raise ValueError("correction_text must contain between 1 and 20,000 characters.")
    sequence = (
        Message.objects.filter(conversation=conversation).aggregate(value=Max("sequence"))["value"]
        or 0
    ) + 1
    message = Message.objects.create(
        owner_id=owner_id,
        conversation=conversation,
        sequence=sequence,
        role="customer",
        content=correction_text,
        origin="text",
        payload_commitment=commitment(
            {
                "correction_text": correction_text,
                "facts": facts,
                "requirements": requirements,
            }
        ),
        submitted_at=timezone.now(),
    )
    statement = CustomerStatement.objects.create(
        owner_id=owner_id,
        source_message=message,
        start_offset=0,
        end_offset=len(correction_text),
        kind="correction",
        status="mapped",
    )
    revision = CustomerProfileRevision.objects.create(
        owner_id=owner_id,
        conversation=conversation,
        revision=current.revision + 1,
    )
    for item in facts:
        fact_type = str(item.get("fact_type", ""))
        value = validate_contract("FactValueV1", item.get("value"))
        validate_fact_type(fact_type, value)
        status = _choice(item, "status", "confirmed", FACT_STATUSES)
        subject_id = item.get("subject_person_id")
        if subject_id is not None:
            Person.objects.get(pk=_uuid(subject_id, "subject_person_id"), owner_id=owner_id)
        logical_key = (
            _uuid(item["logical_key"], "logical_key") if item.get("logical_key") else uuid.uuid4()
        )
        prior = (
            CustomerFact.objects.filter(owner_id=owner_id, logical_key=logical_key)
            .order_by("-introduced_in_revision__revision")
            .first()
        )
        if prior is not None and prior.fact_type != fact_type:
            raise ConflictError("A fact correction cannot change its registered fact type.")
        fact_statement = statement
        if subject_id is not None:
            fact_statement = CustomerStatement.objects.create(
                owner_id=owner_id,
                source_message=message,
                start_offset=0,
                end_offset=len(correction_text),
                subject_person_id=subject_id,
                kind="correction",
                status="mapped",
            )
        CustomerFact.objects.create(
            owner_id=owner_id,
            introduced_in_revision=revision,
            source_statement=fact_statement,
            logical_key=logical_key,
            fact_type=fact_type,
            schema_version=1,
            value=value,
            status=status,
        )
    for item in requirements:
        criterion = str(item.get("criterion", ""))
        target = item.get("target_value")
        if target is not None:
            target = validate_contract("FactValueV1", target)
        validate_requirement_type(criterion, target)
        operator = _choice(item, "operator", "equals", REQUIREMENT_OPERATORS)
        priority = _choice(item, "priority", "preferred", REQUIREMENT_PRIORITIES)
        scope = _choice(item, "scope", "entire_purchase", REQUIREMENT_SCOPES)
        status = _choice(item, "status", "confirmed", REQUIREMENT_STATUSES)
        logical_key = (
            _uuid(item["logical_key"], "logical_key") if item.get("logical_key") else uuid.uuid4()
        )
        prior_requirement = (
            CustomerRequirement.objects.filter(owner_id=owner_id, logical_key=logical_key)
            .order_by("-introduced_in_revision__revision")
            .first()
        )
        if prior_requirement is not None and prior_requirement.criterion != criterion:
            raise ConflictError("A requirement correction cannot change its registered criterion.")
        subject_id = item.get("subject_person_id")
        if subject_id is not None:
            Person.objects.get(pk=_uuid(subject_id, "subject_person_id"), owner_id=owner_id)
        CustomerRequirement.objects.create(
            owner_id=owner_id,
            introduced_in_revision=revision,
            source_statement=statement,
            logical_key=logical_key,
            criterion=criterion,
            operator=operator,
            target_value=target,
            priority=priority,
            scope=scope,
            subject_person_id=subject_id,
            status=status,
        )
    conversation.current_profile_revision = revision
    conversation.save(update_fields=["current_profile_revision", "updated_at"])
    return revision
