"""Serialize customer changes; keep independent plan answers parallel and pinned."""

import re
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
from .answer_bank import (
    SYNONYMS,
    TERMS,
    TOPIC_LABELS,
    TOPIC_QUESTIONS,
    bank_groups,
    card_quotes,
    group,
    lookup,
    statements,
)
from .chat_rules import fit_groups, remaining_ids, topic_verdict, waiting_months
from .conversation import (
    GROUP_ORDER,
    interpret,
    join_words,
    need_label,
    next_question,
    plan_name,
    plural,
    summary,
    transition,
)
from .conversation_contracts import ChatState
from .price_compare import premium, short_insurer
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
                optional_covers={},
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


def attach_groups(cards, release):
    """Label each card with where its validated wording puts every answered topic."""
    ids = {i.plan_key: i.id for i in release.indexes.filter(revoked_at__isnull=True)}
    found = bank_groups(ids.values(), release.method)
    for card in cards:
        card["bank_groups"] = found.get(ids.get(card["plan_id"]), {})
    return cards


def title_identity(conversation):
    return f"{conversation.id}:title"


def history(owner):
    """The owner's conversations with at least one customer turn, newest first."""
    rows = DemoConversation.objects.filter(session__owner=owner, revision__gt=0).order_by(
        "-updated_at"
    )
    return [
        {
            "id": str(row.id),
            "title": decrypted(row.title_ciphertext, title_identity(row))["text"]
            if row.title_ciphertext
            else "Conversation",
            "updated_at": row.updated_at.isoformat(),
        }
        for row in rows
    ]


SUGGESTIONS = {
    "people": ["Just me", "Me and my spouse"],
    "sum_insured": ["5 lakh", "10 lakh", "25 lakh", "Not sure", "What are the options?"],
    "annual_budget": ["Not sure"],
    "coverage_basis": ["One shared cover", "Separate cover each", "Not sure"],
    "needs": ["OPD", "Maternity", "No co-pay", "Skip"],
    "strength": ["Must-have", "Nice-to-have"],
    "narrow": ["Yes", "No"],
    "health_details": ["Skip"],
    "batch": ["Show more", "Compare premiums"],
    "which_limit": ["Room rent", "Co-pay", "Disease sub-limits"],
    "limit_question": ["Room rent", "Co-pay", "Disease sub-limits"],
}
for _template in ("exhausted", "batch_end", "few", "after_price"):
    SUGGESTIONS[_template] = ["Compare premiums", "No, that’s all"]
SUGGESTIONS["closing"] = ["Compare premiums"]


def suggestions(state):
    """Short replies the customer can tap for the pending question; never a plan choice."""
    asked = state.pending
    chips = list(SUGGESTIONS.get(asked.template, [])) if asked else []
    if state.question_id and state.topic_reason == "question" and state.last_topic:
        # Follow-ups to a question answered from the stored answers.
        extra = ["Ask exactly my question"]
        if state.last_topic not in TERMS and "base" in state.topic_groups.values():
            extra.insert(0, "Show the plans with it in the base cover")
        chips = [*extra, *chips]
    if state.question_id and state.batch_queue and state.batch_question:
        # Offered on the turn a group of five is read, not on every turn after it.
        chips = ["Ask the next 5", *chips]
    return chips


