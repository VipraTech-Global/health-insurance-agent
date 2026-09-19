"""Leased, idempotent and resumable orchestration for document-processing jobs."""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.adviser.ai import RelayFailure

from .crypto import commitment
from .embedding import policy_index_version, qualified_embedding_status
from .errors import AccountErased
from .models import (
    AuditEvent,
    DocumentPage,
    Outbox,
    PolicyVersionDocument,
    ProcessingJob,
    ProductVariant,
    SourceCapture,
)
from .processing.artifacts import write_artifact
from .processing.readers import DependencyUnavailable, issue
from .processing.stages import (
    MAX_MODEL_PASSAGE_CHARACTERS,
    RECONCILIATION_VERSION,
    RULE_PROMPT_VERSION,
    RULE_REVIEW_PROMPT_VERSION,
    RULE_VALIDATOR_VERSION,
    STAGE_RUNNERS,
)

ADAPTER_VERSION = "coverguide-documents/4"
NEXT_STAGE = {
    "classify": "read",
    "read": "ocr",
    "ocr": "reconcile",
    "extract": "independent_review",
    "independent_review": "validate",
    "validate": "index",
}
RETRYABLE_RELAY_CODES = {
    "provider_timeout",
    "provider_transport",
    "invalid_structured_output",
}
DEFAULT_PROCESSING_LEASE = timedelta(minutes=30)
READ_PROCESSING_LEASE = timedelta(hours=2)
INDEX_PROCESSING_LEASE = timedelta(hours=4)
# The reviewed catalogue includes a 291-page prospectus/rate bundle; retain a
# bounded fence while allowing its three-minute-per-page CPU budget in full.
MAX_READ_PROCESSING_LEASE = timedelta(hours=16)
READ_PROCESSING_MINUTES_PER_PAGE = 3


class StaleProcessingLease(RuntimeError):
    """The worker no longer owns a live fence and must discard its result."""


def _source_identity(
    *, source_capture: SourceCapture | None, customer_uploaded_document_id: uuid.UUID | None
) -> dict[str, str | None]:
    return {
        "source_capture_id": str(source_capture.id) if source_capture else None,
        "source_sha256": (
            source_capture.original_file.sha256
            if source_capture and source_capture.original_file
            else None
        ),
        "customer_uploaded_document_id": (
            str(customer_uploaded_document_id) if customer_uploaded_document_id else None
        ),
    }


def _rule_scope_identity(source_capture: SourceCapture | None) -> list[dict[str, str]]:
    if source_capture is None or source_capture.document_version_id is None:
        return []
    policy_ids = PolicyVersionDocument.objects.filter(
        document_version_id=source_capture.document_version_id
    ).values_list("policy_version_id", flat=True)
    return [
        {
            "id": str(identifier),
            "policy_version_id": str(policy_version_id),
            "name": name,
        }
        for identifier, policy_version_id, name in ProductVariant.objects.filter(
            policy_version_id__in=policy_ids
        )
        .order_by("policy_version_id", "id")
        .values_list("id", "policy_version_id", "name")
    ]


def _embedding_scope_identity() -> dict[str, object]:
    ready, reason, qualification = qualified_embedding_status()
    return {
        "ready": ready,
        "reason": reason,
        "index_version": (
            policy_index_version(qualification) if ready and qualification is not None else None
        ),
    }


@transaction.atomic
def enqueue_stage(
    *,
    stage: str,
    source_capture: SourceCapture | None = None,
    customer_uploaded_document_id: uuid.UUID | None = None,
    owner_id: uuid.UUID | None = None,
    parent_job: ProcessingJob | None = None,
    attempt_number: int = 1,
    retry_instruction: str | None = None,
) -> ProcessingJob:
    if stage not in STAGE_RUNNERS:
        raise ValueError(f"Unsupported processing stage: {stage}")
    if (source_capture is None) == (customer_uploaded_document_id is None):
        raise ValueError("Exactly one public capture or customer document is required.")
    if attempt_number < 1 or attempt_number > 3:
        raise ValueError("Processing stages permit one initial attempt and two retries.")
    input_data: dict[str, Any] = {
        **_source_identity(
            source_capture=source_capture,
            customer_uploaded_document_id=customer_uploaded_document_id,
        ),
        "stage": stage,
        "adapter_version": ADAPTER_VERSION,
        "parent_result_sha256": parent_job.result_storage_sha256 if parent_job else None,
        "retry_instruction": retry_instruction,
    }
    if stage in {"extract", "independent_review", "validate"}:
        input_data["rule_prompt_version"] = RULE_PROMPT_VERSION
        input_data["comparison_variants"] = _rule_scope_identity(source_capture)
    if stage in {"extract", "independent_review"}:
        input_data["max_model_passage_characters"] = MAX_MODEL_PASSAGE_CHARACTERS
    if stage == "extract":
        input_data["requested_model"] = settings.COVERGUIDE_POLICY_EXTRACTION_MODEL
    if stage == "independent_review":
        input_data["rule_review_prompt_version"] = RULE_REVIEW_PROMPT_VERSION
        input_data["requested_model"] = settings.COVERGUIDE_POLICY_REVIEW_MODEL
    if stage == "validate":
        input_data["rule_review_prompt_version"] = RULE_REVIEW_PROMPT_VERSION
        input_data["requested_models"] = {
            "extraction": settings.COVERGUIDE_POLICY_EXTRACTION_MODEL,
            "independent_review": settings.COVERGUIDE_POLICY_REVIEW_MODEL,
        }
    if stage == "validate":
        input_data["rule_validator_version"] = RULE_VALIDATOR_VERSION
    if stage == "index":
        input_data["embedding"] = _embedding_scope_identity()
    if stage == "reconcile":
        input_data["reconciliation_version"] = RECONCILIATION_VERSION
    input_commitment = commitment(input_data)
    lookup = {
        "stage": stage,
        "input_commitment": input_commitment,
        "attempt_number": attempt_number,
    }
    if source_capture:
        lookup["source_capture"] = source_capture
    else:
        lookup["customer_uploaded_document_id"] = customer_uploaded_document_id
    job, created = ProcessingJob.objects.get_or_create(
        **lookup,
        defaults={
            "owner_id": owner_id,
            "parent_job": parent_job,
            "adapter_version": ADAPTER_VERSION,
        },
    )
    if created:
        Outbox.objects.create(
            owner_id=owner_id,
            event_type="document_processing",
            processing_job=job,
            idempotency_key=f"document:{job.id}",
        )
    return job


