import json
import threading
import time

import pytest
from django.utils import timezone

from apps.adviser_v2.demo.evidence import digest
from apps.adviser_v2.demo.services import (
    bundle_for,
    decrypted,
    encrypted,
    publish_progress,
    question_payload,
    run_question,
    save_profile,
    submit,
)
from apps.adviser_v2.models import (
    DemoPlanAnswer,
    DemoPlanIndex,
    DemoQuestion,
    DemoRelease,
    DemoSession,
)
from apps.adviser_v2.services.erasure import erase_account
from apps.adviser_v2.tests.test_demo_contracts import card, profile

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def demo(v2_user, tmp_path):
    release = DemoRelease.objects.create(method="P", manifest_sha256="a" * 64, bakeoff={"protocol_version": 2}, active=True)
    rows = []
    for i in range(5):
        bundle = {"policy_version_id": f"plan{i}", "sections": [], "documents": [], "navigation": []}
        key = digest(bundle)
        bundle["index_id"] = key
        path = tmp_path / (key + ".json")
        path.write_text(json.dumps(bundle))
        plan_card = card(f"plan{i}")
        plan_card.index_version = key
        row = DemoPlanIndex.objects.create(id=key, plan_key=plan_card.plan_id, insurer=plan_card.insurer,
            name=plan_card.name, plan_type=plan_card.plan_type, bundle_path=str(path), card=plan_card.model_dump())
        rows.append(row)
    release.indexes.set(rows)
    session = save_profile(v2_user, profile())
    return release, session, rows


def test_selection_pins_release_and_indexes_and_inputs_are_encrypted(v2_user, demo):
    release, session, rows = demo
    question = submit(v2_user, session.id, "What is covered?", [r.plan_key for r in rows[:3]])
    assert b"What is covered" not in bytes(question.input_ciphertext)
    assert decrypted(question.input_ciphertext, question.id)["question"] == "What is covered?"
    release.active = False
    release.save()
    newer = DemoRelease.objects.create(method="H", manifest_sha256="b"*64, bakeoff={}, active=True)
    newer.indexes.add(rows[-1])
    question.refresh_from_db()
    assert question.release_id == release.id and question.answers.count() == 3


def test_browser_event_stream_accept_header_receives_progress(v2_user, v2_client, demo):
    _, session, rows = demo
    question = submit(v2_user, session.id, 'What is covered?', [r.plan_key for r in rows[:2]])
    DemoQuestion.objects.filter(pk=question.pk).update(state='completed')
    response = v2_client.get(f'/api/v2/demo/questions/{question.id}/events/', HTTP_ACCEPT='text/event-stream')
    assert response.status_code == 200 and response['Content-Type'] == 'text/event-stream'
    payload = b''.join(response.streaming_content).decode()
    assert payload.startswith('data: ') and '"state": "completed"' in payload


def test_cancel_revision_and_revocation_block_late_publication(v2_user, demo):
    _, session, rows = demo
    question = submit(v2_user, session.id, "Q", [r.plan_key for r in rows[:2]])
    row = question.answers.first()
    save_profile(v2_user, profile(), session.id)
    assert not publish_progress(row.id, "answered", {"models": [], "answer": "late"})
    question = DemoQuestion.objects.select_related("session__owner").get(pk=question.id)
    assert question_payload(question)["plans"] == []
    fresh = submit(v2_user, session.id, "Q2", [r.plan_key for r in rows[:2]])
    row = fresh.answers.first()
    row.index.revoked_at = timezone.now()
    row.index.save()
    assert not publish_progress(row.id, "answered", {"models": []})
    visible = next(p for p in question_payload(fresh)["plans"] if p["id"] == str(row.id))
    assert visible["state"] == "source_revoked"


def test_rejected_attempts_are_never_returned_to_customers(v2_user, demo):
    _, session, rows = demo
    question = submit(v2_user, session.id, "Q", [r.plan_key for r in rows[:2]])
    row = question.answers.first()
    assert publish_progress(row.id, "answered", {"status": "answered", "models": ["gpt-5.6-luna"],
        "attempts": [{"answer": "REJECTED WRONG-PLAN TEXT"}], "packet": {"text": "WHOLE PACKET"}, "answer": "ACCEPTED"})
    payload = json.dumps(question_payload(question))
    assert "REJECTED" not in payload and "WHOLE PACKET" not in payload and "ACCEPTED" in payload


