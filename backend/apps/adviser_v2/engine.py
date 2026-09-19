"""Durable end-to-end v2 customer turn orchestration."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.adviser.ai import RelayFailure

from .errors import (
    AccountErased,
    PinnedStateChanged,
    TurnCancellationRequested,
    TurnLeaseLost,
    UnsupportedRecommendationError,
)
from .model_gateway import call_model
from .models import Conversation, KnowledgeChannel, Outbox, Turn
from .registries import FACT_TYPES, REQUIREMENT_TYPES
from .retrieval import conversation_context, index_message, retrieve_policy_context
from .role_routes import configured_route
from .schemas import CustomerInterpretationV1, RecommendationDraftV1
from .selectors.customer import current_profile_payload
from .services.customer import append_turn_event
from .services.interpretation import (
    apply_interpretation,
    normalize_explicit_restoration_scenario,
    normalize_first_turn_references,
    normalize_money_quantity_units,
    normalize_purchase_fact_scopes,
    normalize_requested_sum_insured_priority,
    normalize_self_insured_fact,
    recover_explicit_child_age,
    recover_explicit_city,
    recover_explicit_policy_term,
    recover_explicit_room_illustration,
    suppress_catalogue_clarification,
    validate_interpretation,
)
from .services.recommendations import (
    CORE_FACT_QUESTIONS,
    already_asked_information_keys,
    clarification_draft,
    model_context,
    next_missing_core_fact,
    prepare_recommendation,
    publish_draft,
)

logger = logging.getLogger(__name__)

_PERSONALIZATION_INTENTS = frozenset(
    {
        "purchase_recommendation",
        "product_comparison",
        "coverage_question",
        "renewal_review",
        "portability_review",
    }
)


def _set_lease_token(token: uuid.UUID) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('coverguide.lease_token', %s, true)", [str(token)])


def _execution_times(started_at: datetime, timeout_seconds: int) -> tuple[datetime, datetime]:
    """Give a queued turn its inference budget when a worker actually starts it."""

    return (
        started_at + timedelta(seconds=timeout_seconds),
        started_at + timedelta(seconds=max(180, timeout_seconds * 2)),
    )


def _lock_active_turn(turn_id: uuid.UUID, token: uuid.UUID) -> Turn:
    """Fence a mutation inside the caller's transaction."""

    if not connection.in_atomic_block:
        raise RuntimeError("Turn mutation fencing requires an active transaction.")
    turn = Turn.objects.select_for_update().get(pk=turn_id)
    if turn.state == "cancel_requested":
        raise TurnCancellationRequested("turn_cancel_requested")
    if (
        turn.state != "running"
        or turn.lease_token != token
        or turn.lease_until is None
        or turn.lease_until <= timezone.now()
    ):
        raise TurnLeaseLost("turn_lease_lost")
    return turn


