"""Ownership, immutable index pins and erasure-safe publication for demo questions."""

from __future__ import annotations

import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from pathlib import Path

from django.db import close_old_connections, transaction
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import User

from ..crypto import decrypt_bytes, encrypt_bytes
from ..models import DemoPlanAnswer, DemoPlanIndex, DemoQuestion, DemoRelease, DemoSession
from .answers import answer_plan
from .contracts import PlanCard, Profile
from .evidence import digest
from .matching import validate_selection
from .relay import AUDIT_CONTEXT


def encrypted(value: dict, identity) -> bytes:
    return encrypt_bytes(
        json.dumps(value, ensure_ascii=False).encode(), associated_data=str(identity).encode()
    )


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
        DemoQuestion.objects.filter(session=session).exclude(
            state__in=["completed", "cancelled"]
        ).update(state="cancelled", cancelled_at=timezone.now())
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
    item = DemoQuestion(
        id=uuid.uuid4(),
        session=session,
        release=release,
        profile_revision=session.profile_revision,
        erasure_generation=owner.erasure_generation,
    )
    item.input_ciphertext = encrypted({"question": question}, item.id)
    item.save()
    by_plan = {i.plan_key: i for i in indexes}
    DemoPlanAnswer.objects.bulk_create(
        [DemoPlanAnswer(question=item, index=by_plan[c.plan_id]) for c in selected]
    )
    return item


def usable(question: DemoQuestion) -> bool:
    return (
        question.state not in {"cancelled", "cancel_requested"}
        and question.cancelled_at is None
        and question.session.owner.is_active
        and question.session.owner.deleted_at is None
        and question.erasure_generation == question.session.owner.erasure_generation
        and (
            not question.profile_bound
            or question.profile_revision == question.session.profile_revision
        )
    )


@transaction.atomic
def publish_progress(answer_id, stage: str, value=None, *, execution_token=None) -> bool:
    # Same owner-first locking order as profile changes and account erasure.
    row = (
        DemoPlanAnswer.objects.select_related("question__session__owner", "index")
        .filter(pk=answer_id)
        .first()
    )
    if row is None:
        return False
    User.objects.select_for_update().get(pk=row.question.session.owner_id)
    row = (
        DemoPlanAnswer.objects.select_for_update()
        .select_related("question__session__owner", "index")
        .filter(pk=answer_id)
        .first()
    )
    if row is None or not usable(row.question) or row.index.revoked_at:
        return False
    if execution_token is not None and row.question.execution_token != execution_token:
        return False
    row.state = stage
    if value is not None:
        row.result_ciphertext = encrypted(value, row.id)
        row.model = value.get("models", [""])[-1] if value.get("models") else ""
        row.total_ms = value.get("total_ms", 0)
    row.save()
    return True


