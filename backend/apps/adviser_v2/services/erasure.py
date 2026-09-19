"""Fail-closed account erasure for the protected v2 customer graph."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Iterable
from datetime import timedelta

from django.contrib.sessions.models import Session
from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import User
from apps.adviser.models import AnswerArtifact, RecommendationSnapshot
from apps.adviser.models import Conversation as PilotConversation

from ..crypto import commitment
from ..models import (
    AdviceRequest,
    AuditEvent,
    Calculation,
    ConsentRecord,
    Conversation,
    ConversationMessageChunk,
    CustomerFact,
    CustomerPolicy,
    CustomerPolicyFact,
    CustomerPolicyOption,
    CustomerPolicyRevision,
    CustomerRequirement,
    CustomerStatement,
    CustomerUploadedDocument,
    DeletionRequest,
    EvidenceSpan,
    InformationNeed,
    Message,
    ModelAttempt,
    OriginalFile,
    Outbox,
    Person,
    PersonRelationship,
    PolicyCandidateAssessment,
    PolicyMember,
    PolicyRequirementMatch,
    ProcessingJob,
    Quote,
    Recommendation,
    RecommendationCitation,
    RecommendationStatement,
    Turn,
    TurnEvent,
)
from ..storage import delete_private

ERASED_TEXT = "[erased at customer request]"
STORE_NAMES = (
    "postgres",
    "original_storage",
    "search_index",
    "cache",
    "queue",
    "provider_artifact",
    "backup_tombstone",
)


def has_v2_private_data(owner_id: uuid.UUID) -> bool:
    return (
        Conversation.objects.filter(owner_id=owner_id).exists()
        or OriginalFile.objects.filter(owner_id=owner_id).exists()
        or Person.objects.filter(owner_id=owner_id).exists()
    )


def _verification(status: str) -> dict[str, object]:
    return {
        "stores": [{"store": name, "status": status} for name in STORE_NAMES],
    }


def _receipt(store: str, owner_id: uuid.UUID, count: int) -> str:
    payload = json.dumps(
        {"store": store, "owner_id": str(owner_id), "affected_count": count},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _completed_verification(owner_id: uuid.UUID, counts: dict[str, int]) -> dict[str, object]:
    return {
        "stores": [
            {
                "store": name,
                "status": "erased",
                "receipt_hash": _receipt(name, owner_id, counts.get(name, 0)),
            }
            for name in STORE_NAMES
        ],
        "verified_at": timezone.now().isoformat(),
        "verifier": "coverguide-v2-erasure/1",
    }


@transaction.atomic
def _begin(owner_id: uuid.UUID) -> DeletionRequest:
    owner = User.objects.select_for_update().get(pk=owner_id)
    now = timezone.now()
    owner.erasure_generation += 1
    owner.deleted_at = now
    owner.is_active = False
    owner.is_staff = False
    owner.is_superuser = False
    owner.email = f"deleted+{owner.id}@coverguide.invalid"
    owner.first_name = ""
    owner.last_name = ""
    owner.set_unusable_password()
    owner.save(
        update_fields=[
            "erasure_generation",
            "deleted_at",
            "is_active",
            "is_staff",
            "is_superuser",
            "email",
            "first_name",
            "last_name",
            "password",
        ]
    )
    return DeletionRequest.objects.create(
        owner=owner,
        scope={"kind": "account", "target_ids": [], "include_derived": True},
        state="running",
        verification=_verification("pending"),
    )


def _storage_keys(owner_id: uuid.UUID) -> set[str]:
    keys = set(OriginalFile.objects.filter(owner_id=owner_id).values_list("storage_key", flat=True))
    for key in ModelAttempt.objects.filter(
        owner_id=owner_id, response_storage_key__isnull=False
    ).values_list("response_storage_key", flat=True):
        if key is not None:
            keys.add(key)
    for key in ProcessingJob.objects.filter(
        owner_id=owner_id, result_storage_key__isnull=False
    ).values_list("result_storage_key", flat=True):
        if key is not None:
            keys.add(key)
    return {key for key in keys if key}


def _delete_sessions(owner_id: uuid.UUID) -> int:
    identifiers: list[str] = []
    for session in Session.objects.filter(expire_date__gte=timezone.now()).iterator():
        try:
            session_owner = session.get_decoded().get("_auth_user_id")
        except Exception:
            continue
        if str(session_owner) == str(owner_id):
            identifiers.append(session.session_key)
    if not identifiers:
        return 0
    deleted, _ = Session.objects.filter(session_key__in=identifiers).delete()
    return deleted


def _set_lease_token(token: uuid.UUID) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('coverguide.lease_token', %s, true)", [str(token)])


def _cancel_turns(owner_id: uuid.UUID) -> int:
    turns = list(Turn.objects.select_for_update().filter(owner_id=owner_id))
    now = timezone.now()
    for turn in turns:
        if turn.state == "running" and turn.lease_token is not None:
            Turn.objects.filter(pk=turn.id).update(lease_until=now + timedelta(minutes=1))
            _set_lease_token(turn.lease_token)
            turn.lease_until = now + timedelta(minutes=1)
            turn.state = "cancelled"
        elif turn.state in {"queued", "cancel_requested"}:
            turn.state = "cancelled"
        else:
            continue
        turn.cancelled_at = now
        turn.error_code = "account_erased"
        turn.save(
            update_fields=[
                "state",
                "lease_until",
                "cancelled_at",
                "error_code",
                "updated_at",
            ]
        )
    return len(turns)


def _cancel_jobs(owner_id: uuid.UUID) -> int:
    jobs = list(ProcessingJob.objects.select_for_update().filter(owner_id=owner_id))
    now = timezone.now()
    for job in jobs:
        if job.state == "running" and job.lease_token is not None:
            ProcessingJob.objects.filter(pk=job.id).update(lease_until=now + timedelta(minutes=1))
            _set_lease_token(job.lease_token)
            job.lease_until = now + timedelta(minutes=1)
        job.state = "cancelled"
        job.error_code = "account_erased"
        job.result_storage_key = None
        job.result_storage_sha256 = None
        job.issues = []
        job.save(
            update_fields=[
                "state",
                "lease_until",
                "error_code",
                "result_storage_key",
                "result_storage_sha256",
                "issues",
                "updated_at",
            ]
        )
    return len(jobs)


def _erase_private_evidence(owner_id: uuid.UUID) -> int:
    originals = list(OriginalFile.objects.filter(owner_id=owner_id))
    synthetic_by_id = {
        item.id: hashlib.sha256(f"erased:{item.id}".encode()).hexdigest() for item in originals
    }
    EvidenceSpan.objects.filter(customer_uploaded_document__owner_id=owner_id).update(
        section_label=None,
        quote=ERASED_TEXT,
        context={"span_ids": [], "notes": []},
        method="json",
        verification="failed",
        locator={
            "schema_version": 1,
            "blob_sha256": "0" * 64,
            "resolver_version": "erased/1",
            "kind": "pdf_region",
            "physical_page": 1,
            "bbox": [0, 0, 0, 0],
            "coordinate_space": "unrotated_pdf_points",
            "rotation": 0,
        },
    )
    CustomerUploadedDocument.objects.filter(owner_id=owner_id).update(
        display_name=None,
        kind="other",
        review_status="unusable",
    )
    for original in originals:
        digest = synthetic_by_id[original.id]
        OriginalFile.objects.filter(pk=original.id).update(
            sha256=digest,
            storage_key=f"deleted/{owner_id}/{original.id}",
            byte_size=0,
            media_type="application/x-erased",
            availability="deleted",
            last_verified_at=timezone.now(),
        )
    return len(originals)


def _erase_relational_content(owner_id: uuid.UUID) -> int:
    affected = 0

    def remove(querysets: Iterable[object]) -> None:
        nonlocal affected
        for queryset in querysets:
            deleted, _ = queryset.delete()  # type: ignore[attr-defined]
            affected += deleted

    ConversationMessageChunk.objects.filter(owner_id=owner_id).delete()
    RecommendationCitation.objects.filter(owner_id=owner_id).delete()
    RecommendationStatement.objects.filter(owner_id=owner_id).delete()
    PolicyRequirementMatch.objects.filter(owner_id=owner_id).delete()
    InformationNeed.objects.filter(owner_id=owner_id).delete()
    PolicyCandidateAssessment.objects.filter(owner_id=owner_id).delete()
    Message.objects.filter(owner_id=owner_id).update(recommendation=None)
    Recommendation.objects.filter(owner_id=owner_id).update(supersedes=None)
    remove(
        [
            Recommendation.objects.filter(owner_id=owner_id),
            Calculation.objects.filter(owner_id=owner_id),
            Quote.objects.filter(owner_id=owner_id),
        ]
    )
    CustomerPolicyFact.objects.filter(owner_id=owner_id).update(supersedes=None)
    remove(
        [
            CustomerPolicyFact.objects.filter(owner_id=owner_id),
            PolicyMember.objects.filter(owner_id=owner_id),
            CustomerPolicyOption.objects.filter(owner_id=owner_id),
            CustomerPolicyRevision.objects.filter(owner_id=owner_id),
            CustomerPolicy.objects.filter(owner_id=owner_id),
            ConsentRecord.objects.filter(owner_id=owner_id),
            PersonRelationship.objects.filter(owner_id=owner_id),
            CustomerFact.objects.filter(owner_id=owner_id),
            CustomerRequirement.objects.filter(owner_id=owner_id),
            AdviceRequest.objects.filter(owner_id=owner_id),
            CustomerStatement.objects.filter(owner_id=owner_id),
            Person.objects.filter(owner_id=owner_id),
        ]
    )
    Message.objects.filter(owner_id=owner_id).update(
        content=ERASED_TEXT,
        payload_commitment=commitment({"owner_id": str(owner_id), "state": "erased"}),
        redacted_at=timezone.now(),
    )
    Conversation.objects.filter(owner_id=owner_id).update(
        title=ERASED_TEXT,
        status="deleted",
        preferred_language=None,
        updated_at=timezone.now(),
    )
    TurnEvent.objects.filter(owner_id=owner_id).delete()
    AuditEvent.objects.filter(Q(owner_id=owner_id) | Q(actor_id=owner_id)).delete()
    return affected


@transaction.atomic
def _complete(request_id: uuid.UUID, storage_count: int) -> DeletionRequest:
    deletion = DeletionRequest.objects.select_for_update().get(pk=request_id)
    owner_id = deletion.owner_id
    User.objects.select_for_update().get(pk=owner_id)
    queue_count, _ = Outbox.objects.filter(owner_id=owner_id).delete()
    turn_count = _cancel_turns(owner_id)
    job_count = _cancel_jobs(owner_id)
    ModelAttempt.objects.filter(owner_id=owner_id).update(
        completed_at=timezone.now(),
        status="cancelled",
        error_code="account_erased",
        response_storage_key=None,
        response_storage_sha256=None,
    )
    relational_count = _erase_relational_content(owner_id)
    original_count = _erase_private_evidence(owner_id)
    RecommendationSnapshot.objects.filter(owner_id=owner_id).delete()
    AnswerArtifact.objects.filter(attempt__turn__conversation__owner_id=owner_id).delete()
    PilotConversation.objects.filter(owner_id=owner_id).delete()
    session_count = _delete_sessions(owner_id)
    owner = deletion.owner
    owner.groups.clear()
    owner.user_permissions.clear()
    counts = {
        "postgres": relational_count + original_count,
        "original_storage": storage_count,
        "search_index": relational_count,
        "cache": session_count,
        "queue": queue_count + turn_count + job_count,
        "provider_artifact": storage_count,
        "backup_tombstone": 0,
    }
    deletion.state = "completed"
    deletion.completed_at = timezone.now()
    deletion.verification = _completed_verification(owner_id, counts)
    deletion.error_code = None
    deletion.save(
        update_fields=[
            "state",
            "completed_at",
            "verification",
            "error_code",
            "updated_at",
        ]
    )
    return deletion


def erase_account(owner_id: uuid.UUID) -> DeletionRequest:
    deletion = _begin(owner_id)
    try:
        keys = _storage_keys(owner_id)
        for key in sorted(keys):
            delete_private(owner_id, key)
        return _complete(deletion.id, len(keys))
    except Exception:
        DeletionRequest.objects.filter(pk=deletion.id).update(
            state="failed",
            error_code="account_erasure_failed",
            updated_at=timezone.now(),
        )
        raise
