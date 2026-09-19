from __future__ import annotations

import uuid

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.adviser_v2.crypto import commitment
from apps.adviser_v2.engine import _interpretation_contract_guidance
from apps.adviser_v2.errors import PinnedStateChanged
from apps.adviser_v2.models import (
    AdviceRequest,
    CustomerFact,
    CustomerProfileRevision,
    CustomerStatement,
    KnowledgeChannel,
    Message,
    Person,
    PersonRelationship,
)
from apps.adviser_v2.registries import FACT_TYPES, REQUIREMENT_TYPES
from apps.adviser_v2.schemas import (
    CustomerInterpretationV1,
    InterpretedCorrection,
    InterpretedFact,
    InterpretedRequirement,
)
from apps.adviser_v2.selectors.customer import current_profile_payload
from apps.adviser_v2.services.customer import create_conversation
from apps.adviser_v2.services.interpretation import (
    apply_interpretation,
    normalize_explicit_restoration_scenario,
    normalize_first_turn_references,
    normalize_money_quantity_units,
    normalize_purchase_fact_scopes,
    normalize_requested_sum_insured_priority,
    normalize_self_insured_fact,
    recover_explicit_child_age,
    recover_explicit_city,
    recover_explicit_policy_term,
    recover_explicit_room_illustration,
    suppress_catalogue_clarification,
    validate_interpretation,
)


def _message(owner_id: uuid.UUID, conversation_id: uuid.UUID, sequence: int, text: str) -> Message:
    return Message.objects.create(
        owner_id=owner_id,
        conversation_id=conversation_id,
        sequence=sequence,
        role="customer",
        content=text,
        origin="text",
        payload_commitment=commitment(text),
        submitted_at=timezone.now(),
    )


def test_interpretation_prompt_exposes_the_closed_customer_registries() -> None:
    guidance = _interpretation_contract_guidance()

    assert all(key in guidance for key in FACT_TYPES)
    assert all(key in guidance for key in REQUIREMENT_TYPES)
    assert '"state":"known","kind":"quantity"' in guidance
    assert "Do not encode comparison count, citations, evidence, output format" in guidance
    assert "Person-scoped fact types" in guidance
    assert "Purchase-scoped fact types" in guidance
    assert "subject_key null" in guidance
    assert "medical_history_disclosed" in guidance
    assert "Never record it as false" in guidance


def _family_interpretation(
    text: str,
    *,
    self_id: uuid.UUID | None = None,
    parent_id: uuid.UUID | None = None,
) -> CustomerInterpretationV1:
    return CustomerInterpretationV1.model_validate(
        {
            "schema_version": 1,
            "subjects": [
                {
                    "key": "buyer",
                    "person_id": str(self_id) if self_id else None,
                    "display_name": "Buyer",
                    "relationship": "self",
                },
                {
                    "key": "mother",
                    "person_id": str(parent_id) if parent_id else None,
                    "display_name": "Mother",
                    "relationship": "parent",
                },
            ],
            "statements": [
                {
                    "start_offset": 0,
                    "end_offset": len(text),
                    "subject_key": "mother",
                    "kind": "intended_insured",
                    "ambiguous": False,
                    "ambiguity_reason": None,
                }
            ],
            "facts": [],
            "requirements": [],
            "corrections": [],
            "intent": "purchase_recommendation",
            "ambiguity": False,
            "clarification_question": None,
        }
    )


def test_person_fact_requires_an_explicit_subject() -> None:
    text = "Age 42"
    interpretation = CustomerInterpretationV1.model_validate(
        {
            "schema_version": 1,
            "subjects": [],
            "statements": [
                {
                    "start_offset": 0,
                    "end_offset": len(text),
                    "subject_key": None,
                    "kind": "fact",
                    "ambiguous": False,
                    "ambiguity_reason": None,
                }
            ],
            "facts": [
                {
                    "statement_index": 0,
                    "subject_key": None,
                    "fact_type": "age",
                    "value": {
                        "state": "known",
                        "kind": "quantity",
                        "value": "42",
                        "unit": "year",
                    },
                    "confidence": "explicit",
                }
            ],
            "requirements": [],
            "corrections": [],
            "intent": "conversation",
            "ambiguity": False,
            "clarification_question": None,
        }
    )

    with pytest.raises(ValueError, match="age must be scoped to a person"):
        validate_interpretation(text, interpretation)


