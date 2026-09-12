import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .corpus import lock_corpus_publication
from .evidence import validate_evidence_span
from .models import (
    AIPreference,
    AnswerArtifact,
    AnswerClaim,
    Conversation,
    CorpusRelease,
    Message,
    ProfileRevision,
    RecommendationSnapshot,
    Turn,
    TurnAttempt,
    VerifiedFact,
)
from .relay_routes import selected_route
from .source_maps import DocumentValidationError


class ConflictError(Exception):
    pass


class OwnershipError(Exception):
    pass


@dataclass(frozen=True)
class AcceptedTurn:
    turn_id: str
    attempt_id: str
    profile_revision: int | None
    existing: bool
    terminal_answer_id: str | None
    attempt_status: str


def owned_conversation(
    user_id: uuid.UUID, conversation_id: uuid.UUID, *, lock: bool = False
) -> Conversation:
    query = Conversation.objects.all()
    if lock:
        query = query.select_for_update()
    else:
        query = query.select_related("current_profile")
    try:
        return query.get(id=conversation_id, owner_id=user_id)
    except Conversation.DoesNotExist as exc:
        raise OwnershipError from exc


def create_conversation(user_id: uuid.UUID, title: str = "New conversation") -> Conversation:
    with transaction.atomic():
        conversation = Conversation.objects.create(
            owner_id=user_id, title=title[:200] or "New conversation"
        )
        profile = ProfileRevision.objects.create(
            conversation=conversation, revision=1, data={}, field_provenance={}
        )
        conversation.current_profile = profile
        conversation.save(update_fields=["current_profile", "updated_at"])
    return conversation


def revise_profile(
    user_id: uuid.UUID, conversation_id: uuid.UUID, expected_revision: int, patch: dict[str, Any]
) -> ProfileRevision:
    with transaction.atomic():
        conversation = owned_conversation(user_id, conversation_id, lock=True)
        current = conversation.current_profile
        if current is None or current.revision != expected_revision:
            raise ConflictError("The profile changed. Reload it before saving.")
        data = {**current.data, **patch}
        provenance = {
            **current.field_provenance,
            **{key: {"state": "supplied", "confirmed": False} for key in patch},
        }
        revision = ProfileRevision.objects.create(
            conversation=conversation,
            revision=current.revision + 1,
            data=data,
            field_provenance=provenance,
        )
        conversation.current_profile = revision
        conversation.save(update_fields=["current_profile", "updated_at"])
        TurnAttempt.objects.filter(
            turn__conversation=conversation, status__in=TurnAttempt.ACTIVE
        ).update(status=TurnAttempt.Status.SUPERSEDED, terminal_code="profile_changed")
        conversation.active_attempt = None
        conversation.save(update_fields=["active_attempt", "updated_at"])
    return revision


def confirm_profile(
    user_id: uuid.UUID, conversation_id: uuid.UUID, expected_revision: int
) -> ProfileRevision:
    with transaction.atomic():
        conversation = owned_conversation(user_id, conversation_id, lock=True)
        profile = conversation.current_profile
        if profile is None or profile.revision != expected_revision:
            raise ConflictError("The profile changed. Reload it before confirming.")
        if profile.confirmed_at is None:
            profile.confirmed_at = timezone.now()
            profile.field_provenance = {
                key: {**value, "confirmed": True} for key, value in profile.field_provenance.items()
            }
            profile.save(update_fields=["confirmed_at", "field_provenance"])
    return profile