@transaction.atomic
def _claim_turn(
    turn_id: uuid.UUID,
) -> tuple[Turn, uuid.UUID, uuid.UUID, int, int] | None:
    turn = Turn.objects.select_for_update().select_related("input_message").get(pk=turn_id)
    if turn.state != "queued":
        raise ValueError("turn_not_queued")
    owner = User.objects.select_for_update().get(pk=turn.owner_id)
    if owner.deleted_at is not None or not owner.is_active:
        turn.state = "cancelled"
        turn.cancelled_at = timezone.now()
        turn.error_code = "account_erased"
        turn.save(update_fields=["state", "cancelled_at", "error_code", "updated_at"])
        Outbox.objects.filter(turn=turn, event_type="turn_dispatch").delete()
        append_turn_event(turn, "cancelled", {"schema_version": 1, "kind": "cancelled"})
        return None
    channel = (
        KnowledgeChannel.objects.select_for_update(of=("self",))
        .select_related("current_release")
        .filter(name="live")
        .first()
    )
    if (
        channel is None
        or channel.current_release is None
        or channel.current_release.state != "published"
    ):
        raise ValueError("knowledge_not_ready")
    conversation = (
        Conversation.objects.select_for_update(of=("self",))
        .select_related("current_profile_revision")
        .get(pk=turn.conversation_id)
    )
    if conversation.current_profile_revision_id != turn.starting_profile_revision_id:
        turn.state = "stale"
        turn.error_code = "pinned_state_changed"
        turn.save(update_fields=["state", "error_code", "updated_at"])
        Outbox.objects.filter(turn=turn, event_type="turn_dispatch").update(
            state="delivered", lease_until=None, last_error_code=None
        )
        current_revision = conversation.current_profile_revision
        revision = current_revision.revision if current_revision is not None else 0
        append_turn_event(
            turn,
            "stale",
            {"schema_version": 1, "kind": "stale", "revision": revision},
        )
        return None
    token = uuid.uuid4()
    started_at = timezone.now()
    turn.state = "running"
    turn.lease_token = token
    turn.deadline, turn.lease_until = _execution_times(
        started_at, settings.AI_TURN_TIMEOUT_SECONDS
    )
    turn.save(update_fields=["state", "lease_token", "lease_until", "deadline", "updated_at"])
    Outbox.objects.filter(turn=turn, event_type="turn_dispatch").update(
        state="delivered", lease_until=None, last_error_code=None
    )
    append_turn_event(turn, "started", {"schema_version": 1, "kind": "started"})
    release_id = channel.current_release_id
    if release_id is None:
        raise ValueError("knowledge_not_ready")
    return turn, token, release_id, channel.generation, owner.erasure_generation


@transaction.atomic
def _terminal(
    turn_id: uuid.UUID, token: uuid.UUID, state: str, error_code: str | None = None
) -> bool:
    turn = Turn.objects.select_for_update().get(pk=turn_id)
    if turn.state == "cancel_requested":
        state = "cancelled"
        error_code = None
    elif (
        turn.state != "running"
        or turn.lease_token != token
        or turn.lease_until is None
        or turn.lease_until <= timezone.now()
    ):
        return False
    _set_lease_token(token)
    turn.state = state
    turn.error_code = error_code
    if state == "cancelled" and turn.cancelled_at is None:
        turn.cancelled_at = timezone.now()
    turn.save(update_fields=["state", "error_code", "cancelled_at", "updated_at"])
    if state == "failed":
        append_turn_event(
            turn,
            "failed",
            {
                "schema_version": 1,
                "kind": "failed",
                "error_code": error_code or "technical_failure",
            },
        )
    elif state == "cancelled":
        append_turn_event(turn, "cancelled", {"schema_version": 1, "kind": "cancelled"})
    return True


@transaction.atomic
def _mark_stale(turn_id: uuid.UUID, token: uuid.UUID) -> bool:
    turn = (
        Turn.objects.select_for_update()
        .select_related("conversation__current_profile_revision")
        .get(pk=turn_id)
    )
    if turn.state == "cancel_requested":
        _set_lease_token(token)
        turn.state = "cancelled"
        turn.error_code = None
        turn.save(update_fields=["state", "error_code", "updated_at"])
        append_turn_event(turn, "cancelled", {"schema_version": 1, "kind": "cancelled"})
        return True
    if (
        turn.state != "running"
        or turn.lease_token != token
        or turn.lease_until is None
        or turn.lease_until <= timezone.now()
    ):
        return False
    current = turn.conversation.current_profile_revision
    if current is None:
        raise ValueError("profile_revision_missing")
    _set_lease_token(token)
    turn.state = "stale"
    turn.error_code = "pinned_state_changed"
    turn.save(update_fields=["state", "error_code", "updated_at"])
    append_turn_event(
        turn,
        "stale",
        {"schema_version": 1, "kind": "stale", "revision": current.revision},
    )
    return True


