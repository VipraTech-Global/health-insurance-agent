"""Serialize customer changes; keep independent plan answers parallel and pinned."""

import time
import uuid

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User

from ..models import (
    DemoChatTurn,
    DemoConversation,
    DemoPlanAnswer,
    DemoQuestion,
    DemoRelease,
    DemoSession,
)
from .chat_rules import fit_groups, remaining_ids
from .conversation import interpret, next_question, summary, transition
from .conversation_contracts import ChatState
from .relay import AUDIT_CONTEXT, InvalidOutput, Relay, RelayUnavailable
from .services import decrypted, encrypted


class StaleTurn(ValueError):
    pass


def release_cards(release):
    if hasattr(release, "fact_cards") and release.fact_cards.exists():
        rows = list(release.fact_cards.select_related("index"))
        pairs = [(r.index, {**r.card, "card_version": r.id}) for r in rows]
    else:
        pairs = [(i, dict(i.card)) for i in release.indexes.all()]
    cards = []
    for index, card in pairs:
        if index.revoked_at:
            card.update(
                status="documents_unavailable",
                entry_ages=[],
                renewal_ages=[],
                family_rule=None,
                executable_rules=[],
                common_needs=[],
            )
            for field in (
                "sum_insured",
                "geography",
                "copay",
                "room_limit",
                "ped_waiting",
                "maternity",
                "opd",
            ):
                card[field] = {"state": "not_stated"}
        cards.append(card)
    return sorted(
        cards,
        key=lambda c: (
            c["insurer"].casefold(),
            c["name"].casefold(),
            c["variant"].casefold(),
            c["plan_id"],
        ),
    )


def payload(conversation, state=None):
    state = state or ChatState.model_validate(
        decrypted(conversation.state_ciphertext, conversation.id)
    )
    cards = release_cards(conversation.release)
    state.fit_groups = fit_groups(cards, state.profile)
    return {
        "schema_version": 2,
        "id": str(conversation.id),
        "session_id": str(conversation.session_id),
        "release_id": str(conversation.release_id),
        "cards": [
            {
                k: v
                for k, v in c.items()
                if k
                in {
                    "plan_id",
                    "index_version",
                    "card_version",
                    "insurer",
                    "name",
                    "variant",
                    "plan_type",
                    "status",
                    "field_coverage",
                    "rule_coverage",
                }
            }
            for c in cards
        ],
        "state": state.model_dump(),
    }


@transaction.atomic
def start(owner, *, release_id=None):
    owner = User.objects.select_for_update().get(pk=owner.pk)
    if not owner.is_active or owner.deleted_at:
        raise ValueError("This account is unavailable.")
    release = (
        DemoRelease.objects.get(pk=release_id)
        if release_id
        else DemoRelease.objects.get(active=True)
    )
    session = DemoSession(id=uuid.uuid4(), owner=owner)
    state = ChatState()
    cards = release_cards(release)
    state.source_indexes = sorted({c["index_version"] for c in cards})
    state.fit_groups = fit_groups(cards, state.profile)
    state.understanding = summary(state.profile)
    next_question(state, cards)
    state.transcript.append(
        {"role": "assistant", "text": state.message, "understanding": state.understanding}
    )
    session.profile_ciphertext = encrypted(state.profile.model_dump(), session.id)
    session.save()
    conversation = DemoConversation(id=uuid.uuid4(), session=session, release=release)
    conversation.state_ciphertext = encrypted(state.model_dump(), conversation.id)
    conversation.save()
    return payload(conversation, state)


def submit_policy(owner, conversation, state, cards):
    selected = state.selected_plans or sorted(remaining_ids(state.fit_groups))
    chosen = [c for c in cards if c["plan_id"] in selected]
    if not 1 <= len(chosen) <= 5 or len(chosen) != len(set(selected)):
        return None
    if len({c["plan_type"] for c in chosen}) != 1 or chosen[0]["plan_type"] == "unresolved":
        return None
    indexes = {i.plan_key: i for i in conversation.release.indexes.filter(revoked_at__isnull=True)}
    if any(c["plan_id"] not in indexes for c in chosen):
        return None
    q = DemoQuestion(
        id=uuid.uuid4(),
        session=conversation.session,
        release=conversation.release,
        profile_revision=conversation.session.profile_revision,
        erasure_generation=owner.erasure_generation,
    )
    q.input_ciphertext = encrypted({"question": state.policy_question}, q.id)
    q.save()
    DemoPlanAnswer.objects.bulk_create(
        [DemoPlanAnswer(question=q, index=indexes[c["plan_id"]]) for c in chosen]
    )
    state.policy_question = None
    state.question_id = str(q.id)
    return q