def accept_turn(
    user_id: uuid.UUID, conversation_id: uuid.UUID, payload: dict[str, Any]
) -> AcceptedTurn:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload_hash = hashlib.sha256(canonical.encode()).hexdigest()
    request_id = uuid.UUID(str(payload["request_id"]))
    input_text = str(payload.get("text", "")).strip()
    operation = str(payload.get("operation", "chat"))
    expected = payload.get("expected_profile_revision")
    with transaction.atomic():
        conversation = owned_conversation(user_id, conversation_id, lock=True)
        existing = Turn.objects.filter(conversation=conversation, request_id=request_id).first()
        if existing:
            if existing.payload_hash != payload_hash:
                raise ConflictError("This request ID was already used with different content.")
            attempt = existing.attempts.order_by("-created_at").first()
            if attempt is None:
                raise ConflictError("The existing turn has no execution attempt.")
            answer_id = str(attempt.answer.id) if attempt and hasattr(attempt, "answer") else None
            return AcceptedTurn(
                str(existing.id),
                str(attempt.id),
                attempt.profile_revision,
                True,
                answer_id,
                attempt.status,
            )
        current_revision = (
            conversation.current_profile.revision if conversation.current_profile else None
        )
        if expected is not None and int(expected) != current_revision:
            raise ConflictError("The profile changed. Reload it before sending this message.")
        if conversation.active_attempt_id is not None:
            raise ConflictError("Another turn is already running in this conversation.")
        route = selected_route(user_id)
        if route is not None:
            AIPreference.objects.get_or_create(user_id=user_id, defaults={"route": route})
        turn = Turn.objects.create(
            conversation=conversation,
            request_id=request_id,
            payload_hash=payload_hash,
            input_text=input_text,
            route=route,
            operation=operation,
            expected_profile_revision=expected,
        )
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=input_text,
            origin="structured" if operation != "chat" else "text",
        )
        corpus_release = CorpusRelease.objects.filter(
            activated_at__isnull=False, is_current=True
        ).first()
        attempt = TurnAttempt.objects.create(
            turn=turn,
            conversation=conversation,
            profile_revision=current_revision,
            corpus_release=corpus_release,
            route=turn.route,
            deadline_at=timezone.now() + timedelta(seconds=settings.AI_TURN_TIMEOUT_SECONDS),
        )
        conversation.active_attempt = attempt
        conversation.save(update_fields=["active_attempt", "updated_at"])
    return AcceptedTurn(
        str(turn.id), str(attempt.id), current_revision, False, None, attempt.status
    )


def mark_running(user_id: uuid.UUID, attempt_id: uuid.UUID) -> bool:
    return (
        TurnAttempt.objects.filter(
            id=attempt_id, turn__conversation__owner_id=user_id, status=TurnAttempt.Status.ACCEPTED
        ).update(status=TurnAttempt.Status.RUNNING)
        == 1
    )