def run_question(question_id) -> None:
    question = (
        DemoQuestion.objects.select_related("session__owner", "release")
        .filter(pk=question_id)
        .first()
    )
    if question is None or not usable(question):
        return
    # Claim queued work or an abandoned lease. Old workers cannot publish after
    # recovery changes the execution token, including after erasure/cancellation.
    token = uuid.uuid4()
    stale = timezone.now() - timedelta(minutes=5)
    claimable = Q(state="queued") | (
        Q(state="running") & (Q(heartbeat_at__lt=stale) | Q(heartbeat_at__isnull=True))
    )
    if not DemoQuestion.objects.filter(claimable, pk=question_id).update(
        state="running", execution_token=token, heartbeat_at=timezone.now()
    ):
        return
    text = decrypted(question.input_ciphertext, question.id)["question"]
    from .answer_bank import QUESTION_TOPICS, remember

    topic = QUESTION_TOPICS.get(text)
    rows = list(question.answers.select_related("index").filter(result_ciphertext__isnull=True))
    close_old_connections()
    stop = threading.Event()

    def heartbeat():
        close_old_connections()
        try:
            while not stop.wait(20):
                alive = DemoQuestion.objects.filter(
                    pk=question_id, execution_token=token, state="running"
                ).update(heartbeat_at=timezone.now())
                close_old_connections()
                if not alive:
                    return
        finally:
            close_old_connections()

    pulse = threading.Thread(target=heartbeat, daemon=True)
    pulse.start()

    def plan(row):
        close_old_connections()
        audit_token = AUDIT_CONTEXT.set(
            {
                "question_id": str(question.id),
                "answer_id": str(row.id),
                "index_version": row.index_id,
                "method": question.release.method,
            }
        )
        try:

            def progress(stage):
                accepted = publish_progress(row.id, stage, execution_token=token)
                close_old_connections()
                if not accepted:
                    raise InterruptedError(
                        "Question cancelled, superseded, erased or source revoked."
                    )

            value = answer_plan(
                bundle_for(row.index), text, method=question.release.method, progress=progress
            )
            published = publish_progress(row.id, value["status"], value, execution_token=token)
            if published and topic:
                # A canonical topic answer depends on the wording only: keep it for reuse.
                remember(row.index, topic, question.release.method, value)
        except InterruptedError:
            return
        except (ValueError, OSError) as exc:
            publish_progress(
                row.id,
                "temporarily_unavailable",
                {"status": "temporarily_unavailable", "reason": str(exc), "models": []},
                execution_token=token,
            )
        finally:
            AUDIT_CONTEXT.reset(audit_token)
            close_old_connections()

    try:
        with ThreadPoolExecutor(max_workers=max(1, min(5, len(rows)))) as executor:
            for job in as_completed([executor.submit(plan, row) for row in rows]):
                job.result()
        DemoQuestion.objects.filter(pk=question_id, state="running", execution_token=token).update(
            state="completed", completed_at=timezone.now()
        )
    finally:
        stop.set()
        pulse.join(timeout=5)


def question_payload(question: DemoQuestion) -> dict:
    if not usable(question):
        return {"schema_version": 1, "id": str(question.id), "state": "cancelled", "plans": []}
    from .answer_bank import QUESTION_TOPICS, TERMS, group

    asked = decrypted(question.input_ciphertext, question.id)
    topic = QUESTION_TOPICS.get(asked["question"])
    verdicts = asked.get("verdicts") or {}
    plans = []
    for row in question.answers.select_related("index").order_by(
        "index__insurer", "index__name", "index__variant"
    ):
        result = None
        if row.result_ciphertext and row.index.revoked_at is None:
            result = decrypted(row.result_ciphertext, row.id)
            result.pop(
                "packet", None
            )  # Source packets stay server-side; selected exact quotes are returned.
            result.pop("attempts", None)  # Rejected candidate wording must never be displayed.
        # Where the validated wording puts a topic: base, addon, excluded, not_found. An
        # answer that couldn't be read stays ungrouped with its own message.
        final = bool(topic and result and result.get("status") in {"answered", "not_found"})
        found = group(result, topic, row.index.variant) if final else None
        card = verdicts.get(row.index.plan_key)
        if card and result:
            # A cited fact-card rule or add-on decides, as it does for the plan list; its
            # quotes are shown when the stored answer says otherwise or nothing, or when
            # they are an add-on extending what the base cover has.
            own = card["statements"]
            extends = all(s.get("coverage_scope") == "optional, extra premium" for s in own)
            found, card = card["group"], (own if found != card["group"] or extends else None)
        else:
            card = None
        plans.append(
            {
                "id": str(row.id),
                "plan_id": row.index.plan_key,
                "index_version": row.index_id,
                "name": row.index.name,
                "variant": row.index.variant,
                "insurer": row.index.insurer,
                "plan_type": row.index.plan_type,
                "state": "source_revoked" if row.index.revoked_at else row.state,
                "model": row.model,
                "result": result,
                "group": found,
                # Statements quoted from the plan's fact card; their sources open as card
                # citations.
                "card_statements": card,
            }
        )
    return {
        "schema_version": 1,
        "id": str(question.id),
        "state": question.state,
        "topic": topic,
        # A term every plan states (a waiting period, a co-pay) rather than a benefit.
        "terms": topic in TERMS,
        "plans": plans,
    }