def test_explicit_policy_term_survives_catalogue_name_clarification() -> None:
    text = "A five-year policy term is mandatory. Compare the three reviewed products."
    value = _family_interpretation(text)
    value.statements[0].subject_key = None
    value.statements[0].kind = "requirement"
    value.statements[0].ambiguous = True
    value.statements[0].ambiguity_reason = "Need product names."
    value.ambiguity = True
    value.clarification_question = "Which product names should I compare?"
    recover_explicit_policy_term(text, value)
    suppress_catalogue_clarification(text, value)
    validate_interpretation(text, value)
    assert not value.ambiguity
    assert not value.statements[0].ambiguous
    assert value.requirements[0].criterion == "policy_tenure_selection"
    assert value.requirements[0].priority == "mandatory"
    assert value.requirements[0].target_value == {
        "state": "known", "kind": "quantity", "value": "5", "unit": "year"
    }


def test_requested_cover_amount_does_not_block_a_verified_term_match() -> None:
    value = _family_interpretation("Want ₹10 lakh cover. A five-year term is mandatory.")
    value.requirements.append(
        InterpretedRequirement.model_validate({
            "statement_index": 0,
            "subject_key": None,
            "criterion": "sum_insured",
            "operator": "equals",
            "target_value": {"state": "known", "kind": "quantity", "value": "1000000", "unit": "INR"},
            "priority": "mandatory",
            "scope": "entire_purchase",
        })
    )
    normalize_requested_sum_insured_priority("Want ₹10 lakh cover. A five-year term is mandatory.", value)
    assert value.requirements[0].priority == "preferred"
    value.requirements[0].priority = "mandatory"
    normalize_requested_sum_insured_priority(
        "I need ₹10 lakh health cover for myself. It is mandatory that the sum insured "
        "becomes available again for a second hospitalization.",
        value,
    )
    assert value.requirements[0].priority == "preferred"
    value.requirements[0].priority = "mandatory"
    normalize_requested_sum_insured_priority("A ₹10 lakh base sum insured is mandatory.", value)
    assert value.requirements[0].priority == "mandatory"


def test_money_quantity_units_are_canonicalized_for_the_rule_engine() -> None:
    value = _family_interpretation("₹15,000 a year budget, ₹10 lakh sum insured target.")
    value.requirements.append(InterpretedRequirement.model_validate({
        "statement_index": 0, "subject_key": None, "criterion": "budget",
        "operator": "less_than_or_equal", "target_value": {
            "state": "known", "kind": "quantity", "value": "15000", "unit": "INR per year",
        }, "priority": "preferred", "scope": "entire_purchase",
    }))
    value.requirements.append(InterpretedRequirement.model_validate({
        "statement_index": 0, "subject_key": None, "criterion": "sum_insured",
        "operator": "equals", "target_value": {
            "state": "known", "kind": "quantity", "value": "1000000", "unit": "INR",
        }, "priority": "preferred", "scope": "entire_purchase",
    }))

    normalize_money_quantity_units(value)

    budget, sum_insured = value.requirements
    assert budget.target_value == {
        "state": "known", "kind": "quantity", "value": "15000",
        "unit": "money_per_year", "currency": "INR",
    }
    assert sum_insured.target_value == {
        "state": "known", "kind": "quantity", "value": "1000000",
        "unit": "money", "currency": "INR",
    }


