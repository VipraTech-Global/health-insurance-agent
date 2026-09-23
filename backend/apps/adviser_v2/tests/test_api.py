from __future__ import annotations

import json
import uuid
from datetime import timedelta
from typing import Any, cast
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory
from django.utils import timezone

from apps.accounts.models import User
from apps.adviser_v2.engine import _execution_times
from apps.adviser_v2.models import CustomerUploadedDocument, EvidenceSpan, Message, Outbox, Turn
from apps.adviser_v2.services.customer import append_turn_event
from apps.adviser_v2.views import _ranged_response


def csrf(client: Client) -> str:
    return client.cookies["csrftoken"].value


def post_json(client: Client, path: str, body: dict[str, object]) -> Any:
    return client.post(
        path,
        data=json.dumps(body),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf(client),
    )


def test_queued_turn_gets_its_full_execution_budget_when_claimed() -> None:
    submitted_at = timezone.now()
    started_at = submitted_at + timedelta(minutes=8)

    deadline, lease_until = _execution_times(started_at, 240)

    assert deadline == started_at + timedelta(seconds=240)
    assert lease_until == started_at + timedelta(seconds=480)


def test_pdf_range_clamps_an_overlong_end_to_the_preserved_file() -> None:
    request = RequestFactory().get("/", HTTP_RANGE="bytes=2-99")

    response = _ranged_response(b"0123456789", cast(Any, request), "application/pdf")

    assert response.status_code == 206
    assert response.content == b"23456789"
    assert response["Content-Range"] == "bytes 2-9/10"
    assert response["Content-Length"] == "8"


@pytest.mark.django_db
def test_retired_adviser_urls_and_recommendation_url_are_unavailable(
    v2_client: Client,
) -> None:
    identifier = uuid.uuid4()

    assert v2_client.get(f"/api/v2/recommendations/{identifier}/").status_code == 404
    assert v2_client.get("/api/v1/conversations/").status_code == 404
    assert v2_client.get(f"/api/v1/recommendations/{identifier}/").status_code == 404
    assert v2_client.get("/api/v1/auth/session/").status_code == 200


@pytest.mark.django_db
def test_quote_upload_is_encrypted_owner_scoped_and_range_downloadable(
    v2_client: Client,
    v2_user: User,
    settings: Any,
) -> None:
    conversation = post_json(v2_client, "/api/v2/conversations/", {}).json()
    payload = b"%PDF-1.7\nexact customer quote\n%%EOF\n"
    upload = SimpleUploadedFile("customer-quote.pdf", payload, content_type="application/pdf")

    with patch("apps.adviser_v2.views._schedule_document"):
        accepted = v2_client.post(
            f"/api/v2/conversations/{conversation['id']}/uploads/",
            data={"kind": "quote", "file": upload},
            HTTP_X_CSRFTOKEN=csrf(v2_client),
        )

    assert accepted.status_code == 202
    document = CustomerUploadedDocument.objects.select_related("original_file").get(
        pk=accepted.json()["id"]
    )
    assert document.owner_id == v2_user.id
    stored_bytes = (
        settings.COVERGUIDE_V2_STORAGE_ROOT / document.original_file.storage_key
    ).read_bytes()
    assert stored_bytes != payload
    span = EvidenceSpan.objects.create(
        customer_uploaded_document=document,
        section_label="customer quote",
        quote="Exact customer quote evidence.",
        context={"span_ids": [], "notes": []},
        method="native_text",
        verification="text_verified",
        locator={
            "schema_version": 1,
            "blob_sha256": document.original_file.sha256,
            "resolver_version": "coverguide-upload-test/1",
            "kind": "text_range",
            "encoding": "utf-8",
            "byte_start": 0,
            "byte_end_exclusive": len(payload),
            "newline_policy": "preserve_original",
        },
    )

    downloaded = v2_client.get(
        f"/api/v2/uploads/{document.id}/file/",
        HTTP_RANGE="bytes=0-999",
    )
    assert downloaded.status_code == 206
    assert downloaded.content == payload
    assert downloaded["Content-Range"] == f"bytes 0-{len(payload) - 1}/{len(payload)}"

    other = User.objects.create_user(
        email="other-upload@example.com", password="Other-Upload-Password-42"
    )
    other_client = Client()
    other_client.force_login(other)
    assert other_client.get(f"/api/v2/uploads/{document.id}/file/").status_code == 404
    assert v2_client.get(f"/api/v2/evidence/{span.id}/").status_code == 200
    assert other_client.get(f"/api/v2/evidence/{span.id}/").status_code == 404