def publish_controlled_answer(user_id: uuid.UUID, attempt_id: uuid.UUID) -> dict[str, Any]:
    with transaction.atomic():
        conversation_id = TurnAttempt.objects.values_list("turn__conversation_id", flat=True).get(
            id=attempt_id, turn__conversation__owner_id=user_id
        )
        conversation = Conversation.objects.select_for_update().get(
            id=conversation_id, owner_id=user_id
        )
        attempt = (
            TurnAttempt.objects.select_for_update()
            .select_related("turn")
            .get(id=attempt_id, turn__conversation__owner_id=user_id)
        )
        if attempt.status != TurnAttempt.Status.RUNNING:
            raise ConflictError("This attempt can no longer publish.")
        profile = (
            ProfileRevision.objects.get(id=conversation.current_profile_id)
            if conversation.current_profile_id
            else None
        )
        current_revision = profile.revision if profile else None
        if current_revision != attempt.profile_revision:
            attempt.status = TurnAttempt.Status.SUPERSEDED
            attempt.terminal_code = "profile_changed"
            attempt.save(update_fields=["status", "terminal_code", "updated_at"])
            raise ConflictError("The profile changed while the answer was being prepared.")
        operation = attempt.turn.operation
        facts: list[VerifiedFact] = []
        if operation in {"recommend", "compare"} and (
            profile is None or profile.confirmed_at is None
        ):
            outcome = TurnAttempt.Status.NEEDS_INPUT
            text = "Please review and confirm your insurance profile before I compare or recommend policies."
            blocks = [{"type": "text", "text": text}]
        elif operation in {"recommend", "compare", "policy_question"} or _asks_about_active_fact(
            attempt.turn.input_text
        ):
            if attempt.corpus_release_id is None:
                outcome = TurnAttempt.Status.INSUFFICIENT_EVIDENCE
                text = "I can’t support this policy conclusion yet because this pilot has no active, reviewed policy evidence. The catalogue coverage screen shows what still needs review."
                blocks = [{"type": "text", "text": text}]
            else:
                lock_corpus_publication()
                current_release_id = (
                    CorpusRelease.objects.select_for_update()
                    .filter(activated_at__isnull=False, is_current=True)
                    .values_list("id", flat=True)
                    .first()
                )
                if current_release_id != attempt.corpus_release_id:
                    attempt.status = TurnAttempt.Status.SUPERSEDED
                    attempt.terminal_code = "corpus_changed"
                    attempt.save(update_fields=["status", "terminal_code", "updated_at"])
                    raise ConflictError(
                        "The evidence corpus changed while the answer was prepared."
                    )
                facts = _active_facts(attempt, operation)
                if not facts:
                    outcome = TurnAttempt.Status.INSUFFICIENT_EVIDENCE
                    text = "The active test corpus does not contain a verified fact for that question yet."
                    blocks = [{"type": "text", "text": text}]
                else:
                    outcome = TurnAttempt.Status.SUCCEEDED
                    text = _answer_intro(operation)
                    blocks = [{"type": "text", "text": text}]
                    blocks.extend(
                        {"type": "claim", "text": _fact_text(fact.category)} for fact in facts
                    )
        else:
            outcome = TurnAttempt.Status.NEEDS_INPUT
            text = "Tell me who needs cover, their ages, your city, existing cover, budget, medical conditions you want considered, and any must-have hospitals or benefits. You can mark anything as unknown."
            blocks = [{"type": "text", "text": text}]
        answer = AnswerArtifact.objects.create(
            attempt=attempt,
            outcome=outcome,
            blocks=blocks,
            verification_status="controlled_template",
            profile_revision=attempt.profile_revision,
            corpus_release=attempt.corpus_release,
        )
        claims = []
        for fact in facts:
            claim = AnswerClaim.objects.create(
                answer=answer,
                claim_type="policy_fact",
                display_text=_fact_text(fact.category),
                fact_ids=[str(fact.id)],
                verification_result="verified",
            )
            claim.evidence_bundles.add(fact.evidence_bundle)
            claims.append(claim)
        if operation in {"recommend", "compare"} and outcome == TurnAttempt.Status.SUCCEEDED:
            corpus_release = attempt.corpus_release
            if corpus_release is None:
                raise ConflictError("The captured corpus release is unavailable.")
            RecommendationSnapshot.objects.create(
                answer=answer,
                owner_id=user_id,
                profile_revision=attempt.profile_revision or 0,
                corpus_release=corpus_release,
                candidate_results=[
                    {
                        "plan": "Care Supreme",
                        "uin": "CHIHLIP27061V032627",
                        "outcome": "needs_evidence",
                        "missing": ["personalised premium", "underwriting outcome"],
                    }
                ],
                rankings=[],
                calculations=[],
                rule_version="pilot-v1",
            )
        message_text = "\n\n".join([text, *[f"• {_fact_text(fact.category)}" for fact in facts]])
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=message_text,
            origin="controlled_template",
            answer=answer,
        )
        attempt.status = outcome
        attempt.save(update_fields=["status", "updated_at"])
        if conversation.active_attempt_id == attempt.id:
            conversation.active_attempt = None
            conversation.save(update_fields=["active_attempt", "updated_at"])
    from .serializers import AnswerSerializer

    answer = AnswerArtifact.objects.prefetch_related(
        "claims__evidence_bundles__evidencebundlespan_set__span__page__extraction_revision__document_version"
    ).get(id=answer.id)
    return dict(AnswerSerializer(answer).data)