def _recover_expired_turn() -> None:
    from .services.outbox import recover_expired_work

    recover_expired_work()


@transaction.atomic
def _publish_terminal_event(
    turn_id: uuid.UUID,
    token: uuid.UUID,
    *,
    release_id: uuid.UUID,
    channel_generation: int,
    profile_revision_id: uuid.UUID,
    recommendation_id: uuid.UUID,
    message_id: uuid.UUID,
    clarification: bool,
) -> None:
    turn = Turn.objects.select_for_update().get(pk=turn_id)
    if turn.state == "cancel_requested":
        _set_lease_token(token)
        turn.state = "cancelled"
        turn.save(update_fields=["state", "updated_at"])
        append_turn_event(turn, "cancelled", {"schema_version": 1, "kind": "cancelled"})
        return
    if (
        turn.state != "running"
        or turn.lease_token != token
        or turn.lease_until is None
        or turn.lease_until <= timezone.now()
    ):
        raise TurnLeaseLost("turn_lease_lost")
    channel = KnowledgeChannel.objects.select_related("current_release").get(name="live")
    conversation = turn.conversation
    if (
        channel.current_release_id != release_id
        or channel.generation != channel_generation
        or conversation.current_profile_revision_id != profile_revision_id
    ):
        current_revision = conversation.current_profile_revision
        if current_revision is None:
            raise ValueError("profile_revision_missing")
        _set_lease_token(token)
        turn.state = "stale"
        turn.error_code = "pinned_state_changed"
        turn.save(update_fields=["state", "error_code", "updated_at"])
        append_turn_event(
            turn,
            "stale",
            {
                "schema_version": 1,
                "kind": "stale",
                "revision": current_revision.revision,
            },
        )
        return
    _set_lease_token(token)
    turn.state = "completed"
    turn.save(update_fields=["state", "updated_at"])
    if clarification:
        append_turn_event(
            turn,
            "clarification",
            {"schema_version": 1, "kind": "clarification", "message_id": str(message_id)},
        )
    else:
        append_turn_event(
            turn,
            "recommendation",
            {
                "schema_version": 1,
                "kind": "recommendation",
                "decision_id": str(recommendation_id),
            },
        )


def _interpretation_contract_guidance() -> str:
    """Describe semantic constraints hidden behind JSON-encoded contract values."""

    fact_types = " ".join(sorted(FACT_TYPES))
    requirement_types = " ".join(sorted(REQUIREMENT_TYPES))
    person_fact_types = " ".join(
        sorted(key for key, value in FACT_TYPES.items() if value.person_scoped)
    )
    purchase_fact_types = " ".join(
        sorted(key for key, value in FACT_TYPES.items() if not value.person_scoped)
    )
    person_requirement_types = " ".join(
        sorted(key for key, value in REQUIREMENT_TYPES.items() if value.person_scoped)
    )
    return (
        "Allowed fact_type tokens (use only these): "
        f"{fact_types}. Allowed requirement criterion tokens (use only these): "
        f"{requirement_types}. "
        "Do not encode comparison count, citations, evidence, output format, explanation style, "
        "or instructions to show unknowns as customer requirements; keep those as context or "
        "question statements. The three published products are already available to the adviser; "
        "never ask the customer to provide their names or policy documents merely to compare them. "
        "For an explicitly requested policy term, use requirement criterion "
        "policy_tenure_selection with a quantity target in years. Extract every explicitly "
        "stated insured person's age, including an infant's age in days. Use city, not location. "
        f"Person-scoped fact types: {person_fact_types}. They require a declared subject and the "
        "same non-null subject_key. "
        f"Purchase-scoped fact types: {purchase_fact_types}. They require subject_key null. "
        f"Person-scoped requirement types: {person_requirement_types}. They require scope person "
        "and a declared non-null subject_key; every other requirement requires subject_key null. "
        "Every fact value and non-null target_value is a JSON-encoded object string. "
        "Known quantity example: {\"state\":\"known\",\"kind\":\"quantity\","
        "\"value\":\"32\",\"unit\":\"year\"}. Known text example: "
        "{\"state\":\"known\",\"kind\":\"text\",\"value\":\"Bengaluru\"}. "
        "Known boolean example: {\"state\":\"known\",\"kind\":\"boolean\","
        "\"value\":true}. Unknown example: {\"state\":\"unknown\","
        "\"reason\":\"not provided\"}. Use decimal strings, not JSON numbers, for quantities. "
        "Whenever a person states or denies a pre-existing condition or ongoing treatment, "
        "also record a medical_history_disclosed fact for that same person as a known boolean "
        "true, regardless of whether they have any conditions — it only marks that the topic "
        "was addressed. Never record it as false; omit it entirely if the topic was not "
        "raised. This is separate from medical_condition, which only exists when a specific "
        "condition is actually disclosed."
    )


