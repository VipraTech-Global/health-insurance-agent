import json
import uuid
from datetime import timedelta

import httpx
import pytest
from asgiref.sync import async_to_sync
from django.db import DatabaseError, connection, transaction
from django.test import Client
from django.utils import timezone

from apps.accounts.models import User
from apps.adviser.ai import InterviewDraft, RelayFailure
from apps.adviser.ai_turns import prepare_turn, publish_ai_answer
from apps.adviser.models import (
    AIPreference,
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


def test_admin_permissions_csrf_and_user_preferences(user, qualified, monkeypatch):
    browser = Client(enforce_csrf_checks=True)
    assert browser.get("/api/v1/ai/models/").status_code == 403
    browser.force_login(user)
    assert browser.get("/api/v1/admin/ai-relay/").status_code == 403
    assert (
        browser.post("/api/v1/admin/ai-relay/accounts/", data={"action": "forget"}).status_code
        == 403
    )
    assert (
        browser.post(
            "/api/v1/admin/ai-relay/qualifications/", data={"model": "gpt-6-astra"}
        ).status_code
        == 403
    )
    assert (
        browser.patch(
            "/api/v1/ai/preferences/",
            data=json.dumps({"route_id": str(qualified.id)}),
            content_type="application/json",
        ).status_code
        == 403
    )
    browser.get("/api/v1/auth/csrf/")
    response = browser.patch(
        "/api/v1/ai/preferences/",
        data=json.dumps({"route_id": str(qualified.id)}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=browser.cookies["csrftoken"].value,
    )
    assert response.status_code == 200 and AIPreference.objects.get(user=user).route == qualified
    user.is_staff = True
    user.save()
    assert (
        browser.post("/api/v1/admin/ai-relay/accounts/", data={"action": "forget"}).status_code
        == 403
    )
    monkeypatch.setattr("apps.adviser.ai_views.discover_models", lambda: ["gpt-6-astra"])
    from apps.adviser.relay_accounts import ProviderAccountSummary

    monkeypatch.setattr(
        "apps.adviser.ai_views.provider_account_summary",
        lambda _: ProviderAccountSummary(
            "codex", "Codex", "Connected", "p***@e***.com", True, False, False, False
        ),
    )
    response = browser.get("/api/v1/admin/ai-relay/")
    assert response.status_code == 200 and response["Cache-Control"] == "no-store"


@pytest.mark.django_db(transaction=True)
def test_stream_calls_provider_with_no_database_connection(user, qualified, monkeypatch, settings):
    from config.lifecycle import runtime

    settings.AI_RELAY_API_KEY = "fake-secret"
    monkeypatch.setattr("apps.adviser.streaming.active_account_identity", lambda: "account-hash")
    conversation = create_conversation(user.id)
    captured = []

    async def handler(request):
        def check():
            # Runs in the same thread as all preceding ORM boundaries.
            assert connection.connection is None

        from asgiref.sync import sync_to_async

        await sync_to_async(check, thread_sensitive=True)()
        captured.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "model": "gpt-6-astra",
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"fields":[{"field":"location","value":"Bengaluru"}]}',
                            }
                        ],
                    }
                ],
            },
        )

    browser = Client()
    browser.force_login(user)
    response = browser.post(
        f"/api/v1/conversations/{conversation.id}/turns/",
        data=json.dumps(
            {
                "request_id": str(uuid.uuid4()),
                "text": "I live in Bengaluru",
                "expected_profile_revision": 1,
            }
        ),
        content_type="application/json",
    )

    async def collect():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            monkeypatch.setattr(runtime, "http_client", client)
            return b"".join([chunk async for chunk in response.streaming_content])

    content = async_to_sync(collect)()
    assert b"event: result" in content and len(captured) == 1
    assert ModelCallAttempt.objects.get().status == "succeeded"
    assert ModelCallAttempt.objects.get().upstream_reported_model == "gpt-6-astra"


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


@pytest.mark.django_db(transaction=True)
def test_cancelling_stream_stops_provider_and_never_publishes(
    user, qualified, monkeypatch, settings
):
    import asyncio

    from config.lifecycle import runtime

    from apps.adviser.streaming import _database_call

    settings.AI_RELAY_API_KEY = "fake-secret"
    monkeypatch.setattr("apps.adviser.streaming.active_account_identity", lambda: "account-hash")
    conversation = create_conversation(user.id)
    browser = Client()
    browser.force_login(user)
    response = browser.post(
        f"/api/v1/conversations/{conversation.id}/turns/",
        data=json.dumps(
            {
                "request_id": str(uuid.uuid4()),
                "text": "I live in Bengaluru",
                "expected_profile_revision": 1,
            }
        ),
        content_type="application/json",
    )
    attempt_id = TurnAttempt.objects.get().id
    cancelled = []

    async def handler(request):
        await _database_call(cancel_attempt, user.id, attempt_id)
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled.append(True)
            raise
        return httpx.Response(500)

    async def collect():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            monkeypatch.setattr(runtime, "http_client", client)
            return b"".join([chunk async for chunk in response.streaming_content])

    content = async_to_sync(collect)()
    assert b"attempt_not_active" in content and cancelled == [True]
    assert not AnswerArtifact.objects.exists()
    call = ModelCallAttempt.objects.get()
    assert call.status == "failed" and call.safe_error_code == "attempt_not_active"
    assert TurnAttempt.objects.get().status == "cancelled"