def turn_blocks(state, before, cards):
    """Tables to draw inside this turn's assistant message, snapshotted for history."""
    by_id = {c["plan_id"]: c for c in cards}
    fits = {
        r["plan_id"]: r for key in ("fits", "unresolved") for r in state.fit_groups.get(key, [])
    }
    blocks = []
    if state.shown_plans:
        # One column per checkable customer need, in the order they were given.
        needs = [r for r in state.profile.requirements if not r.field.startswith("unsupported:")]
        rows = []
        for plan_id in state.shown_plans:
            card, fit = by_id.get(plan_id), fits.get(plan_id)
            if not card:
                continue
            reasons = [*fit["hard_limits"], *fit["other_needs"]] if fit else []
            by_field = {r["field"]: r for r in fit["other_needs"]} if fit else {}
            amount = premium(card, state.profile)
            rows.append(
                {
                    "plan_id": plan_id,
                    "insurer": short_insurer(card["insurer"]),
                    "name": card["name"],
                    "variant": card["variant"],
                    "plan_type": card["plan_type"],
                    "confirmed": bool(fit) and fit["status"] == "fits",
                    "citations": [
                        c for r in reasons if r["status"] == "fits" for c in r["citations"]
                    ],
                    "needs": [
                        {
                            "field": n.field,
                            "status": by_field.get(n.field, {}).get("status", "unresolved"),
                            # Two quotes per cell; the source panel shows the rest.
                            "citations": by_field.get(n.field, {}).get("citations", [])[:2],
                            # A wait shown for information reads as its months; otherwise
                            # the label says where the wording puts it.
                            **(
                                {"detail": f"{months} months"}
                                if n.value == "shown"
                                and (months := waiting_months(card, n, state.profile)) is not None
                                else {"detail": detail}
                                if (detail := by_field.get(n.field, {}).get("detail"))
                                else {}
                            ),
                        }
                        for n in needs
                    ],
                    "premium": f"{amount:,}" if amount is not None else None,
                }
            )
        blocks.append(
            {
                "type": "shortlist",
                "needs": [{"field": n.field, "label": need_label(n)} for n in needs],
                "plans": rows,
            }
        )
    if state.question_id and state.question_id != before.question_id:
        blocks.append({"type": "question", "question_id": state.question_id})
    if state.price and state.price != before.price:
        blocks.append({"type": "price", "plan_id": state.price_plan, **state.price})
    if state.price_comparison and state.price_comparison != before.price_comparison:
        blocks.append({"type": "price_comparison", **state.price_comparison})
    return blocks


def payload(conversation, state=None):
    state = state or ChatState.model_validate(
        decrypted(conversation.state_ciphertext, conversation.id)
    )
    cards = attach_groups(release_cards(conversation.release), conversation.release)
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
    cards = attach_groups(release_cards(release), release)
    state.source_indexes = sorted({c["index_version"] for c in cards})
    state.fit_groups = fit_groups(cards, state.profile)
    state.understanding = summary(state.profile)
    next_question(state, cards)
    state.transcript.append(
        {
            "role": "assistant",
            "text": state.message,
            "understanding": state.understanding,
            "suggestions": suggestions(state),
        }
    )
    session.profile_ciphertext = encrypted(state.profile.model_dump(), session.id)
    session.save()
    conversation = DemoConversation(id=uuid.uuid4(), session=session, release=release)
    conversation.state_ciphertext = encrypted(state.model_dump(), conversation.id)
    conversation.save()
    return payload(conversation, state)


def new_question(owner, conversation, text, verdicts=None):
    # Answers never read the profile, so a later profile change leaves them readable.
    q = DemoQuestion(
        id=uuid.uuid4(),
        session=conversation.session,
        release=conversation.release,
        profile_revision=conversation.session.profile_revision,
        erasure_generation=owner.erasure_generation,
        profile_bound=False,
    )
    asked = {"question": text}
    if verdicts:
        # Where each plan's fact card puts the topic, with its quotes; see topic_verdict.
        asked["verdicts"] = verdicts
    q.input_ciphertext = encrypted(asked, q.id)
    q.save()
    return q


def submit_policy(owner, conversation, state, cards):
    selected = state.asked_plans
    state.asked_plans = []
    chosen = [c for c in cards if c["plan_id"] in selected]
    if not 1 <= len(chosen) <= 5 or len(chosen) != len(set(selected)):
        state.policy_question = None
        return None
    if len({c["plan_type"] for c in chosen}) != 1 or chosen[0]["plan_type"] == "unresolved":
        return None
    indexes = {i.plan_key: i for i in conversation.release.indexes.filter(revoked_at__isnull=True)}
    if any(c["plan_id"] not in indexes for c in chosen):
        return None
    q = new_question(owner, conversation, state.policy_question)
    DemoPlanAnswer.objects.bulk_create(
        [DemoPlanAnswer(question=q, index=indexes[c["plan_id"]]) for c in chosen]
    )
    state.policy_question = None
    state.question_id = str(q.id)
    return q