def test_second_hospitalization_restoration_stays_typed() -> None:
    text = (
        "It is mandatory that the sum insured becomes available again for a second "
        "hospitalization in the same policy year after a first paid hospitalization "
        "claim uses all the base cover."
    )
    value = _family_interpretation(text)
    value.requirements.append(InterpretedRequirement.model_validate({
        "statement_index": 0, "subject_key": None, "criterion": "restoration",
        "operator": "equals", "target_value": {
            "state": "known", "kind": "text", "value": text,
        }, "priority": "mandatory", "scope": "entire_purchase",
    }))

    normalize_explicit_restoration_scenario(text, value)

    assert value.requirements[-1].target_value == {
        "state": "known", "kind": "boolean", "value": True,
    }


def test_explicit_self_cover_has_boolean_intended_insured_fact() -> None:
    value = _family_interpretation("I want health insurance for myself.")
    value.facts.append(InterpretedFact.model_validate({
        "statement_index": 0, "subject_key": "buyer", "fact_type": "intended_insured",
        "value": {"state": "known", "kind": "text", "value": "self"},
        "confidence": "explicit",
    }))

    normalize_self_insured_fact("I want health insurance for myself.", value)

    assert value.facts[-1].value == {"state": "known", "kind": "boolean", "value": True}


def test_explicit_family_city_survives_an_omitted_model_fact() -> None:
    text = "Maya Rao is a 34-year-old parent in Bengaluru. She wants cover for Avi."
    value = _family_interpretation(text)

    recover_explicit_city(text, value)

    assert value.facts[-1].fact_type == "city"
    assert value.facts[-1].subject_key is None
    assert value.facts[-1].value == {
        "state": "known", "kind": "text", "value": "Bengaluru",
    }


def test_first_turn_cannot_reference_nonexistent_customer_records() -> None:
    value = _family_interpretation("Apply the verified Care Supreme exclusion.")
    value.subjects[0].person_id = str(uuid.uuid4())
    value.corrections.append(InterpretedCorrection.model_validate({
        "statement_index": 0, "assertion_kind": "fact",
        "logical_key": "maternity_coverage.care_supreme",
        "replacement_value": {"state": "known", "kind": "boolean", "value": False},
        "replacement_status": "confirmed",
    }))

    normalize_first_turn_references(value, starting_revision=1)

    assert value.corrections == []
    assert value.subjects[0].person_id is None


def test_room_claim_illustration_recovers_only_stated_amounts() -> None:
    text = (
        "Eligible room rent is ₹5,000, actual room rent is ₹10,000, "
        "and associated medical expenses are ₹1 lakh for a higher room category."
    )
    value = _family_interpretation(text)
    recover_explicit_room_illustration(text, value)
    validate_interpretation(text, value)
    by_type = {fact.fact_type: fact.value for fact in value.facts}
    assert by_type["eligible_room_rent_limit"]["value"] == "5000"
    assert by_type["room_rent_actually_incurred"]["value"] == "10000"
    assert by_type["total_associated_medical_expenses"]["value"] == "100000"
    assert by_type["actual_room_category_higher_than_eligible"]["value"] is True


@pytest.mark.django_db
def test_purchase_city_attached_to_parent_is_saved_at_purchase_scope(v2_user: User) -> None:
    conversation = create_conversation(v2_user.id)
    KnowledgeChannel.objects.create(name="live")
    message = _message(v2_user.id, conversation.id, 1, "Cover my mother in Bengaluru.")
    interpretation = _family_interpretation(message.content)
    interpretation.facts.append(
        InterpretedFact.model_validate(
            {
                "statement_index": 0,
                "subject_key": "mother",
                "fact_type": "city",
                "value": {"state": "known", "kind": "text", "value": "Bengaluru"},
                "confidence": "explicit",
            }
        )
    )

    normalize_purchase_fact_scopes(interpretation)
    validate_interpretation(message.content, interpretation)
    apply_interpretation(
        message,
        interpretation,
        expected_profile_revision_id=conversation.current_profile_revision_id,
        expected_release_id=None,
        expected_channel_generation=0,
        expected_erasure_generation=v2_user.erasure_generation,
    )

    city = next(
        fact
        for fact in current_profile_payload(v2_user.id, conversation.id)["facts"]
        if fact["fact_type"] == "city"
    )
    assert city["subject_person_id"] is None


