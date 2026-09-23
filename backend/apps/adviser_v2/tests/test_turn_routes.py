from __future__ import annotations

import uuid
from typing import Any

import pytest
from django.db import DatabaseError, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.adviser.ai import RelayFailure
from apps.adviser_v2.model_gateway import route_for_binding
from apps.adviser_v2.models import Message, ModelRoute, Turn, TurnRouteBinding
from apps.adviser_v2.schemas import CustomerInterpretationV1
from apps.adviser_v2.services.customer import create_conversation, retry_turn, submit_message
from apps.adviser_v2.tests.test_outbox import queued_turn


def test_submission_pins_both_interactive_routes(v2_user: User) -> None:
    turn = queued_turn(v2_user)

    bindings = list(turn.route_bindings.select_related("route", "qualification").order_by("role"))

    assert [binding.role for binding in bindings] == [
        "comparison_answer",
        "fact_interpretation",
    ]
    assert len(turn.route_commitment) == 64
    assert all(binding.qualification.result == "passed" for binding in bindings)
    assert all(
        binding.route.configuration_sha256 == binding.route_configuration_sha256
        for binding in bindings
    )
    assert all(binding.expected_model == binding.observed_model for binding in bindings)


def test_retry_keeps_the_original_routes_after_operator_settings_change(
    v2_user: User, settings: Any
) -> None:
    original = queued_turn(v2_user)
    Turn.objects.filter(pk=original.pk).update(state="failed", error_code="test_failure")
    original.refresh_from_db()
    original_routes = {
        binding.role: (
            binding.route_id,
            binding.qualification_id,
            binding.route_configuration_sha256,
        )
        for binding in original.route_bindings.all()
    }

    settings.COVERGUIDE_CUSTOMER_INTERPRETATION_ROUTE = "omniroute:not-qualified"
    settings.COVERGUIDE_COMPARISON_ROUTE = "omniroute:not-qualified"
    retried = retry_turn(v2_user.id, original.id).turn

    assert retried.route_commitment == original.route_commitment
    assert {
        binding.role: (
            binding.route_id,
            binding.qualification_id,
            binding.route_configuration_sha256,
        )
        for binding in retried.route_bindings.all()
    } == original_routes
    retried_binding = retried.route_bindings.select_related("route", "qualification").get(
        role="fact_interpretation"
    )
    runtime_route, _qualification = route_for_binding(
        retried_binding, "fact_interpretation", CustomerInterpretationV1
    )
    assert runtime_route.requested_model == retried_binding.requested_model
    assert runtime_route.relay_type == "cliproxyapi"


def test_disabled_pinned_route_fails_closed(v2_user: User) -> None:
    turn = queued_turn(v2_user)
    binding = turn.route_bindings.select_related("route", "qualification").get(
        role="fact_interpretation"
    )
    ModelRoute.objects.filter(pk=binding.route_id).update(disabled_at=timezone.now())
    binding.route.refresh_from_db()

    with pytest.raises(RelayFailure) as caught:
        route_for_binding(binding, "fact_interpretation", CustomerInterpretationV1)

    assert caught.value.code == "route_disabled"


def test_changed_pinned_endpoint_configuration_fails_closed(v2_user: User, settings: Any) -> None:
    turn = queued_turn(v2_user)
    binding = turn.route_bindings.select_related("route", "qualification").get(
        role="fact_interpretation"
    )
    settings.AI_RELAY_BASE_URL = "http://127.0.0.1:9999"

    with pytest.raises(RelayFailure) as caught:
        route_for_binding(binding, "fact_interpretation", CustomerInterpretationV1)

    assert caught.value.code == "route_configuration_mismatch"


def test_turn_route_binding_and_commitment_are_database_immutable(v2_user: User) -> None:
    turn = queued_turn(v2_user)
    binding = turn.route_bindings.select_related("route", "qualification").get(
        role="fact_interpretation"
    )

    with pytest.raises(DatabaseError, match="Turn route bindings are immutable"):
        with transaction.atomic():
            TurnRouteBinding.objects.filter(pk=binding.pk).update(
                route_configuration_sha256="f" * 64
            )
    with pytest.raises(DatabaseError, match="Turn route commitments are immutable"):
        with transaction.atomic():
            Turn.objects.filter(pk=turn.pk).update(route_commitment="f" * 64)

    route_for_binding(binding, "fact_interpretation", CustomerInterpretationV1)


def test_unqualified_operator_route_rolls_back_submission(v2_user: User, settings: Any) -> None:
    settings.DEBUG = True
    settings.OMNIROUTE_ENABLED = True
    settings.OMNIROUTE_BASE_URL = "http://127.0.0.1:20128"
    settings.OMNIROUTE_API_KEY = "test-key"
    settings.OMNIROUTE_LOGGING_DISABLED_CONFIRMED = True
    settings.COVERGUIDE_LOCAL_OMNIROUTE_PILOT_ACK = True
    settings.OMNIROUTE_MODELS = "gemini/unqualified=unqualified"
    settings.COVERGUIDE_COMPARISON_ROUTE = "omniroute:gemini/unqualified"
    conversation = create_conversation(v2_user.id)

    with pytest.raises(RelayFailure) as caught:
        submit_message(
            v2_user.id,
            conversation.id,
            request_id=uuid.uuid4(),
            text="Compare the reviewed products.",
            expected_profile_revision=1,
        )

    assert caught.value.code == "route_unqualified"
    assert not Message.objects.filter(conversation=conversation).exists()
    assert not Turn.objects.filter(conversation=conversation).exists()
