"""Validation and durable application of CustomerInterpretationV1."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from django.db import transaction

from apps.accounts.models import User

from ..contracts import validate_contract
from ..errors import AccountErased, PinnedStateChanged
from ..models import (
    AdviceRequest,
    Conversation,
    CustomerFact,
    CustomerProfileRevision,
    CustomerRequirement,
    CustomerStatement,
    KnowledgeChannel,
    Message,
    Person,
    PersonRelationship,
)
from ..registries import (
    FACT_TYPES,
    REQUIREMENT_TYPES,
    validate_fact_type,
    validate_requirement_type,
)
from ..schemas import (
    CustomerInterpretationV1,
    InterpretedFact,
    InterpretedRequirement,
    InterpretedStatement,
)


@dataclass(frozen=True)
class AppliedInterpretation:
    profile_revision: CustomerProfileRevision
    advice_request: AdviceRequest
    statements: list[CustomerStatement]


def normalize_purchase_fact_scopes(value: CustomerInterpretationV1) -> None:
    """Keep registered purchase facts at purchase scope when a model names a person."""

    for fact in value.facts:
        assertion = FACT_TYPES.get(fact.fact_type)
        if assertion is not None and not assertion.person_scoped:
            fact.subject_key = None


_MONEY_PER_YEAR_CRITERIA = {"budget"}
_MONEY_CRITERIA = {"sum_insured"}


def _canonicalize_money_unit(quantity: dict[str, object], unit: str) -> None:
    if quantity.get("state") == "known" and quantity.get("kind") == "quantity":
        quantity["unit"] = unit
        quantity.setdefault("currency", "INR")


def normalize_money_quantity_units(value: CustomerInterpretationV1) -> None:
    """Canonicalize free-form currency units (e.g. 'INR per year') into the rule
    engine's fixed unit vocabulary, so budget/sum_insured requirements can actually
    be matched against authored PolicyRule amounts."""

    for fact in value.facts:
        if fact.fact_type in _MONEY_PER_YEAR_CRITERIA:
            _canonicalize_money_unit(fact.value, "money_per_year")
        elif fact.fact_type in _MONEY_CRITERIA:
            _canonicalize_money_unit(fact.value, "money")
    for requirement in value.requirements:
        if requirement.target_value is None:
            continue
        if requirement.criterion in _MONEY_PER_YEAR_CRITERIA:
            _canonicalize_money_unit(requirement.target_value, "money_per_year")
        elif requirement.criterion in _MONEY_CRITERIA:
            _canonicalize_money_unit(requirement.target_value, "money")


def normalize_first_turn_references(
    value: CustomerInterpretationV1, *, starting_revision: int
) -> None:
    """A new conversation has no prior person or customer assertion to reference."""

    if starting_revision == 1:
        value.corrections.clear()
        for subject in value.subjects:
            subject.person_id = None


def normalize_self_insured_fact(
    source_text: str, value: CustomerInterpretationV1
) -> None:
    """Treat an explicit self-cover statement as the registered boolean fact."""

    if not re.search(r"\b(?:for myself|for self|covering myself)\b", source_text, re.I):
        return
    self_keys = {subject.key for subject in value.subjects if subject.relationship == "self"}
    for fact in value.facts:
        if (
            fact.fact_type == "intended_insured"
            and fact.subject_key in self_keys
            and fact.value.get("kind") == "text"
            and str(fact.value.get("value", "")).casefold() in {"self", "myself"}
        ):
            fact.value = {"state": "known", "kind": "boolean", "value": True}


_EXPLICIT_CITY = re.compile(
    r"\b(?:am|live|reside|based|parent)\b[^.!?]{0,55}\bin\s+"
    r"(?P<city>Bengaluru|Bangalore|Chennai|Delhi|Hyderabad|Kolkata|Mumbai|Pune)\b",
    re.I,
)


def recover_explicit_city(source_text: str, value: CustomerInterpretationV1) -> None:
    """Keep a single literally named customer city if interpretation omitted it."""

    if any(fact.fact_type == "city" for fact in value.facts):
        return
    matches = list(_EXPLICIT_CITY.finditer(source_text))
    named = {match.group("city").casefold() for match in matches}
    if len(named) != 1 or not matches:
        return
    match = matches[0]
    statement_index = next(
        (
            index for index, statement in enumerate(value.statements)
            if statement.start_offset <= match.start()
            and statement.end_offset >= match.end()
            and not statement.ambiguous
        ),
        None,
    )
    if statement_index is None:
        value.statements.append(InterpretedStatement(
            start_offset=match.start(), end_offset=match.end(), subject_key=None,
            kind="fact", ambiguous=False, ambiguity_reason=None,
        ))
        statement_index = len(value.statements) - 1
    city = "Bengaluru" if match.group("city").casefold() == "bangalore" else match.group("city").title()
    value.facts.append(InterpretedFact(
        statement_index=statement_index, subject_key=None, fact_type="city",
        value={"state": "known", "kind": "text", "value": city},
        confidence="explicit",
    ))


_CHILD_AGE = re.compile(
    r"\b(?P<amount>\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten)"
    r"[ -]*(?P<unit>day|year)s?[ -]*old\b(?=.{0,18}\b(?:baby|child|son|daughter)\b)",
    re.IGNORECASE,
)
_AGE_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def recover_explicit_child_age(source_text: str, value: CustomerInterpretationV1) -> None:
    """Recover an exact child age omitted by interpretation when only one child is named."""

    child_keys = [subject.key for subject in value.subjects if subject.relationship == "child"]
    if len(child_keys) != 1:
        return
    child_key = child_keys[0]
    if any(fact.fact_type == "age" and fact.subject_key == child_key for fact in value.facts):
        return
    matches = list(_CHILD_AGE.finditer(source_text))
    if len(matches) != 1:
        return
    match = matches[0]
    statement_index = next(
        (
            index
            for index, statement in enumerate(value.statements)
            if statement.start_offset <= match.start() and statement.end_offset >= match.end()
        ),
        None,
    )
    if statement_index is None or value.statements[statement_index].ambiguous:
        return
    raw = match.group("amount").lower()
    amount = int(raw) if raw.isdigit() else _AGE_WORDS[raw]
    value.facts.append(
        InterpretedFact(
            statement_index=statement_index,
            subject_key=child_key,
            fact_type="age",
            value={
                "state": "known",
                "kind": "quantity",
                "value": str(amount),
                "unit": match.group("unit").lower(),
            },
            confidence="explicit",
        )
    )


_POLICY_TERM = re.compile(
    r"\b(?P<years>\d+|one|two|three|four|five)[ -]year policy term\b",
    re.IGNORECASE,
)


def recover_explicit_policy_term(source_text: str, value: CustomerInterpretationV1) -> None:
    """Retain an exact policy term when interpretation omits the stated requirement."""

    if any(item.criterion == "policy_tenure_selection" for item in value.requirements):
        return
    matches = list(_POLICY_TERM.finditer(source_text))
    if len(matches) != 1:
        return
    match = matches[0]
    statement_index = next(
        (
            index
            for index, statement in enumerate(value.statements)
            if statement.start_offset <= match.start() and statement.end_offset >= match.end()
        ),
        None,
    )
    if statement_index is None:
        return
    raw = match.group("years").lower()
    years = int(raw) if raw.isdigit() else _AGE_WORDS.get(raw)
    if years is None:
        return
    value.requirements.append(
        InterpretedRequirement(
            statement_index=statement_index,
            subject_key=None,
            criterion="policy_tenure_selection",
            operator="equals",
            target_value={
                "state": "known",
                "kind": "quantity",
                "value": str(years),
                "unit": "year",
            },
            priority="mandatory" if re.search(r"\b(mandatory|required|must)\b", source_text, re.I) else "preferred",
            scope="entire_purchase",
        )
    )


def suppress_catalogue_clarification(source_text: str, value: CustomerInterpretationV1) -> None:
    """The live release already defines the reviewed products for comparison."""

    question = value.clarification_question or ""
    if (
        value.ambiguity
        and re.search(r"\b(?:three|3) reviewed products\b", source_text, re.I)
        and re.search(r"product|policy|plan", question, re.I)
        and re.search(r"name|which|details|document", question, re.I)
    ):
        value.ambiguity = False
        value.clarification_question = None
        for statement in value.statements:
            excerpt = source_text[statement.start_offset : statement.end_offset]
            if statement.ambiguous and re.search(r"product|policy|plan", excerpt, re.I):
                statement.ambiguous = False
                statement.ambiguity_reason = None


def normalize_requested_sum_insured_priority(
    source_text: str, value: CustomerInterpretationV1
) -> None:
    """A requested configuration is not a hard availability claim absent explicit wording."""

    explicitly_hard = re.search(
        r"\b(?:mandatory|required|must|only)\b[^.!?]{0,32}₹\s*\d"
        r"|₹\s*[\d,.]+[^.!?]{0,32}\b(?:mandatory|required|must|only)\b",
        source_text,
        re.I,
    )
    if explicitly_hard:
        return
    for requirement in value.requirements:
        if requirement.criterion == "sum_insured" and requirement.priority == "mandatory":
            requirement.priority = "preferred"


def normalize_explicit_restoration_scenario(
    source_text: str, value: CustomerInterpretationV1
) -> None:
    """Keep the exact second-hospitalization request typed as a boolean benefit."""

    text = source_text.casefold()
    if not all(
        phrase in text
        for phrase in (
            "sum insured becomes available again",
            "second hospitalization",
            "same policy year",
            "first paid hospitalization claim",
            "base cover",
        )
    ):
        return
    for requirement in value.requirements:
        if requirement.criterion == "restoration" and requirement.operator == "equals":
            requirement.target_value = {"state": "known", "kind": "boolean", "value": True}


_ROOM_ILLUSTRATION_AMOUNTS = {
    "eligible_room_rent_limit": re.compile(r"eligible room rent\s*(?:is|of|:)\s*₹\s*([\d,]+)(?:\s*(lakh|lakhs))?", re.I),
    "room_rent_actually_incurred": re.compile(r"actual room rent\s*(?:is|of|:)\s*₹\s*([\d,]+)(?:\s*(lakh|lakhs))?", re.I),
    "total_associated_medical_expenses": re.compile(r"associated medical expenses\s*(?:are|is|of|:)\s*₹\s*([\d,]+)(?:\s*(lakh|lakhs))?", re.I),
}
_HIGHER_ROOM = re.compile(r"(?:higher room category|room category above the eligible|above the eligible category)", re.I)


def recover_explicit_room_illustration(source_text: str, value: CustomerInterpretationV1) -> None:
    """Record exact stipulated claim inputs without inferring a purchase preference."""

    matches = {key: list(pattern.finditer(source_text)) for key, pattern in _ROOM_ILLUSTRATION_AMOUNTS.items()}
    higher = list(_HIGHER_ROOM.finditer(source_text))
    if any(len(found) != 1 for found in matches.values()) or len(higher) != 1:
        return

    def statement_for(match: re.Match[str]) -> int:
        for index, statement in enumerate(value.statements):
            if statement.start_offset <= match.start() and statement.end_offset >= match.end() and not statement.ambiguous:
                return index
        value.statements.append(InterpretedStatement(
            start_offset=match.start(), end_offset=match.end(), subject_key=None,
            kind="fact", ambiguous=False, ambiguity_reason=None,
        ))
        return len(value.statements) - 1

    for key, found in matches.items():
        match = found[0]
        rupees = int(match.group(1).replace(",", "")) * (100000 if match.group(2) else 1)
        fact = next((item for item in value.facts if item.fact_type == key), None)
        payload: dict[str, object] = {
            "state": "known",
            "kind": "quantity",
            "value": str(rupees),
            "unit": "INR",
        }
        if fact is None:
            value.facts.append(InterpretedFact(
                statement_index=statement_for(match), subject_key=None,
                fact_type=key, value=payload, confidence="explicit",
            ))
        elif fact.value.get("state") != "known":
            fact.value = payload
            fact.subject_key = None
            fact.statement_index = statement_for(match)
            fact.confidence = "explicit"
    if not any(item.fact_type == "actual_room_category_higher_than_eligible" for item in value.facts):
        value.facts.append(InterpretedFact(
            statement_index=statement_for(higher[0]), subject_key=None,
            fact_type="actual_room_category_higher_than_eligible",
            value={"state": "known", "kind": "boolean", "value": True},
            confidence="explicit",
        ))


def validate_interpretation(source_text: str, value: CustomerInterpretationV1) -> None:
    for statement in value.statements:
        if statement.end_offset > len(source_text):
            raise ValueError("A statement offset falls outside the exact customer message.")
        if not source_text[statement.start_offset : statement.end_offset].strip():
            raise ValueError("A statement cannot reference only whitespace.")
    for fact in value.facts:
        normalized = validate_contract("FactValueV1", fact.value)
        validate_fact_type(fact.fact_type, normalized)
        if FACT_TYPES[fact.fact_type].person_scoped != (fact.subject_key is not None):
            scope = "a person" if FACT_TYPES[fact.fact_type].person_scoped else "the purchase"
            raise ValueError(f"{fact.fact_type} must be scoped to {scope}.")
    for requirement in value.requirements:
        normalized = (
            validate_contract("FactValueV1", requirement.target_value)
            if requirement.target_value is not None
            else None
        )
        validate_requirement_type(requirement.criterion, normalized)
        requires_person = REQUIREMENT_TYPES[requirement.criterion].person_scoped
        if requires_person and requirement.scope != "person":
            raise ValueError(f"{requirement.criterion} must use person scope.")
        if (requirement.scope == "person") != (requirement.subject_key is not None):
            raise ValueError("A person-scoped requirement requires exactly one subject person.")


def _existing_person(owner_id: uuid.UUID, person_id: str | None) -> Person | None:
    if not person_id:
        return None
    try:
        parsed = uuid.UUID(person_id)
    except ValueError as exc:
        raise ValueError("An interpreted person_id is not a UUID.") from exc
    return Person.objects.get(pk=parsed, owner_id=owner_id)


@transaction.atomic
def apply_interpretation(
    turn_message: Message,
    interpretation: CustomerInterpretationV1,
    *,
    expected_profile_revision_id: uuid.UUID | None,
    expected_release_id: uuid.UUID | None,
    expected_channel_generation: int,
    expected_erasure_generation: int,
) -> AppliedInterpretation:
    normalize_purchase_fact_scopes(interpretation)
    validate_interpretation(turn_message.content, interpretation)
    owner_id = turn_message.owner_id
    owner = User.objects.select_for_update().get(pk=owner_id)
    if (
        owner.erasure_generation != expected_erasure_generation
        or owner.deleted_at is not None
        or not owner.is_active
    ):
        raise AccountErased("account_erased")
    channel = (
        KnowledgeChannel.objects.select_for_update(of=("self",))
        .select_related("current_release")
        .get(name="live")
    )
    conversation = (
        Conversation.objects.select_for_update(of=("self",))
        .select_related("current_profile_revision")
        .get(pk=turn_message.conversation_id, owner_id=owner_id)
    )
    if (
        conversation.current_profile_revision_id != expected_profile_revision_id
        or channel.current_release_id != expected_release_id
        or channel.generation != expected_channel_generation
    ):
        raise PinnedStateChanged("pinned_state_changed")
    current = conversation.current_profile_revision
    next_revision = (current.revision if current else 0) + 1
    revision = CustomerProfileRevision.objects.create(
        owner_id=owner_id,
        conversation=conversation,
        revision=next_revision,
    )
    people: dict[str, Person] = {}
    for subject in interpretation.subjects:
        person = _existing_person(owner_id, subject.person_id)
        if person is None:
            person = Person.objects.create(
                owner_id=owner_id,
                display_name=subject.display_name or subject.relationship.replace("_", " ").title(),
            )
        people[subject.key] = person
    statements: list[CustomerStatement] = []
    for source in interpretation.statements:
        statement = CustomerStatement.objects.create(
            owner_id=owner_id,
            source_message=turn_message,
            start_offset=source.start_offset,
            end_offset=source.end_offset,
            subject_person=people.get(source.subject_key or ""),
            kind=source.kind,
            status="clarification_required" if source.ambiguous else "mapped",
            resolution_note=source.ambiguity_reason,
        )
        statements.append(statement)
    if not statements:
        statements.append(
            CustomerStatement.objects.create(
                owner_id=owner_id,
                source_message=turn_message,
                start_offset=0,
                end_offset=len(turn_message.content),
                kind="context",
                status="mapped",
            )
        )
    self_subject = next(
        (subject for subject in interpretation.subjects if subject.relationship == "self"), None
    )
    self_person = people.get(self_subject.key) if self_subject else None
    relationship_statement = statements[0]
    if self_person:
        for subject in interpretation.subjects:
            other = people[subject.key]
            if other.id == self_person.id or subject.relationship == "self":
                continue
            relationship = PersonRelationship.objects.filter(
                owner_id=owner_id,
                from_person=self_person,
                to_person=other,
                relationship_type=subject.relationship,
                valid_from=None,
                valid_to=None,
            ).first()
            if relationship is None:
                PersonRelationship.objects.create(
                    owner_id=owner_id,
                    from_person=self_person,
                    to_person=other,
                    relationship_type=subject.relationship,
                    source_statement=relationship_statement,
                )
    for fact in interpretation.facts:
        source = interpretation.statements[fact.statement_index]
        if source.ambiguous or fact.confidence == "uncertain":
            continue
        statement = statements[fact.statement_index]
        person = people.get(fact.subject_key or "")
        if statement.subject_person_id != (person.id if person else None):
            source = interpretation.statements[fact.statement_index]
            statement = CustomerStatement.objects.create(
                owner_id=owner_id,
                source_message=turn_message,
                start_offset=source.start_offset,
                end_offset=source.end_offset,
                subject_person=person,
                kind="fact",
                status="mapped",
            )
            statements.append(statement)
        prior = (
            CustomerFact.objects.filter(
                owner_id=owner_id,
                fact_type=fact.fact_type,
                source_statement__subject_person=person,
                introduced_in_revision__conversation=conversation,
            )
            .order_by("-introduced_in_revision__revision")
            .first()
        )
        CustomerFact.objects.create(
            owner_id=owner_id,
            introduced_in_revision=revision,
            source_statement=statement,
            logical_key=prior.logical_key if prior else uuid.uuid4(),
            fact_type=fact.fact_type,
            schema_version=1,
            value=validate_contract("FactValueV1", fact.value),
            status="reported",
        )
    explicit_intended_subjects = {
        people[fact.subject_key].id
        for fact in interpretation.facts
        if fact.fact_type == "intended_insured"
        and fact.subject_key is not None
        and fact.subject_key in people
    }
    for statement_index, source in enumerate(interpretation.statements):
        statement = statements[statement_index]
        person = statement.subject_person
        if (
            source.kind != "intended_insured"
            or source.ambiguous
            or person is None
            or person.id in explicit_intended_subjects
            or any(
                fact.statement_index == statement_index
                and fact.fact_type == "intended_insured"
                and fact.subject_key != source.subject_key
                for fact in interpretation.facts
            )
        ):
            continue
        prior = (
            CustomerFact.objects.filter(
                owner_id=owner_id,
                fact_type="intended_insured",
                source_statement__subject_person=person,
                introduced_in_revision__conversation=conversation,
            )
            .order_by("-introduced_in_revision__revision")
            .first()
        )
        intended_value = {"state": "known", "kind": "boolean", "value": True}
        if (
            prior is not None
            and prior.status in {"reported", "confirmed"}
            and prior.value == intended_value
        ):
            continue
        CustomerFact.objects.create(
            owner_id=owner_id,
            introduced_in_revision=revision,
            source_statement=statement,
            logical_key=prior.logical_key if prior else uuid.uuid4(),
            fact_type="intended_insured",
            schema_version=1,
            value=intended_value,
            status="reported",
        )
    for requirement in interpretation.requirements:
        source = interpretation.statements[requirement.statement_index]
        if source.ambiguous:
            continue
        statement = statements[requirement.statement_index]
        person = people.get(requirement.subject_key or "")
        prior_requirement = (
            CustomerRequirement.objects.filter(
                owner_id=owner_id,
                criterion=requirement.criterion,
                subject_person=person,
                introduced_in_revision__conversation=conversation,
            )
            .order_by("-introduced_in_revision__revision")
            .first()
        )
        CustomerRequirement.objects.create(
            owner_id=owner_id,
            introduced_in_revision=revision,
            source_statement=statement,
            logical_key=prior_requirement.logical_key if prior_requirement else uuid.uuid4(),
            criterion=requirement.criterion,
            operator=requirement.operator,
            target_value=(
                validate_contract("FactValueV1", requirement.target_value)
                if requirement.target_value is not None
                else None
            ),
            priority=requirement.priority,
            scope=requirement.scope,
            subject_person=person,
            status="reported",
        )
    for correction in interpretation.corrections:
        try:
            logical_key = uuid.UUID(correction.logical_key)
        except ValueError as exc:
            raise ValueError("A correction logical_key is not a UUID.") from exc
        statement = statements[correction.statement_index]
        if correction.assertion_kind == "fact":
            prior_fact = (
                CustomerFact.objects.filter(owner_id=owner_id, logical_key=logical_key)
                .order_by("-introduced_in_revision__revision")
                .first()
            )
            if prior_fact is None:
                raise ValueError("A correction references an unknown customer fact.")
            if correction.replacement_status == "withdrawn":
                raise ValueError("Facts use retracted rather than withdrawn status.")
            value = correction.replacement_value or prior_fact.value
            validate_fact_type(prior_fact.fact_type, value)
            prior_person = prior_fact.source_statement.subject_person
            if (
                statement.subject_person_id is not None
                and statement.subject_person_id != prior_fact.source_statement.subject_person_id
            ):
                raise ValueError("A fact correction cannot change its subject person.")
            fact_statement = statement
            if prior_person is not None and statement.subject_person_id is None:
                fact_statement = CustomerStatement.objects.create(
                    owner_id=owner_id,
                    source_message=turn_message,
                    start_offset=statement.start_offset,
                    end_offset=statement.end_offset,
                    subject_person=prior_person,
                    kind="correction",
                    status=statement.status,
                    resolution_note=statement.resolution_note,
                )
            CustomerFact.objects.create(
                owner_id=owner_id,
                introduced_in_revision=revision,
                source_statement=fact_statement,
                logical_key=logical_key,
                fact_type=prior_fact.fact_type,
                schema_version=1,
                value=value,
                status=correction.replacement_status,
            )
        else:
            prior_requirement = (
                CustomerRequirement.objects.filter(owner_id=owner_id, logical_key=logical_key)
                .order_by("-introduced_in_revision__revision")
                .first()
            )
            if prior_requirement is None:
                raise ValueError("A correction references an unknown customer requirement.")
            if correction.replacement_status == "retracted":
                raise ValueError("Requirements use withdrawn rather than retracted status.")
            value = correction.replacement_value or prior_requirement.target_value
            validate_requirement_type(prior_requirement.criterion, value)
            CustomerRequirement.objects.create(
                owner_id=owner_id,
                introduced_in_revision=revision,
                source_statement=statement,
                logical_key=logical_key,
                criterion=prior_requirement.criterion,
                operator=prior_requirement.operator,
                target_value=value,
                priority=prior_requirement.priority,
                scope=prior_requirement.scope,
                subject_person=prior_requirement.subject_person,
                status=correction.replacement_status,
            )
    request_type = (
        interpretation.intent if interpretation.intent != "conversation" else "coverage_question"
    )
    advice_request = AdviceRequest.objects.create(
        owner_id=owner_id,
        conversation=conversation,
        source_statement=statements[0],
        request_type=request_type,
    )
    conversation.current_profile_revision = revision
    conversation.save(update_fields=["current_profile_revision", "updated_at"])
    return AppliedInterpretation(revision, advice_request, statements)