def test_erasure_cascades_demo_private_data_and_late_worker_cannot_restore(v2_user, demo):
    _, session, rows = demo
    question = submit(v2_user, session.id, "Q", [r.plan_key for r in rows[:2]])
    row = question.answers.first()
    publish_progress(row.id, "answering")
    erase_account(v2_user.id)
    assert not DemoSession.objects.filter(owner=v2_user).exists()
    assert not DemoQuestion.objects.filter(pk=question.id).exists()
    assert not DemoPlanAnswer.objects.filter(pk=row.id).exists()
    assert not publish_progress(row.id, "answered", {"models": []})
    assert DemoPlanIndex.objects.count() == 5


def test_bundle_tampering_and_ciphertext_identity_are_rejected(demo):
    _, _, rows = demo
    row = rows[0]
    bundle = bundle_for(row)
    bundle["navigation"] = ["changed"]
    from pathlib import Path
    Path(row.bundle_path).write_text(json.dumps(bundle))
    with pytest.raises(ValueError, match="hash"):
        bundle_for(row)
    from cryptography.exceptions import InvalidTag
    with pytest.raises(InvalidTag):
        decrypted(encrypted({"private": 1}, "one"), "two")


def test_five_plan_chains_overlap_and_publish_as_each_finishes(v2_user, demo, monkeypatch):
    _, session, rows = demo
    question = submit(v2_user, session.id, "Q", [r.plan_key for r in rows])
    lock = threading.Lock()
    concurrent, peak = 0, 0

    def fake(bundle, text, *, method, progress):
        nonlocal concurrent, peak
        progress("searching")
        with lock:
            concurrent += 1
            peak = max(peak, concurrent)
        time.sleep(.15)
        progress("answering")
        time.sleep(.15)
        with lock:
            concurrent -= 1
        return {"status": "not_found", "models": ["gpt-5.6-luna"], "total_ms": 300}

    monkeypatch.setattr("apps.adviser_v2.demo.services.answer_plan", fake)
    started = time.monotonic()
    run_question(question.id)
    elapsed = time.monotonic() - started
    assert peak == 5
    assert elapsed < 1.3  # Five serial chains alone would require 1.5 seconds.
    question.refresh_from_db()
    assert question.state == "completed"
    assert set(question.answers.values_list("state", flat=True)) == {"not_found"}


def test_api_ownership_selection_and_coverage(v2_client, v2_user, demo, monkeypatch):
    _, session, rows = demo
    monkeypatch.setattr("apps.adviser_v2.demo.views.demo_question.apply_async", lambda **kwargs: None)
    csrf = v2_client.cookies["csrftoken"].value
    data = {"session_id": str(session.id), "question": "Q", "plan_ids": [r.plan_key for r in rows[:2]]}
    response = v2_client.post("/api/v2/demo/questions/", data=json.dumps(data), content_type="application/json", HTTP_X_CSRFTOKEN=csrf)
    assert response.status_code == 202
    data["plan_ids"] = [rows[0].plan_key]*2
    assert v2_client.post("/api/v2/demo/questions/", data=json.dumps(data), content_type="application/json", HTTP_X_CSRFTOKEN=csrf).status_code == 400
    from apps.accounts.models import User
    outsider = User.objects.create_user(email="other-demo@example.com", password="Not-a-real-user-123")
    v2_client.force_login(outsider)
    assert v2_client.get(f"/api/v2/demo/questions/{response.json()['id']}/").status_code == 404
    assert len(v2_client.get("/api/v2/demo/coverage/").json()["insurers"]) == 10


def test_abandoned_question_recovers_without_repeating_completed_plans(v2_user, demo, monkeypatch):
    import uuid
    from datetime import timedelta
    _, session, rows = demo
    question = submit(v2_user, session.id, 'Q', [r.plan_key for r in rows[:2]])
    finished = question.answers.first()
    publish_progress(finished.id, 'not_found', {'status': 'not_found', 'models': ['gpt-5.6-luna']})
    old_token = uuid.uuid4()
    DemoQuestion.objects.filter(pk=question.id).update(state='running', execution_token=old_token,
                                                      heartbeat_at=timezone.now() - timedelta(minutes=6))
    calls = []
    def fake(bundle, text, *, method, progress):
        calls.append(bundle['policy_version_id'])
        progress('searching')
        return {'status': 'not_found', 'models': ['gpt-5.6-luna']}
    monkeypatch.setattr('apps.adviser_v2.demo.services.answer_plan', fake)
    run_question(question.id)
    question.refresh_from_db()
    assert question.state == 'completed' and len(calls) == 1
    assert question.execution_token != old_token
    assert not publish_progress(finished.id, 'answered', {'models': []}, execution_token=old_token)