@pytest.mark.parametrize(
    ("text", "expected", "unit"),
    [
        ("Cover my 60-day-old baby.", "60", "day"),
        ("Cover my four-year-old child.", "4", "year"),
    ],
)
def test_explicit_child_age_is_recovered_from_exact_source(
    text: str, expected: str, unit: str
) -> None:
    interpretation = CustomerInterpretationV1.model_validate(
        {
            "schema_version": 1,
            "subjects": [
                {
                    "key": "child",
                    "person_id": None,
                    "display_name": "Child",
                    "relationship": "child",
                }
            ],
            "statements": [
                {
                    "start_offset": 0,
                    "end_offset": len(text),
                    "subject_key": None,
                    "kind": "intended_insured",
                    "ambiguous": False,
                    "ambiguity_reason": None,
                }
            ],
            "facts": [
                {
                    "statement_index": 0,
                    "subject_key": "child",
                    "fact_type": "intended_insured",
                    "value": {"state": "known", "kind": "boolean", "value": True},
                    "confidence": "explicit",
                }
            ],
            "requirements": [],
            "corrections": [],
            "intent": "purchase_recommendation",
            "ambiguity": False,
            "clarification_question": None,
        }
    )

    recover_explicit_child_age(text, interpretation)
    validate_interpretation(text, interpretation)

    age = next(fact for fact in interpretation.facts if fact.fact_type == "age")
    assert age.subject_key == "child"
    assert age.value == {"state": "known", "kind": "quantity", "value": expected, "unit": unit}


@pytest.mark.django_db
def test_person_fact_uses_its_own_subject_when_statement_is_unscoped(v2_user: User) -> None:
    conversation = create_conversation(v2_user.id)
    KnowledgeChannel.objects.create(name="live")
    message = _message(v2_user.id, conversation.id, 1, "I want cover for my child.")
    interpretation = CustomerInterpretationV1.model_validate(
        {
            "schema_version": 1,
            "subjects": [
                {
                    "key": "self",
                    "person_id": None,
                    "display_name": "I",
                    "relationship": "self",
                },
                {
                    "key": "child",
                    "person_id": None,
                    "display_name": "Child",
                    "relationship": "child",
                }
            ],
            "statements": [
                {
                    "start_offset": 0,
                    "end_offset": len(message.content),
                    "subject_key": "self",
                    "kind": "intended_insured",
                    "ambiguous": False,
                    "ambiguity_reason": None,
                }
            ],
            "facts": [
                {
                    "statement_index": 0,
                    "subject_key": "child",
                    "fact_type": "intended_insured",
                    "value": {"state": "known", "kind": "boolean", "value": True},
                    "confidence": "explicit",
                }
            ],
            "requirements": [],
            "corrections": [],
            "intent": "purchase_recommendation",
            "ambiguity": False,
            "clarification_question": None,
        }
    )

    apply_interpretation(
        message,
        interpretation,
        expected_profile_revision_id=conversation.current_profile_revision_id,
        expected_release_id=None,
        expected_channel_generation=0,
        expected_erasure_generation=v2_user.erasure_generation,
    )

    facts = [
        fact
        for fact in current_profile_payload(v2_user.id, conversation.id)["facts"]
        if fact["fact_type"] == "intended_insured"
    ]
    assert len(facts) == 1
    assert facts[0]["subject_person_id"] is not None


@pytest.mark.django_db
def test_interpretation_rejects_a_stale_profile_before_writing(v2_user: User) -> None:
    conversation = create_conversation(v2_user.id)
    KnowledgeChannel.objects.create(name="live")
    message = _message(v2_user.id, conversation.id, 1, "Cover my mother.")

    with pytest.raises(PinnedStateChanged):
        apply_interpretation(
            message,
            _family_interpretation(message.content),
            expected_profile_revision_id=uuid.uuid4(),
            expected_release_id=None,
            expected_channel_generation=0,
            expected_erasure_generation=0,
        )

    conversation.refresh_from_db()
    assert conversation.current_profile_revision is not None
    assert conversation.current_profile_revision.revision == 1
    assert CustomerProfileRevision.objects.filter(conversation=conversation).count() == 1
    assert not CustomerStatement.objects.filter(source_message=message).exists()
    assert not AdviceRequest.objects.filter(conversation=conversation).exists()


