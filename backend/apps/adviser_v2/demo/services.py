"""Ownership, immutable index pins and erasure-safe publication for demo questions."""

from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from django.db import close_old_connections, transaction
from django.utils import timezone

from apps.accounts.models import User

from ..crypto import decrypt_bytes, encrypt_bytes
from ..models import DemoPlanAnswer, DemoPlanIndex, DemoQuestion, DemoRelease, DemoSession
from .answers import answer_plan
from .contracts import PlanCard, Profile
from .evidence import digest
from .matching import validate_selection


def encrypted(value: dict, identity) -> bytes:
    return encrypt_bytes(json.dumps(value, ensure_ascii=False).encode(), associated_data=str(identity).encode())


def decrypted(value, identity) -> dict:
    return json.loads(decrypt_bytes(bytes(value), associated_data=str(identity).encode()))


def bundle_for(index: DemoPlanIndex) -> dict:
    if index.revoked_at:
        raise ValueError("This plan's source index was revoked.")
    bundle = json.loads(Path(index.bundle_path).read_text())
    if digest({k: v for k, v in bundle.items() if k != "index_id"}) != index.id:
        raise ValueError("The pinned plan-index content no longer matches its hash.")
    return bundle


@transaction.atomic
def save_profile(owner: User, profile: Profile, session_id=None) -> DemoSession:
    owner = User.objects.select_for_update().get(pk=owner.pk)
    if not owner.is_active or owner.deleted_at:
        raise ValueError("This account is unavailable.")
    if session_id:
        session = DemoSession.objects.select_for_update().get(pk=session_id, owner=owner)
        session.profile_revision += 1
        DemoQuestion.objects.filter(session=session).exclude(state__in=["completed", "cancelled"]).update(
            state="cancelled", cancelled_at=timezone.now())
    else:
        session = DemoSession(id=uuid.uuid4(), owner=owner)
    profile = profile.model_copy(update={"revision": session.profile_revision})
    session.profile_ciphertext = encrypted(profile.model_dump(), session.id)
    session.save()
    return session


@transaction.atomic
def submit(owner: User, session_id, question: str, plan_ids: list[str]) -> DemoQuestion:
    owner = User.objects.select_for_update().get(pk=owner.pk)
    if not owner.is_active or owner.deleted_at:
        raise ValueError("This account is unavailable.")
    session = DemoSession.objects.select_for_update().get(pk=session_id, owner=owner)
    release = DemoRelease.objects.get(active=True)
    indexes = list(release.indexes.filter(revoked_at__isnull=True))
    cards = [PlanCard.model_validate(i.card) for i in indexes]
    selected = validate_selection(cards, plan_ids)
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 3000:
        raise ValueError("Enter a question of 1–3000 characters.")
    item = DemoQuestion(id=uuid.uuid4(), session=session, release=release,
        profile_revision=session.profile_revision, erasure_generation=owner.erasure_generation)
    item.input_ciphertext = encrypted({"question": question}, item.id)
    item.save()
    by_plan = {i.plan_key: i for i in indexes}
    DemoPlanAnswer.objects.bulk_create([DemoPlanAnswer(question=item, index=by_plan[c.plan_id]) for c in selected])
    return item


def usable(question: DemoQuestion) -> bool:
    return (question.state not in {"cancelled", "cancel_requested"} and question.cancelled_at is None
            and question.session.owner.is_active and question.session.owner.deleted_at is None
            and question.erasure_generation == question.session.owner.erasure_generation
            and question.profile_revision == question.session.profile_revision)


@transaction.atomic
def publish_progress(answer_id, stage: str, value=None) -> bool:
    # Same owner-first locking order as profile changes and account erasure.
    row = DemoPlanAnswer.objects.select_related("question__session__owner", "index").filter(pk=answer_id).first()
    if row is None:
        return False
    User.objects.select_for_update().get(pk=row.question.session.owner_id)
    row = DemoPlanAnswer.objects.select_for_update().select_related("question__session__owner", "index").filter(pk=answer_id).first()
    if row is None or not usable(row.question) or row.index.revoked_at:
        return False
    row.state = stage
    if value is not None:
        row.result_ciphertext = encrypted(value, row.id)
        row.model = value.get("models", [""])[-1] if value.get("models") else ""
        row.total_ms = value.get("total_ms", 0)
    row.save()
    return True


def run_question(question_id) -> None:
    question = DemoQuestion.objects.select_related("session__owner", "release").filter(pk=question_id).first()
    if question is None or not usable(question):
        return
    # Claim once. A duplicate queue delivery cannot duplicate the relay chains.
    if not DemoQuestion.objects.filter(pk=question_id, state="queued").update(state="running"):
        return
    text = decrypted(question.input_ciphertext, question.id)["question"]
    rows = list(question.answers.select_related("index"))

    def plan(row):
        close_old_connections()
        try:
            def progress(stage):
                if not publish_progress(row.id, stage):
                    raise InterruptedError("Question cancelled, superseded, erased or source revoked.")

            value = answer_plan(bundle_for(row.index), text, method=question.release.method, progress=progress)
            publish_progress(row.id, value["status"], value)
        except InterruptedError:
            return
        except (ValueError, OSError) as exc:
            publish_progress(row.id, "temporarily_unavailable", {"status": "temporarily_unavailable", "reason": str(exc), "models": []})
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=min(5, len(rows))) as executor:
        for job in as_completed([executor.submit(plan, row) for row in rows]):
            job.result()
    DemoQuestion.objects.filter(pk=question_id, state="running").update(state="completed", completed_at=timezone.now())


def question_payload(question: DemoQuestion) -> dict:
    if not usable(question):
        return {"schema_version": 1, "id": str(question.id), "state": "cancelled", "plans": []}
    plans = []
    for row in question.answers.select_related("index").order_by("index__insurer", "index__name", "index__variant"):
        result = None
        if row.result_ciphertext and row.index.revoked_at is None:
            result = decrypted(row.result_ciphertext, row.id)
            result.pop("packet", None)  # Source packets stay server-side; selected exact quotes are returned.
            result.pop("attempts", None)  # Rejected candidate wording must never be displayed.
        plans.append({"id": str(row.id), "plan_id": row.index.plan_key, "index_version": row.index_id,
                      "name": row.index.name, "plan_type": row.index.plan_type,
                      "state": "source_revoked" if row.index.revoked_at else row.state,
                      "model": row.model, "result": result})
    return {"schema_version": 1, "id": str(question.id), "state": question.state, "plans": plans}