def _set_lease_token(token: uuid.UUID) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('coverguide.lease_token', %s, true)", [str(token)])


def _set_expired_lease_recovery() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('coverguide.recover_expired_lease', 'true', true)")


def _processing_lease_duration(job: ProcessingJob) -> timedelta:
    if job.stage == "index":
        return INDEX_PROCESSING_LEASE
    if job.stage != "read":
        return DEFAULT_PROCESSING_LEASE
    original_file_id: uuid.UUID | None = None
    if job.source_capture_id and job.source_capture is not None:
        original_file_id = job.source_capture.original_file_id
    elif job.customer_uploaded_document_id and job.customer_uploaded_document is not None:
        original_file_id = job.customer_uploaded_document.original_file_id
    page_count = (
        DocumentPage.objects.filter(original_file_id=original_file_id).count()
        if original_file_id is not None
        else 0
    )
    scaled = timedelta(minutes=page_count * READ_PROCESSING_MINUTES_PER_PAGE)
    return min(MAX_READ_PROCESSING_LEASE, max(READ_PROCESSING_LEASE, scaled))


@transaction.atomic
def _claim_job(job_id: uuid.UUID) -> tuple[ProcessingJob, uuid.UUID, int | None] | None:
    job = (
        ProcessingJob.objects.select_for_update(of=("self",))
        .select_related(
            "source_capture__original_file",
            "source_capture__document_version__document_series",
            "customer_uploaded_document__original_file",
            "parent_job",
        )
        .get(pk=job_id)
    )
    now = timezone.now()
    if job.state == "running" and job.lease_until is not None and job.lease_until <= now:
        _set_expired_lease_recovery()
        job.state = "queued"
        job.lease_token = None
        job.lease_until = None
        job.save(update_fields=["state", "lease_token", "lease_until", "updated_at"])
        AuditEvent.objects.create(
            owner_id=job.owner_id,
            operation="processing_lease_recovered",
            object_kind="processing_job",
            object_id=job.id,
            outcome="succeeded",
            metadata={
                "error_code": "processing_lease_expired",
                "affected_count": 1,
                "authorization_basis_code": "expired_database_worker_fence",
            },
        )
    if job.state != "queued":
        raise ValueError("job_not_queued")
    owner_generation: int | None = None
    if job.owner_id is not None:
        owner = User.objects.select_for_update().get(pk=job.owner_id)
        if owner.deleted_at is not None or not owner.is_active:
            job.state = "cancelled"
            job.error_code = "account_erased"
            job.save(update_fields=["state", "error_code", "updated_at"])
            Outbox.objects.filter(processing_job=job, event_type="document_processing").delete()
            return None
        owner_generation = owner.erasure_generation
    token = uuid.uuid4()
    job.state = "running"
    job.lease_token = token
    lease_duration = _processing_lease_duration(job)
    job.lease_until = now + lease_duration
    job.save(update_fields=["state", "lease_token", "lease_until", "updated_at"])
    Outbox.objects.filter(processing_job=job, event_type="document_processing").update(
        state="delivered", lease_until=None, last_error_code=None
    )
    return job, token, owner_generation