def _interpretation_messages(turn: Turn) -> list[dict[str, str]]:
    profile = current_profile_payload(turn.owner_id, turn.conversation_id)
    history = conversation_context(turn.owner_id, turn.conversation_id, turn.input_message.content)
    message_length = len(turn.input_message.content)
    return [
        {
            "role": "system",
            "content": (
                "Return CustomerInterpretationV1 only. Preserve exact UTF-8 character offsets. "
                f"The customer message you are interpreting is exactly {message_length} UTF-8 "
                f"characters long: every statement's start_offset must be >= 0 and end_offset must "
                f"be <= {message_length}. Only emit a statement whose span is an actual substring "
                "of that message; never invent a statement beyond its end. "
                "Do not resolve ambiguity, invent people, diagnoses, dates, budgets, or preferences. "
                "Use existing person IDs and logical keys when the current profile supplies them. "
                "Encode each fact value and non-null requirement/correction value as a JSON object "
                "string conforming to FactValueV1. "
                "Mark one focused clarification only when the message cannot be safely interpreted. "
                + _interpretation_contract_guidance()
            ),
        },
        {
            "role": "system",
            "content": "Current structured profile: " + json.dumps(profile, default=str),
        },
        *[
            {
                "role": "assistant" if item.role == "adviser" else "user",
                "content": item.content,
            }
            for item in history
        ],
    ]


def _recommendation_contract_guidance() -> str:
    return (
        "Statements with statement_type eligibility requirement_match benefit restriction price "
        "provider calculation must include at least one supplied citation, except a calculation "
        "statement may instead reference a supplied calculation_id. Critical statements also need "
        "a citation or calculation unless their statement_type is customer_context limitation or "
        "next_step. Describe deterministic candidate names and ranks without policy evidence using "
        "statement_type limitation. Describe unknown or unavailable evidence, including the absence "
        "of a comparable premium quote, using statement_type limitation, never price or provider. "
        "A candidate-specific citation must belong to that same candidate's policy version. For "
        "each citation, copy role only from that evidence entry's allowed_citation_roles list. "
        "Each statement may set at most one of candidate_assessment_id, requirement_match_id, "
        "information_need_id: requirement_match_id already identifies its candidate, so set it "
        "alone rather than also setting candidate_assessment_id. If an explanation genuinely "
        "concerns more than one decision object, split it into separate statements instead of "
        "combining references on one statement."
    )