FACT_TEXT = {
    "pre_existing_disease_waiting_period": (
        "The base wording applies a 36-month waiting period to pre-existing disease treatment "
        "and direct complications. Portability credit can reduce it; later coverage requires "
        "declaration at application and insurer acceptance."
    ),
    "named_ailment_waiting_period": (
        "Listed conditions, surgeries, and treatments have a 24-month waiting period; the clause "
        "exempts claims arising from an accident."
    ),
    "initial_waiting_period": (
        "Illness treatment is excluded during the first 30 days, except covered accident claims. "
        "The wording also states a continuous-coverage condition."
    ),
    "optional_copayment": (
        "Co-payment is an optional benefit. If selected, the percentage in the policy schedule "
        "applies to every claim for each insured member."
    ),
}

FACT_VALUES = {
    "pre_existing_disease_waiting_period": {"months": "36"},
    "named_ailment_waiting_period": {"months": "24"},
    "initial_waiting_period": {"days": "30"},
    "optional_copayment": {"optional": True, "amount_source": "policy_schedule"},
}

FACT_VALUE_TYPES = {
    "pre_existing_disease_waiting_period": "duration",
    "named_ailment_waiting_period": "duration",
    "initial_waiting_period": "duration",
    "optional_copayment": "structured_text",
}

FACT_APPLICABILITY = {
    "pre_existing_disease_waiting_period": {
        "portability_credit": True,
        "declaration_and_acceptance_required": True,
    },
    "named_ailment_waiting_period": {"accident_exception": True},
    "initial_waiting_period": {
        "accident_exception": True,
        "continuous_coverage_condition": True,
    },
    "optional_copayment": {"only_if_selected": True},
}

FACT_REQUIRED_TERMS = {
    "pre_existing_disease_waiting_period": (
        "36 months",
        "portability",
        "declared",
        "accepted by insurer",
    ),
    "named_ailment_waiting_period": ("24 months", "accident"),
    "initial_waiting_period": ("30 days", "continuous coverage"),
    "optional_copayment": ("co-payment", "policy schedule", "each and every claim"),
}


def _fact_text(category: str) -> str:
    return FACT_TEXT[category]


def _asks_about_active_fact(text: str) -> bool:
    lowered = text.casefold()
    return any(
        keyword in lowered
        for keyword in (
            "care supreme",
            "waiting period",
            "pre-existing",
            "pre existing",
            "ped",
            "named ailment",
            "30-day",
            "30 day",
            "initial waiting",
            "copay",
            "co-pay",
        )
    )


def _active_facts(attempt: TurnAttempt, operation: str) -> list[VerifiedFact]:
    if operation in {"recommend", "compare"}:
        categories = list(FACT_TEXT)
    else:
        lowered = attempt.turn.input_text.casefold()
        if "copay" in lowered or "co-pay" in lowered:
            categories = ["optional_copayment"]
        elif any(term in lowered for term in ("pre-existing", "pre existing", "ped")):
            categories = ["pre_existing_disease_waiting_period"]
        elif "named ailment" in lowered:
            categories = ["named_ailment_waiting_period"]
        elif any(term in lowered for term in ("30-day", "30 day", "initial waiting")):
            categories = ["initial_waiting_period"]
        else:
            categories = []
    corpus_release = attempt.corpus_release
    if corpus_release is None:
        return []
    manifest_ids = set(corpus_release.manifest.get("fact_ids", []))
    extraction_revision_id = corpus_release.manifest.get("extraction_revision_id")
    candidate_facts = list(
        VerifiedFact.objects.select_for_update()
        .filter(
            id__in=manifest_ids,
            category__in=categories,
            verification_state="verified",
            conflict=False,
            evidence_bundle__review_state="verified",
        )
        .select_related("evidence_bundle")
    )
    facts_by_category = {}
    for fact in candidate_facts:
        links = list(
            fact.evidence_bundle.evidencebundlespan_set.select_for_update().select_related(
                "span__page__extraction_revision"
            )
        )
        evidence_text = " ".join(link.span.quote for link in links).casefold()
        try:
            for link in links:
                validate_evidence_span(link.span)
        except DocumentValidationError:
            continue
        if (
            fact.value == FACT_VALUES.get(fact.category)
            and fact.value_type == FACT_VALUE_TYPES.get(fact.category)
            and fact.applicability == FACT_APPLICABILITY.get(fact.category)
            and links
            and all(
                str(link.span.page.extraction_revision_id) == str(extraction_revision_id)
                for link in links
            )
            and all(term in evidence_text for term in FACT_REQUIRED_TERMS[fact.category])
        ):
            facts_by_category[fact.category] = fact
    if any(category not in facts_by_category for category in categories):
        return []
    return [facts_by_category[category] for category in categories]