def submit_topic(owner, conversation, state, cards):
    """Answer a whole-benefit question for the asked plans from the engine's stored answers.

    The customer's question is stored as the canonical topic question, so citations,
    erasure and live updates work as for any question. Only plans without a stored
    answer are read live; a need or a shared illness shows stored answers only, so the
    reply never waits."""
    topic, reason = state.policy_topic, state.topic_reason
    asked, state.asked_plans = state.asked_plans, []
    # A newer table replaces a question still being read in groups of five.
    state.batch_queue, state.batch_question = [], None
    state.policy_question = state.policy_topic = None
    release = conversation.release
    indexes = {i.plan_key: i for i in release.indexes.filter(revoked_at__isnull=True)}
    chosen = [c for c in cards if c["plan_id"] in asked and c["plan_id"] in indexes]
    stored = lookup(
        [indexes[c["plan_id"]] for c in chosen],
        topic,
        release.method,
        siblings=[i.id for i in indexes.values()],
    )
    if reason != "question":
        chosen = [c for c in chosen if indexes[c["plan_id"]].id in stored]
    if not chosen:
        return None
    # One answer per plan: a cited fact-card rule or add-on decides as it does for the
    # plan list, then the stored answer; the table and the counts below both use it.
    verdicts, groups = {}, {}
    for card in chosen:
        index = indexes[card["plan_id"]]
        result = stored.get(index.id)
        banked = group(result, topic, index.variant) if result else None
        decided, quoted = topic_verdict(card, topic, banked, state.profile)
        if quoted:
            shown = card_quotes(quoted, topic)
            verdicts[card["plan_id"]] = {"group": decided, "statements": shown}
        if result:
            groups[card["plan_id"]] = decided
    q = new_question(owner, conversation, TOPIC_QUESTIONS[topic], verdicts)
    rows, results = [], {}
    for card in chosen:
        index = indexes[card["plan_id"]]
        row = DemoPlanAnswer(id=uuid.uuid4(), question=q, index=index)
        result = stored.get(index.id)
        if result:
            row.state = result["status"]
            row.result_ciphertext = encrypted(result, row.id)
            row.model = (result.get("models") or [""])[-1][:80]
            row.total_ms = result.get("total_ms", 0)
            results[card["plan_id"]] = result
        rows.append(row)
    DemoPlanAnswer.objects.bulk_create(rows)
    if len(results) == len(rows):
        q.state, q.completed_at = "completed", timezone.now()
        q.save(update_fields=["state", "completed_at"])
    state.question_id = str(q.id)
    state.last_topic = topic
    state.topic_groups = dict(sorted(groups.items(), key=lambda item: GROUP_ORDER[item[1]]))
    every = set(asked) == remaining_ids(state.fit_groups)
    text = topic_reply(state, topic, reason, chosen, results, groups, every=every)
    asked_text = state.pending.text if state.pending else ""
    if reason != "question" and asked_text and state.message.endswith(asked_text):
        # A need's evidence comes just before the question about it.
        state.message = f"{state.message[: -len(asked_text)]}{text} {asked_text}"
    else:
        state.message = f"{text} {state.message}".strip()
    return q


def specific_words(topic, text):
    """The customer's own term for a topic when it is narrower than the topic's name,
    such as "helicopter" for air ambulance, as a pattern; else None."""
    pattern = SYNONYMS.get(topic)
    if not pattern:
        return None
    for part in top_level(pattern):
        if re.search(part, text, re.I) and not re.search(part, TOPIC_LABELS[topic], re.I):
            return part
    return None


def top_level(pattern):
    """A pattern's top-level alternatives."""
    parts, depth, start = [], 0, 0
    for i, ch in enumerate(pattern):
        if ch == "\\":
            continue
        if ch == "(" and (i == 0 or pattern[i - 1] != "\\"):
            depth += 1
        elif ch == ")" and pattern[i - 1] != "\\":
            depth -= 1
        elif ch == "|" and depth == 0 and pattern[i - 1] != "\\":
            parts.append(pattern[start:i])
            start = i + 1
    return [*parts, pattern[start:]]


def counted(n, one, many):
    return f"{n} {one if n == 1 else many}"