def _recommendation_messages(context: dict[str, Any]) -> list[dict[str, str]]:
    catalogue_limit = str(context.get("catalogue_limit", "the published reviewed products"))
    return [
        {
            "role": "system",
            "content": (
                "Return RecommendationDraftV1 only. The deterministic outcome, candidate order, "
                "facts, rules, calculations, and evidence IDs are immutable. Reference only supplied "
                "IDs. Explain restrictions that affect the customer's stated requirements; omit "
                "unrelated policy terms. Do not quote "
                "a premium unless a supplied comparable customer quote supports it. For a conditional "
                "outcome, state that no product's full eligibility is verified and do not call the "
                "first-ranked candidate a best fit or recommendation. If claim_illustration is true, "
                "explain the supplied deterministic calculation as a claim example, subject to its "
                "assumptions; do not treat it as a purchase recommendation. "
                "If ayush_scenario_conditions are present, identify each condition explicitly "
                "stated in the customer's hypothetical scenario, and identify any remaining "
                "unknown condition separately. Do not call a stated eligible facility, valid "
                "licence, or India treatment location unstated or unverified within that scenario; "
                "real claim admissibility can still remain unknown. Limit comparisons to "
                f"{catalogue_limit}, never the whole market. "
                "When a requirement_matches entry has a non-null comparison_value, you may state "
                "that matched amount alongside its outcome, but only in a statement whose "
                "requirement_match_id is that exact entry's requirement_match_id — never state "
                "one match's comparison_value in a statement about a different match or candidate. "
                "Never state a comparison_value amount when it is null; describe the outcome only. "
                "When the customer has stated both a sum_insured requirement and a budget "
                "requirement, explicitly name which candidate(s) meet the budget requirement at "
                "the customer's stated sum_insured, and which do not, using only the real "
                "comparison_value figures already supplied for those exact requirement_matches; "
                "never assert a budget fit that isn't backed by a supplied comparison_value. "
                + _recommendation_contract_guidance()
            ),
        },
        {
            "role": "system",
            "content": "Validated decision context: " + json.dumps(context, default=str),
        },
        {"role": "user", "content": "Explain this validated decision clearly and concisely."},
    ]


