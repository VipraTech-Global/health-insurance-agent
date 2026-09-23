import uuid
from datetime import timedelta

import pytest
from django.db import DatabaseError, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.adviser.ai import InterviewDraft, RelayFailure
from apps.adviser.ai_turns import prepare_turn, publish_ai_answer
from apps.adviser.models import (
    AnswerArtifact,
    ModelCallAttempt,
    RouteConfiguration,
    RouteQualification,
    Turn,
    TurnAttempt,
)
from apps.adviser.relay_routes import choose_model, configuration_hash, model_choices, route_values
from apps.adviser.services import (
    ConflictError,
    accept_turn,
    cancel_attempt,
    create_conversation,
    mark_running,
    revise_profile,
)


def prepared(user, qualified):
    conversation = create_conversation(user.id)
    accepted = accept_turn(
        user.id,
        conversation.id,
        {
            "request_id": str(uuid.uuid4()),
            "text": "I live in Bengaluru",
            "expected_profile_revision": 1,
        },
    )
    mark_running(user.id, uuid.UUID(accepted.attempt_id))
    result = prepare_turn(user.id, uuid.UUID(accepted.attempt_id))
    assert result is not None
    return conversation, result


def test_route_is_immutable_and_preferences_do_not_fallback(user, qualified):
    choose_model(user.id, qualified.id)
    with pytest.raises(DatabaseError), transaction.atomic():
        RouteConfiguration.objects.filter(pk=qualified.id).update(configured_model="substitution")
    RouteConfiguration.objects.filter(pk=qualified.id).update(qualification_state="failed")
    result = model_choices(user.id)
    assert result["selected_model"] == "gpt-6-astra" and not result["selected_available"]
    assert result["models"] == []
    with pytest.raises(RelayFailure):
        choose_model(user.id, qualified.id)


def test_preferences_are_per_user_and_capture_turn_route(user, qualified):
    values = route_values("gpt-5.6-sol")
    other = RouteConfiguration.objects.create(
        **values, configuration_hash=configuration_hash(values), qualification_state="qualified"
    )
    RouteQualification.objects.create(
        route=other, tested_configuration_hash=other.configuration_hash, state="qualified"
    )
    choose_model(user.id, other.id)
    second = User.objects.create_user(email="second@example.com", password="Valid-Test-Password42")
    assert model_choices(second.id)["selected_model"] == "gpt-6-astra"
    _, turn = prepared(user, qualified)
    assert turn.route.model == "gpt-5.6-sol"
    choose_model(user.id, qualified.id)
    assert Turn.objects.get(attempts__id=turn.attempt_id).route_id == other.id
    assert TurnAttempt.objects.get(id=turn.attempt_id).route_id == other.id


def test_interview_suggestions_are_reviewable_and_quote_grounded(user, qualified):
    conversation, turn = prepared(user, qualified)
    draft = InterviewDraft.model_validate({"fields": [{"field": "location", "value": "Bengaluru"}]})
    answer = publish_ai_answer(user.id, turn, draft)
    assert answer["verification_status"] == "ai_validated"
    assert answer["blocks"][1]["patch"] == {"location": "Bengaluru"}
    conversation.refresh_from_db()
    assert conversation.current_profile.data == {}
    assert conversation.messages.get(role="assistant").content.endswith('{"location": "Bengaluru"}')


@pytest.mark.parametrize(
    "change", ["profile", "cancel", "deadline", "qualification", "fabrication"]
)
def test_publication_rechecks_captured_state(user, qualified, change):
    conversation, turn = prepared(user, qualified)
    draft = InterviewDraft.model_validate({"fields": [{"field": "location", "value": "Bengaluru"}]})
    if change == "profile":
        revise_profile(user.id, conversation.id, 1, {"location": "Mumbai"})
    elif change == "cancel":
        cancel_attempt(user.id, turn.attempt_id)
    elif change == "deadline":
        TurnAttempt.objects.filter(id=turn.attempt_id).update(
            deadline_at=timezone.now() - timedelta(seconds=1)
        )
    elif change == "qualification":
        RouteConfiguration.objects.filter(pk=qualified.id).update(qualification_state="failed")
    else:
        draft.fields[0].value = "Mumbai"
    with pytest.raises((ConflictError, RelayFailure)):
        publish_ai_answer(user.id, turn, draft)
    assert not AnswerArtifact.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_failed_qualification_stays_hidden_and_audited(monkeypatch, user):
    from apps.adviser import relay_routes
    from apps.adviser.relay_management import RelayCredential

    monkeypatch.setattr(relay_routes, "discover_models", lambda: ["gpt-5.6-luna"])
    monkeypatch.setattr(
        "apps.adviser.relay_management.RelayManagementClient.credentials",
        lambda *_: (RelayCredential("opaque", "codex", False, False, "a***", ""),),
    )
    monkeypatch.setattr("django.conf.settings.AI_RELAY_MANAGEMENT_KEY", "m" * 64)

    async def fail(*_):
        raise RelayFailure("model_identity_mismatch", "The model identity did not match.")

    monkeypatch.setattr(relay_routes, "probe", fail)
    qualification = relay_routes.qualify_model("gpt-5.6-luna")
    assert qualification.state == "failed"
    assert model_choices(user.id)["models"] == []
    call = ModelCallAttempt.objects.get()
    assert call.status == "failed" and call.safe_error_code == "model_identity_mismatch"
    with pytest.raises(DatabaseError), transaction.atomic():
        RouteQualification.objects.filter(pk=qualification.pk).update(state="qualified")