def _answer_intro(operation: str) -> str:
    if operation in {"recommend", "compare"}:
        return (
            "The Care Supreme document is active as a one-plan, evidence-backed test option. This is "
            "not yet a personalised buying recommendation: the pilot has no verified premium or underwriting "
            "result for you, and the other 202 catalogue listings remain unreviewed."
        )
    return "Here is what the active Care Supreme policy wording supports:"


def cancel_attempt(user_id: uuid.UUID, attempt_id: uuid.UUID) -> bool:
    with transaction.atomic():
        conversation_id = (
            TurnAttempt.objects.filter(id=attempt_id, turn__conversation__owner_id=user_id)
            .values_list("turn__conversation_id", flat=True)
            .first()
        )
        if conversation_id is None:
            return False
        conversation = Conversation.objects.select_for_update().get(
            id=conversation_id, owner_id=user_id
        )
        changed = (
            TurnAttempt.objects.filter(id=attempt_id, status__in=TurnAttempt.ACTIVE).update(
                status=TurnAttempt.Status.CANCELLED, terminal_code="user_cancelled"
            )
            == 1
        )
        if changed and conversation.active_attempt_id == attempt_id:
            conversation.active_attempt = None
            conversation.save(update_fields=["active_attempt", "updated_at"])
        return changed


def reconcile_expired_attempts(limit: int = 100) -> int:
    expired = list(
        TurnAttempt.objects.filter(status__in=TurnAttempt.ACTIVE, deadline_at__lt=timezone.now())
        .values_list("id", "turn__conversation_id")
        .order_by("deadline_at")[:limit]
    )
    reconciled = 0
    for attempt_id, conversation_id in expired:
        with transaction.atomic():
            conversation = Conversation.objects.select_for_update().get(id=conversation_id)
            changed = TurnAttempt.objects.filter(
                id=attempt_id,
                status__in=TurnAttempt.ACTIVE,
                deadline_at__lt=timezone.now(),
            ).update(status=TurnAttempt.Status.FAILED, terminal_code="deadline_expired")
            if changed and conversation.active_attempt_id == attempt_id:
                conversation.active_attempt = None
                conversation.save(update_fields=["active_attempt", "updated_at"])
            reconciled += changed
    return reconciled


def retry_turn(user_id: uuid.UUID, turn_id: uuid.UUID) -> TurnAttempt:
    with transaction.atomic():
        conversation_id = Turn.objects.values_list("conversation_id", flat=True).get(
            id=turn_id, conversation__owner_id=user_id
        )
        conversation = (
            Conversation.objects.select_for_update()
            .select_related("current_profile")
            .get(id=conversation_id, owner_id=user_id)
        )
        turn = Turn.objects.select_for_update().get(id=turn_id, conversation__owner_id=user_id)
        last = turn.attempts.order_by("-created_at").first()
        if last is None or last.status not in [
            TurnAttempt.Status.FAILED,
            TurnAttempt.Status.CANCELLED,
        ]:
            raise ConflictError("Only failed or cancelled attempts can be retried.")
        if conversation.active_attempt_id is not None:
            raise ConflictError("Another turn is already running in this conversation.")
        revision = conversation.current_profile.revision if conversation.current_profile else None
        corpus_release = CorpusRelease.objects.filter(
            activated_at__isnull=False, is_current=True
        ).first()
        attempt = TurnAttempt.objects.create(
            turn=turn,
            conversation=conversation,
            profile_revision=revision,
            corpus_release=corpus_release,
            route=turn.route,
            deadline_at=timezone.now() + timedelta(seconds=settings.AI_TURN_TIMEOUT_SECONDS),
        )
        conversation.active_attempt = attempt
        conversation.save(update_fields=["active_attempt", "updated_at"])
        return attempt