def topic_reply(state, topic, reason, chosen, results, groups, *, every=True):
    """What the documents say, counted by where each plan's answer puts the topic."""
    label = TOPIC_LABELS[topic]
    if reason == "health":
        return "Each plan’s own wording on pre-existing diseases is quoted in the table below."
    counts = {g: 0 for g in GROUP_ORDER}
    for found in groups.values():
        counts[found] += 1
    waiting = len(chosen) - len(results)
    total = len(chosen)
    if total == 1:
        of = "Of the plan " + ("open to you" if every else "you asked about")
    else:
        of = f"Of the {total} plans " + ("open to you" if every else "you asked about")
    parts = []
    if topic in TERMS:
        if counts["base"]:
            parts.append(counted(counts["base"], "states", "state") + f" terms for {label}")
        if counts["not_found"]:
            parts.append(counted(counts["not_found"], "doesn’t state them", "don’t state them"))
        lead = f"{of}, " + join_words(parts) + "." if parts else ""
        if counts["addon"]:
            lead += " " + counted(
                counts["addon"],
                "plan offers an optional add-on that changes them",
                "plans offer an optional add-on that changes them",
            )
            lead += ", for an extra premium."
    else:
        if counts["base"]:
            parts.append(
                counted(counts["base"], "includes it", "include it") + " in the base cover"
            )
        if counts["addon"]:
            parts.append(
                counted(counts["addon"], "offers it", "offer it")
                + " only as an optional add-on (extra premium)"
            )
        if counts["excluded"]:
            parts.append(
                counted(counts["excluded"], "says it isn’t covered", "say it isn’t covered")
            )
        if counts["not_found"]:
            parts.append(counted(counts["not_found"], "doesn’t mention it", "don’t mention it"))
        lead = f"{of}, " + join_words(parts) + "." if parts else ""
        if reason != "need":
            # The answer names the benefit the question was read as.
            lead = re.sub(r"\bit\b", label, lead, count=1)
    if reason == "need" and lead:
        lead = f"{label[0].upper()}{label[1:]}: {lead[0].lower()}{lead[1:]}"
    sentences = [lead] if lead else []
    words = specific_words(topic, state.topic_original or "") if reason == "question" else None
    if words:
        # The customer used a narrower word than the benefit's name, such as helicopter.
        sentences.insert(0, f"I’ve read this as a question about {label}.")
        named, word = [], None
        for card in chosen:
            for statement in statements(results.get(card["plan_id"])):
                text = " ".join(
                    part.get("text", "") for part in [statement, *statement.get("conditions", [])]
                )
                if found := re.search(words, text, re.I):
                    named.append(plan_name(card))
                    word = word or found.group(0).lower()
                    break
        if named:
            only = "Only the" if len(named) < len(results) else "The"
            sentences.append(
                f"{only} wording of {join_words(named)} "
                f"{'mentions' if len(named) == 1 else 'mention'} “{word}” by name."
            )
    if waiting:
        sentences.append(
            f"I’m still reading the documents of {plural(waiting, 'plan')}; "
            "their answers will appear in the table."
        )
    if counts["base"] or counts["addon"]:
        sentences.append("Limits and conditions differ, so check each plan’s quote below.")
    if counts["not_found"] and topic not in TERMS:
        sentences.append("A plan that doesn’t mention it isn’t necessarily excluding it.")
    return " ".join(sentences)


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
    prior = state.model_copy(deep=True)
    state.shown_plans = []
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
    cards = attach_groups(release_cards(conversation.release), conversation.release)
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
    q = None
    if state.policy_question and not state.policy_deferred and state.stage != "stopped":
        submit = submit_topic if state.policy_topic else submit_policy
        q = submit(owner, conversation, state, cards)
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
            {
                "role": "assistant",
                "text": state.message,
                "understanding": state.understanding,
                "blocks": turn_blocks(state, prior, cards),
                "suggestions": suggestions(state),
            },
        ]
    )
    conversation.state_ciphertext = encrypted(state.model_dump(), conversation.id)
    fields = ["revision", "state_ciphertext", "updated_at"]
    if not conversation.title_ciphertext:
        conversation.title_ciphertext = encrypted(
            {"text": " ".join(text.split())[:60]}, title_identity(conversation)
        )
        fields.append("title_ciphertext")
    conversation.save(update_fields=fields)
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
    if q and q.state == "queued" and dispatch:
        from .tasks import demo_question

        transaction.on_commit(
            lambda: demo_question.apply_async(args=[str(q.id)], queue="demo_live")
        )
    return result