@transaction.atomic
def _finish_job(
    job: ProcessingJob,
    token: uuid.UUID,
    *,
    state: str,
    result: dict[str, Any] | None,
    issues: list[dict[str, Any]],
    expected_erasure_generation: int | None,
    error_code: str | None = None,
) -> ProcessingJob:
    if job.owner_id is not None:
        owner = User.objects.select_for_update().get(pk=job.owner_id)
        if (
            owner.erasure_generation != expected_erasure_generation
            or owner.deleted_at is not None
            or not owner.is_active
        ):
            raise AccountErased("account_erased")
    current = ProcessingJob.objects.select_for_update().get(pk=job.id)
    if (
        current.state != "running"
        or current.lease_token != token
        or current.lease_until is None
        or current.lease_until <= timezone.now()
    ):
        raise StaleProcessingLease("processing_lease_stale")
    _set_lease_token(token)
    if result is not None:
        storage_key, storage_sha256 = write_artifact(current, result)
        current.result_storage_key = storage_key
        current.result_storage_sha256 = storage_sha256
    current.state = state
    current.issues = issues
    current.error_code = error_code
    current.save(
        update_fields=[
            "state",
            "issues",
            "error_code",
            "result_storage_key",
            "result_storage_sha256",
            "updated_at",
        ]
    )
    return current


def _source_arguments(job: ProcessingJob) -> dict[str, Any]:
    return {
        "source_capture": job.source_capture if job.source_capture_id else None,
        "customer_uploaded_document_id": job.customer_uploaded_document_id,
        "owner_id": job.owner_id,
    }


def _enqueue_retry(job: ProcessingJob, description: str) -> ProcessingJob | None:
    if job.attempt_number >= 3:
        return None
    return enqueue_stage(
        stage=job.stage,
        parent_job=job.parent_job,
        attempt_number=job.attempt_number + 1,
        retry_instruction=description,
        **_source_arguments(job),
    )


def _material_issues(result: dict[str, Any], stage: str) -> list[dict[str, Any]]:
    values = result.get("issues", [])
    issues = [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []
    if stage == "extract":
        for description in result.get("material_issues", []):
            issues.append(
                issue(
                    "extraction_material_issue",
                    str(description),
                    material=False,
                    retry_instruction="Keep this category unknown until supported evidence agrees.",
                )
            )
        omitted = result.get("omitted_inventory_categories", [])
        if omitted:
            issues.append(
                issue(
                    "omitted_inventory_categories",
                    ", ".join(str(item) for item in omitted),
                    material=False,
                    retry_instruction="Keep omitted categories unknown in the alpha release.",
                )
            )
    return issues


def _process_claimed_job(
    job: ProcessingJob,
    token: uuid.UUID,
    erasure_generation: int | None,
) -> None:
    runner = STAGE_RUNNERS[job.stage]
    try:
        result = runner(job)
        issues = _material_issues(result, job.stage)
        material = [item for item in issues if item.get("material") and not item.get("resolved")]
        if material:
            completed = _finish_job(
                job,
                token,
                state="blocked",
                result=result,
                issues=issues,
                expected_erasure_generation=erasure_generation,
                error_code=str(material[0].get("code", "material_processing_issue")),
            )
            return
        completed = _finish_job(
            job,
            token,
            state="succeeded",
            result=result,
            issues=issues,
            expected_erasure_generation=erasure_generation,
        )
    except DependencyUnavailable as exc:
        dependency_issue = issue(
            "dependency_unavailable",
            str(exc),
            material=True,
            retry_instruction="Install and pin the exact local dependency artifact, then retry.",
        )
        _finish_job(
            job,
            token,
            state="blocked",
            result=None,
            issues=[dependency_issue],
            expected_erasure_generation=erasure_generation,
            error_code="dependency_unavailable",
        )
        return
    except RelayFailure as exc:
        relay_issue = issue(
            exc.code,
            str(exc),
            material=True,
            retry_instruction="Retry this visible processing stage with the same qualified route.",
        )
        failed = _finish_job(
            job,
            token,
            state="failed",
            result=None,
            issues=[relay_issue],
            expected_erasure_generation=erasure_generation,
            error_code=exc.code,
        )
        if exc.code in RETRYABLE_RELAY_CODES and job.stage not in {
            "extract",
            "independent_review",
        }:
            _enqueue_retry(failed, relay_issue["retry_instruction"])
        return
    except ValueError as exc:
        validation_issue = issue(
            "processing_validation_failed",
            str(exc),
            material=True,
            retry_instruction="Inspect the exact stage inputs and correct the identified conflict.",
        )
        _finish_job(
            job,
            token,
            state="blocked",
            result=None,
            issues=[validation_issue],
            expected_erasure_generation=erasure_generation,
            error_code="processing_validation_failed",
        )
        return
    except AccountErased:
        return
    except Exception:
        _finish_job(
            job,
            token,
            state="failed",
            result=None,
            issues=[
                issue(
                    "technical_failure",
                    "The document stage failed unexpectedly; no policy result was published.",
                    material=True,
                    retry_instruction="Inspect server diagnostics before a visible retry.",
                )
            ],
            expected_erasure_generation=erasure_generation,
            error_code="technical_failure",
        )
        raise
    next_stage = NEXT_STAGE.get(completed.stage)
    if next_stage:
        enqueue_stage(
            stage=next_stage,
            parent_job=completed,
            **_source_arguments(completed),
        )


def process_job(job_id: uuid.UUID) -> None:
    try:
        claimed = _claim_job(job_id)
    except ValueError as exc:
        if str(exc) == "job_not_queued":
            return
        raise
    if claimed is None:
        return
    try:
        _process_claimed_job(*claimed)
    except StaleProcessingLease:
        return
