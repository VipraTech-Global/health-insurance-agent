from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db import connection

from apps.accounts.models import User
from apps.adviser.ai import validate_strict_schema
from apps.adviser_v2.contracts import (
    contract_document,
    contract_schema_document,
    validate_contract,
)
from apps.adviser_v2.crypto import commitment, commitment_matches
from apps.adviser_v2.models import Conversation
from apps.adviser_v2.schemas import (
    CustomerInterpretationV1,
    PolicyRuleExtractionV1,
    PolicyRuleReviewV1,
    RecommendationDraftV1,
)


def test_all_referenced_json_components_resolve() -> None:
    document = contract_document()
    references = set()

    def visit(value: object) -> None:
        if isinstance(value, dict):
            reference = value.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/$defs/"):
                references.add(reference.removeprefix("#/$defs/"))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(document)
    assert references <= document["$defs"].keys()


def test_prompt_schema_contains_the_rule_contract_reference_closure() -> None:
    schema = contract_schema_document("RuleV1")

    assert schema["$ref"] == "#/$defs/RuleV1"
    assert {
        "RuleV1",
        "PredicateV1",
        "ExpressionV1",
        "LimitScopeV1",
        "DurationV1",
    }.issubset(schema["$defs"])


def test_nested_closed_contracts_validate() -> None:
    assert validate_contract(
        "FactValueV1",
        {
            "state": "known",
            "kind": "duration",
            "value": {
                "state": "known",
                "value": 36,
                "unit": "calendar_month",
                "anchor_event": "policy inception",
                "boundary": "inclusive",
            },
        },
    )
    with pytest.raises(ValueError, match="not valid"):
        validate_contract(
            "FactValueV1",
            {"state": "known", "kind": "boolean", "value": True, "invented": 1},
        )


def test_all_v2_model_schemas_are_strict_relay_compatible() -> None:
    for model in (
        CustomerInterpretationV1,
        PolicyRuleExtractionV1,
        PolicyRuleReviewV1,
        RecommendationDraftV1,
    ):
        validate_strict_schema(model.model_json_schema())


def test_embedded_contract_string_is_decoded_and_closed() -> None:
    interpretation = CustomerInterpretationV1.model_validate(
        {
            "schema_version": 1,
            "subjects": [],
            "statements": [
                {
                    "start_offset": 0,
                    "end_offset": 4,
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
                    "fact_type": "has_diabetes",
                    "value": '{"state":"known","kind":"boolean","value":true}',
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
    assert interpretation.facts[0].value["value"] is True
    with pytest.raises(ValueError, match="FactValueV1"):
        CustomerInterpretationV1.model_validate(
            {
                **interpretation.model_dump(mode="json"),
                "facts": [
                    {
                        "statement_index": 0,
                        "subject_key": None,
                        "fact_type": "has_diabetes",
                        "value": '{"state":"known","kind":"boolean","value":true,"extra":1}',
                        "confidence": "explicit",
                    }
                ],
            }
        )


def test_commitments_are_keyed_and_verifiable() -> None:
    digest = commitment({"message": "diabetes"})
    assert len(digest) == 64
    assert commitment_matches(digest, {"message": "diabetes"})
    assert not commitment_matches(digest, {"message": "hypertension"})


@pytest.mark.django_db
def test_encrypted_model_field_never_stores_plaintext(v2_user: User) -> None:
    phrase = "Private diabetes disclosure"
    conversation = Conversation.objects.create(owner=v2_user, title=phrase)
    with connection.cursor() as cursor:
        cursor.execute("SELECT title FROM adviser_v2_conversation WHERE id = %s", [conversation.id])
        stored = cursor.fetchone()[0]
    assert phrase not in stored
    assert stored.startswith("cg2$")
    assert Conversation.objects.get(pk=conversation.pk).title == phrase


@pytest.mark.django_db
def test_validated_json_field_rejects_invalid_write(v2_user: User) -> None:
    from apps.adviser_v2.models import CustomerFact

    field = CustomerFact._meta.get_field("value")
    with pytest.raises(ValidationError):
        field.get_prep_value({"state": "known", "kind": "boolean"})