def process_turn(turn_id: uuid.UUID) -> None:
    try:
        claimed = _claim_turn(turn_id)
    except ValueError as exc:
        if str(exc) == "turn_not_queued":
            return
        turn = Turn.objects.get(pk=turn_id)
        # A not-ready turn never became running, so no lease fence is needed.
        turn.state = "failed"
        turn.error_code = str(exc)
        turn.save(update_fields=["state", "error_code", "updated_at"])
        append_turn_event(
            turn,
            "failed",
            {"schema_version": 1, "kind": "failed", "error_code": str(exc)},
        )
        return
    if claimed is None:
        return
    turn, token, release_id, channel_generation, erasure_generation = claimed
    try:
        with transaction.atomic():
            _lock_active_turn(turn.id, token)
            index_message(turn.input_message)
            append_turn_event(
                turn,
                "progress",
                {
                    "schema_version": 1,
                    "kind": "progress",
                    "progress_code": "understanding_request",
                },
            )
        interpretation = call_model(
            route=configured_route("fact_interpretation"),
            schema_name="fact_interpretation",
            output_type=CustomerInterpretationV1,
            messages=_interpretation_messages(turn),
            remaining_seconds=max(0.0, (turn.deadline - timezone.now()).total_seconds()),
            turn=turn,
        )
        normalize_first_turn_references(
            interpretation,
            starting_revision=(
                turn.starting_profile_revision.revision
                if turn.starting_profile_revision is not None else 1
            ),
        )
        normalize_purchase_fact_scopes(interpretation)
        normalize_self_insured_fact(turn.input_message.content, interpretation)
        recover_explicit_city(turn.input_message.content, interpretation)
        recover_explicit_child_age(turn.input_message.content, interpretation)
        recover_explicit_policy_term(turn.input_message.content, interpretation)
        recover_explicit_room_illustration(turn.input_message.content, interpretation)
        suppress_catalogue_clarification(turn.input_message.content, interpretation)
        normalize_requested_sum_insured_priority(turn.input_message.content, interpretation)
        normalize_explicit_restoration_scenario(turn.input_message.content, interpretation)
        normalize_money_quantity_units(interpretation)
        validate_interpretation(turn.input_message.content, interpretation)
        with transaction.atomic():
            _lock_active_turn(turn.id, token)
            applied = apply_interpretation(
                turn.input_message,
                interpretation,
                expected_profile_revision_id=turn.starting_profile_revision_id,
                expected_release_id=release_id,
                expected_channel_generation=channel_generation,
                expected_erasure_generation=erasure_generation,
            )
            append_turn_event(
                turn,
                "progress",
                {"schema_version": 1, "kind": "progress", "progress_code": "checking_policies"},
            )
        release = KnowledgeChannel.objects.get(name="live").current_release
        if release is None or release.id != release_id:
            raise PinnedStateChanged("pinned_state_changed")
        profile = current_profile_payload(turn.owner_id, turn.conversation_id)
        missing_core_fact = None
        if not interpretation.ambiguity and interpretation.intent in _PERSONALIZATION_INTENTS:
            missing_core_fact = next_missing_core_fact(
                profile, already_asked_information_keys(turn.owner_id, turn.conversation_id)
            )
        is_clarifying = interpretation.ambiguity or missing_core_fact is not None
        clarification_question = interpretation.clarification_question or (
            CORE_FACT_QUESTIONS[missing_core_fact] if missing_core_fact else None
        )
        retrieval = (
            None
            if is_clarifying
            else retrieve_policy_context(
                "\n".join(
                    [
                        turn.input_message.content,
                        json.dumps(profile, default=str, ensure_ascii=False),
                    ]
                ),
                release,
            )
        )
        with transaction.atomic():
            _lock_active_turn(turn.id, token)
            prepared = prepare_recommendation(
                turn,
                applied.advice_request,
                applied.profile_revision,
                release,
                clarification_question=clarification_question,
                information_key=missing_core_fact or "customer_clarification",
            )
        decision_context = model_context(prepared, retrieval, profile=profile)
        if is_clarifying:
            draft = clarification_draft(clarification_question or "Please clarify.", prepared)
        else:
            with transaction.atomic():
                _lock_active_turn(turn.id, token)
                append_turn_event(
                    turn,
                    "progress",
                    {
                        "schema_version": 1,
                        "kind": "progress",
                        "progress_code": "validating_evidence",
                    },
                )
            draft = call_model(
                route=configured_route("recommendation_answer"),
                schema_name="recommendation_answer",
                output_type=RecommendationDraftV1,
                messages=_recommendation_messages(decision_context),
                remaining_seconds=max(0.0, (turn.deadline - timezone.now()).total_seconds()),
                turn=turn,
            )
        with transaction.atomic():
            _lock_active_turn(turn.id, token)
            adviser_message = publish_draft(
                turn,
                prepared,
                draft,
                decision_context,
                expected_release_id=release_id,
                expected_channel_generation=channel_generation,
                expected_erasure_generation=erasure_generation,
            )
            index_message(adviser_message)
            _publish_terminal_event(
                turn.id,
                token,
                release_id=release_id,
                channel_generation=channel_generation,
                profile_revision_id=applied.profile_revision.id,
                recommendation_id=prepared.recommendation.id,
                message_id=adviser_message.id,
                clarification=is_clarifying,
            )
    except RelayFailure as exc:
        if not _terminal(turn.id, token, "failed", exc.code):
            _recover_expired_turn()
    except TurnCancellationRequested:
        _terminal(turn.id, token, "cancelled")
    except TurnLeaseLost:
        _recover_expired_turn()
    except UnsupportedRecommendationError as exc:
        logger.warning("Recommendation validation rejected a draft: %s", exc)
        if not _terminal(turn.id, token, "failed", "unsupported_answer"):
            _recover_expired_turn()
    except AccountErased:
        _terminal(turn.id, token, "cancelled", "account_erased")
    except PinnedStateChanged:
        if not _mark_stale(turn.id, token):
            _recover_expired_turn()
    except Exception:
        if not _terminal(turn.id, token, "failed", "turn_processing_failed"):
            _recover_expired_turn()
        raise