@transaction.atomic
def commit_turn(owner, conversation_id, *, request_id, revision, text, relay=None, dispatch=True):
    tick = time.monotonic()
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 3000:
        raise ValueError("Enter a message of 1–3000 characters.")
    owner = User.objects.select_for_update().get(pk=owner.pk)
    if not owner.is_active or owner.deleted_at:
        raise ValueError("This account is unavailable.")
    conversation = (
        DemoConversation.objects.select_for_update()
        .select_related("session", "release")
        .get(pk=conversation_id, session__owner=owner)
    )
    previous = conversation.receipts.filter(request_id=request_id).first()
    if previous:
        if decrypted(previous.input_ciphertext, previous.id) != {
            "text": text,
            "revision": revision,
        }:
            raise StaleTurn("This submission ID was already used for a different message.")
        if conversation.release.indexes.filter(revoked_at__isnull=False).exists():
            raise StaleTurn(
                "A source has been revoked; refresh the conversation before continuing."
            )
        return decrypted(previous.output_ciphertext, previous.id)
    if conversation.revision != revision:
        raise StaleTurn(
            "A newer turn has already changed this conversation; refresh before replying."
        )
    state = ChatState.model_validate(decrypted(conversation.state_ciphertext, conversation.id))
    stopping = text.strip().casefold().rstrip(".!") in {
        "stop",
        "stop please",
        "stop asking",
        "i want to stop",
        "end conversation",
        "done",
    }
    if (
        state.question_id
        and DemoQuestion.objects.filter(pk=state.question_id)
        .exclude(state__in=["completed", "cancelled"])
        .exists()
    ):
        if not stopping:
            raise StaleTurn(
                "The policy comparison is still answering; cancel it or wait before the next reply."
            )
        DemoQuestion.objects.filter(pk=state.question_id).update(
            state="cancelled", cancelled_at=timezone.now()
        )
    if state.stage == "stopped":
        raise ValueError("Guided questions have stopped; start a new conversation to continue.")
    cards = release_cards(conversation.release)
    before = state.profile.model_dump()
    model = None
    token = AUDIT_CONTEXT.set(
        {
            "conversation_id": str(conversation.id),
            "revision": revision + 1,
            "request_id": str(request_id),
        }
    )
    try:
        changes, model = interpret(text, state, cards, relay=relay)
        allowed = {c["plan_id"] for c in cards}
        if set(changes.selected_plans + changes.restored_plans) - allowed:
            raise InvalidOutput("A proposed comparison is outside the pinned release.")
        state = transition(state, changes, cards, relay=relay or Relay.configured())
    except (RelayUnavailable, InvalidOutput, ValueError) as exc:
        # Preserve every established fact and the same pending question.
        state.message = "I could not interpret that reply right now. " + (
            state.pending.text if state.pending else "Would you like to try that reply again?"
        )
        state.stop_reason = None
        failure = type(exc).__name__
    else:
        failure = None
    finally:
        AUDIT_CONTEXT.reset(token)
    if model:
        state.models.append(model)
    if before != state.profile.model_dump():
        session = conversation.session
        session.profile_revision += 1
        session.profile_ciphertext = encrypted(state.profile.model_dump(), session.id)
        session.save(update_fields=["profile_revision", "profile_ciphertext"])
        DemoQuestion.objects.filter(session=session).exclude(
            state__in=["completed", "cancelled"]
        ).update(state="cancelled", cancelled_at=timezone.now())
    q = (
        submit_policy(owner, conversation, state, cards)
        if state.policy_question and not state.policy_deferred
        else None
    )
    if state.price_plan and state.stage != "stopped":
        from .chat_prices import price_step

        price_step(state, cards)
    elapsed = round((time.monotonic() - tick) * 1000)
    conversation.revision += 1
    state.revision = conversation.revision
    state.turns.append(
        {
            "revision": state.revision,
            "stage": state.stage,
            "elapsed_ms": elapsed,
            "counts": {k: len(v) for k, v in state.fit_groups.items()},
            "question_count": state.question_count,
            "question": state.pending.model_dump() if state.pending else None,
            "stop_reason": state.stop_reason,
            "model": model,
            "failure": failure,
        }
    )
    state.transcript.extend(
        [
            {"role": "customer", "text": text},
            {"role": "assistant", "text": state.message, "understanding": state.understanding},
        ]
    )
    conversation.state_ciphertext = encrypted(state.model_dump(), conversation.id)
    conversation.save(update_fields=["revision", "state_ciphertext"])
    result = payload(conversation, state)
    receipt = DemoChatTurn(
        id=uuid.uuid4(),
        conversation=conversation,
        request_id=request_id,
        base_revision=revision,
        elapsed_ms=elapsed,
    )
    receipt.input_ciphertext = encrypted({"text": text, "revision": revision}, receipt.id)
    receipt.output_ciphertext = encrypted(result, receipt.id)
    receipt.save()
    if q and dispatch:
        from .tasks import demo_question

        transaction.on_commit(
            lambda: demo_question.apply_async(args=[str(q.id)], queue="demo_live")
        )
    return result