@pytest.mark.django_db
def test_message_submission_is_atomic_idempotent_and_replayable(
    v2_client: Client,
) -> None:
    with patch("apps.adviser_v2.views._schedule_turn"):
        created = post_json(v2_client, "/api/v2/conversations/", {"title": "Family"})
        assert created.status_code == 201
        conversation_id = created.json()["id"]
        request_id = str(uuid.uuid4())
        body = {
            "request_id": request_id,
            "text": "I am buying cover for my mother.",
            "expected_profile_revision": 1,
        }
        first = post_json(v2_client, f"/api/v2/conversations/{conversation_id}/messages/", body)
        second = post_json(v2_client, f"/api/v2/conversations/{conversation_id}/messages/", body)
    assert first.status_code == second.status_code == 202
    assert first.json()["turn_id"] == second.json()["turn_id"]
    assert first.json()["created"] is True
    assert second.json()["created"] is False
    assert Message.objects.count() == 1
    assert Turn.objects.count() == 1
    assert Outbox.objects.count() == 1
    stream = v2_client.get(first.json()["event_url"], {"timeout": 0})
    assert stream.status_code == 200
    rendered = b"".join(cast(Any, stream).streaming_content)
    assert b"event: turn.accepted" in rendered
    assert stream["Cache-Control"] == "private, no-store"


@pytest.mark.django_db
def test_reused_request_id_with_different_payload_conflicts(v2_client: Client) -> None:
    with patch("apps.adviser_v2.views._schedule_turn"):
        created = post_json(v2_client, "/api/v2/conversations/", {}).json()
        request_id = str(uuid.uuid4())
        path = f"/api/v2/conversations/{created['id']}/messages/"
        first = post_json(
            v2_client,
            path,
            {"request_id": request_id, "text": "First", "expected_profile_revision": 1},
        )
        changed = post_json(
            v2_client,
            path,
            {"request_id": request_id, "text": "Changed", "expected_profile_revision": 1},
        )
    assert first.status_code == 202
    assert changed.status_code == 409


@pytest.mark.django_db
def test_sse_reconnect_resumes_after_sequence_and_queued_cancel_is_durable(
    v2_client: Client,
) -> None:
    with patch("apps.adviser_v2.views._schedule_turn"):
        conversation = post_json(v2_client, "/api/v2/conversations/", {}).json()
        submitted = post_json(
            v2_client,
            f"/api/v2/conversations/{conversation['id']}/messages/",
            {
                "request_id": str(uuid.uuid4()),
                "text": "Compare the reviewed policies.",
                "expected_profile_revision": 1,
            },
        ).json()
    turn = Turn.objects.get(pk=submitted["turn_id"])
    append_turn_event(
        turn,
        "progress",
        {"schema_version": 1, "kind": "progress", "progress_code": "checking_policies"},
    )

    resumed = v2_client.get(submitted["event_url"], {"after_sequence": 1, "timeout": 0})
    resumed_body = b"".join(cast(Any, resumed).streaming_content)
    assert b"id: 1\n" not in resumed_body
    assert b"id: 2\nevent: turn.progress" in resumed_body

    cancelled = post_json(v2_client, f"/api/v2/turns/{turn.id}/cancel/", {})
    assert cancelled.status_code == 200
    assert cancelled.json()["state"] == "cancelled"
    terminal_stream = v2_client.get(submitted["event_url"], {"after_sequence": 2, "timeout": 0})
    terminal_body = b"".join(cast(Any, terminal_stream).streaming_content)
    assert b"id: 3\nevent: turn.cancelled" in terminal_body


@pytest.mark.django_db
def test_sse_uses_comparison_terminal_event_name(v2_client: Client) -> None:
    with patch("apps.adviser_v2.views._schedule_turn"):
        conversation = post_json(v2_client, "/api/v2/conversations/", {}).json()
        submitted = post_json(
            v2_client,
            f"/api/v2/conversations/{conversation['id']}/messages/",
            {
                "request_id": str(uuid.uuid4()),
                "text": "Compare the reviewed products.",
                "expected_profile_revision": 1,
            },
        ).json()
    turn = Turn.objects.get(pk=submitted["turn_id"])
    comparison_id = uuid.uuid4()
    append_turn_event(
        turn,
        "comparison",
        {"schema_version": 1, "kind": "comparison", "comparison_id": str(comparison_id)},
    )

    stream = v2_client.get(submitted["event_url"], {"after_sequence": 1, "timeout": 0})
    rendered = b"".join(cast(Any, stream).streaming_content)
    assert b"event: comparison.completed" in rendered
    assert str(comparison_id).encode() in rendered
    assert b"recommendation.completed" not in rendered