@pytest.mark.django_db
def test_repeated_interpretation_reuses_the_same_relationship(v2_user: User) -> None:
    conversation = create_conversation(v2_user.id)
    KnowledgeChannel.objects.create(name="live")
    first_message = _message(v2_user.id, conversation.id, 1, "Cover my mother.")
    first = apply_interpretation(
        first_message,
        _family_interpretation(first_message.content),
        expected_profile_revision_id=conversation.current_profile_revision_id,
        expected_release_id=None,
        expected_channel_generation=0,
        expected_erasure_generation=0,
    )
    buyer, mother = Person.objects.filter(owner=v2_user).order_by("created_at")
    second_message = _message(v2_user.id, conversation.id, 2, "Still cover my mother.")

    apply_interpretation(
        second_message,
        _family_interpretation(
            second_message.content,
            self_id=buyer.id,
            parent_id=mother.id,
        ),
        expected_profile_revision_id=first.profile_revision.id,
        expected_release_id=None,
        expected_channel_generation=0,
        expected_erasure_generation=0,
    )

    assert (
        PersonRelationship.objects.filter(
            owner=v2_user,
            from_person=buyer,
            to_person=mother,
            relationship_type="parent",
        ).count()
        == 1
    )

    intended = CustomerFact.objects.get(
        owner=v2_user,
        fact_type="intended_insured",
        source_statement__subject_person=mother,
    )
    assert intended.value == {"state": "known", "kind": "boolean", "value": True}


@pytest.mark.django_db
def test_fact_correction_preserves_the_original_subject(v2_user: User) -> None:
    conversation = create_conversation(v2_user.id)
    KnowledgeChannel.objects.create(name="live")
    first_message = _message(v2_user.id, conversation.id, 1, "Cover my mother.")
    first = apply_interpretation(
        first_message,
        _family_interpretation(first_message.content),
        expected_profile_revision_id=conversation.current_profile_revision_id,
        expected_release_id=None,
        expected_channel_generation=0,
        expected_erasure_generation=0,
    )
    _buyer, mother = Person.objects.filter(owner=v2_user).order_by("created_at")
    original = CustomerFact.objects.get(
        owner=v2_user,
        fact_type="intended_insured",
        source_statement__subject_person=mother,
    )
    correction_text = "Actually, do not include her."
    correction_message = _message(v2_user.id, conversation.id, 2, correction_text)
    correction = CustomerInterpretationV1.model_validate(
        {
            "schema_version": 1,
            "subjects": [],
            "statements": [
                {
                    "start_offset": 0,
                    "end_offset": len(correction_text),
                    "subject_key": None,
                    "kind": "correction",
                    "ambiguous": False,
                    "ambiguity_reason": None,
                }
            ],
            "facts": [],
            "requirements": [],
            "corrections": [
                {
                    "statement_index": 0,
                    "assertion_kind": "fact",
                    "logical_key": str(original.logical_key),
                    "replacement_value": None,
                    "replacement_status": "retracted",
                }
            ],
            "intent": "conversation",
            "ambiguity": False,
            "clarification_question": None,
        }
    )

    apply_interpretation(
        correction_message,
        correction,
        expected_profile_revision_id=first.profile_revision.id,
        expected_release_id=None,
        expected_channel_generation=0,
        expected_erasure_generation=0,
    )

    latest = CustomerFact.objects.filter(logical_key=original.logical_key).latest(
        "introduced_in_revision__revision"
    )
    assert latest.status == "retracted"
    assert latest.source_statement.subject_person_id == mother.id