@pytest.mark.django_db
def test_v2_resources_are_owner_scoped(v2_client: Client) -> None:
    created = post_json(v2_client, "/api/v2/conversations/", {"title": "Private"}).json()
    other = User.objects.create_user(email="other-v2@example.com", password="Other-V2-Password-42")
    other_client = Client()
    other_client.force_login(other)
    assert other_client.get(f"/api/v2/conversations/{created['id']}/").status_code == 404
    assert other_client.get(f"/api/v2/conversations/{created['id']}/profile/").status_code == 404


@pytest.mark.django_db
def test_turn_lifecycle_is_owner_scoped(v2_client: Client) -> None:
    with patch("apps.adviser_v2.views._schedule_turn"):
        conversation = post_json(v2_client, "/api/v2/conversations/", {}).json()
        submitted = post_json(
            v2_client,
            f"/api/v2/conversations/{conversation['id']}/messages/",
            {
                "request_id": str(uuid.uuid4()),
                "text": "Keep this request private.",
                "expected_profile_revision": 1,
            },
        ).json()
    turn_id = submitted["turn_id"]
    other = User.objects.create_user(
        email="other-turn@example.com", password="Other-Turn-Password-42"
    )
    other_client = Client()
    other_client.force_login(other)

    assert other_client.get(f"/api/v2/turns/{turn_id}/").status_code == 404
    assert other_client.get(f"/api/v2/turns/{turn_id}/events/?timeout=0").status_code == 404
    assert other_client.post(f"/api/v2/turns/{turn_id}/cancel/").status_code == 404
    assert other_client.post(f"/api/v2/turns/{turn_id}/retry/").status_code == 404

    turn = Turn.objects.get(pk=turn_id)
    assert turn.owner_id != other.id
    assert turn.state == "queued"


@pytest.mark.django_db
def test_profile_correction_checks_revision(v2_client: Client) -> None:
    created = post_json(v2_client, "/api/v2/conversations/", {}).json()
    path = f"/api/v2/conversations/{created['id']}/profile/"
    body = {
        "expected_revision": 1,
        "correction_text": "My budget is INR 30,000 per year.",
        "facts": [
            {
                "fact_type": "budget",
                "value": {
                    "state": "known",
                    "kind": "quantity",
                    "value": "30000",
                    "unit": "per_year",
                    "currency": "INR",
                },
            }
        ],
    }
    updated = v2_client.patch(
        path,
        data=json.dumps(body),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf(v2_client),
    )
    stale = v2_client.patch(
        path,
        data=json.dumps(body),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf(v2_client),
    )
    assert updated.status_code == 200
    assert updated.json()["revision"] == 2
    assert updated.json()["facts"][0]["value"]["value"] == "30000"
    assert stale.status_code == 409


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field,payload",
    [
        (
            "facts",
            {
                "fact_type": "budget",
                "value": {
                    "state": "known",
                    "kind": "quantity",
                    "value": "30000",
                    "unit": "per_year",
                    "currency": "INR",
                },
                "status": "invented",
            },
        ),
        (
            "requirements",
            {
                "criterion": "budget",
                "target_value": None,
                "operator": "approximately",
            },
        ),
    ],
)
def test_invalid_profile_choices_roll_back_the_entire_correction(
    v2_client: Client, field: str, payload: dict[str, object]
) -> None:
    created = post_json(v2_client, "/api/v2/conversations/", {}).json()
    path = f"/api/v2/conversations/{created['id']}/profile/"
    body: dict[str, object] = {
        "expected_revision": 1,
        "correction_text": "This invalid correction must not be retained.",
        "facts": [],
        "requirements": [],
    }
    body[field] = [payload]

    response = v2_client.patch(
        path,
        data=json.dumps(body),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf(v2_client),
    )

    assert response.status_code == 400
    profile = v2_client.get(path).json()
    assert profile["revision"] == 1
    assert not Message.objects.filter(conversation_id=created["id"]).exists()


@pytest.mark.django_db
def test_retry_reuses_exact_input_message_without_duplication(v2_client: Client) -> None:
    with patch("apps.adviser_v2.views._schedule_turn"):
        conversation = post_json(v2_client, "/api/v2/conversations/", {}).json()
        submitted = post_json(
            v2_client,
            f"/api/v2/conversations/{conversation['id']}/messages/",
            {
                "request_id": str(uuid.uuid4()),
                "text": "Please compare the reviewed catalogue.",
                "expected_profile_revision": 1,
            },
        ).json()
        Turn.objects.filter(pk=submitted["turn_id"]).update(state="failed")
        retried = post_json(v2_client, f"/api/v2/turns/{submitted['turn_id']}/retry/", {})
    assert retried.status_code == 202
    assert retried.json()["message_id"] == submitted["message_id"]
    assert retried.json()["turn_id"] != submitted["turn_id"]
    assert Message.objects.count() == 1
    assert Turn.objects.count() == 2
