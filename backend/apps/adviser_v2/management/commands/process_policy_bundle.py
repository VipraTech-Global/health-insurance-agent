"""Run the resumable pipeline for one exact policy bundle."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.adviser_v2.models import (
    PolicyVersion,
    PolicyVersionDocument,
    ProcessingJob,
    SourceCapture,
)
from apps.adviser_v2.pipeline import ADAPTER_VERSION, enqueue_stage, process_job
from apps.adviser_v2.processing.adjudication import synchronize_reconciliation_evidence
from apps.adviser_v2.processing.identity import (
    reconcile_capture_identity,
    verify_observed_identity,
)
from apps.adviser_v2.storage import read_public


class Command(BaseCommand):
    help = "Idempotently process every captured document in one exact policy version."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("policy_version_id", type=uuid.UUID)
        parser.add_argument("--retry-blocked", action="store_true")
        parser.add_argument(
            "--documents-only",
            action="store_true",
            help="Stop after every fixed-manifest document has reconciled.",
        )

    def _drain(self, capture: SourceCapture) -> None:
        while True:
            queued = (
                ProcessingJob.objects.filter(
                    source_capture=capture,
                    adapter_version=ADAPTER_VERSION,
                    state="queued",
                )
                .order_by("created_at")
                .first()
            )
            if queued is None:
                return
            process_job(queued.id)

    @staticmethod
    def _stage_failure(stage: str, job: ProcessingJob | None) -> CommandError:
        if job is None:
            return CommandError(f"Policy bundle stopped before {stage}: stage_not_enqueued.")
        issue_codes = sorted(
            {
                str(item.get("code"))
                for item in job.issues
                if isinstance(item, dict) and item.get("code")
            }
        )
        details = ",".join(issue_codes[:5]) or job.error_code or "no_recorded_issue"
        return CommandError(
            f"Policy bundle stopped at {stage} attempt {job.attempt_number}: "
            f"state={job.state}; error={job.error_code or 'none'}; issues={details}."
        )

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            policy_version = PolicyVersion.objects.select_related("product__insurer").get(
                pk=options["policy_version_id"]
            )
        except PolicyVersion.DoesNotExist as exc:
            raise CommandError("Policy version does not exist.") from exc
        uin = policy_version.uin
        if not uin:
            raise CommandError("Policy version has no exact UIN.")
        memberships = list(
            PolicyVersionDocument.objects.filter(policy_version=policy_version).select_related(
                "document_version"
            )
        )
        if not memberships:
            raise CommandError("Policy version has no captured bundle membership.")
        captures: list[SourceCapture] = []
        for membership in memberships:
            capture = (
                SourceCapture.objects.filter(
                    document_version=membership.document_version,
                    status="captured",
                    original_file__isnull=False,
                )
                .select_related("original_file", "document_version__document_series")
                .order_by("-completed_at")
                .first()
            )
            if capture is None:
                raise CommandError(
                    f"Bundle document {membership.document_version_id} has no successful capture."
                )
            assert capture.original_file is not None
            reconcile_capture_identity(
                capture,
                read_public(
                    capture.original_file.storage_key,
                    capture.original_file.sha256,
                ),
                uin=uin,
                issuer=policy_version.product.insurer.name,
                notes=[f"Fixed manifest membership role: {membership.role}."],
                record_audit=True,
            )
            captures.append(capture)
            root = enqueue_stage(stage="classify", source_capture=capture)
            if options["retry_blocked"]:
                latest = (
                    ProcessingJob.objects.filter(
                        source_capture=capture,
                        adapter_version=ADAPTER_VERSION,
                    )
                    .order_by("-created_at")
                    .first()
                )
                if latest and latest.state in {"blocked", "failed"} and latest.attempt_number < 3:
                    enqueue_stage(
                        stage=latest.stage,
                        source_capture=capture,
                        parent_job=latest.parent_job,
                        attempt_number=latest.attempt_number + 1,
                        retry_instruction="Explicit operator retry after resolving the recorded blocker.",
                    )
            self._drain(capture)
            latest_ocr = (
                ProcessingJob.objects.filter(
                    source_capture=capture,
                    adapter_version=ADAPTER_VERSION,
                    stage="ocr",
                    state="succeeded",
                )
                .order_by("-created_at")
                .first()
            )
            if latest_ocr is not None:
                enqueue_stage(
                    stage="reconcile",
                    source_capture=capture,
                    parent_job=latest_ocr,
                )
                self._drain(capture)
            root.refresh_from_db()
        document_blockers: list[tuple[uuid.UUID, str, str, str | None]] = []
        reconciled_capture_ids: set[uuid.UUID] = set()
        for capture in captures:
            latest = (
                ProcessingJob.objects.filter(
                    source_capture=capture,
                    adapter_version=ADAPTER_VERSION,
                )
                .order_by("-created_at")
                .first()
            )
            reconcile = (
                ProcessingJob.objects.filter(
                    source_capture=capture,
                    adapter_version=ADAPTER_VERSION,
                    stage="reconcile",
                )
                .order_by("-created_at")
                .first()
            )
            if reconcile is not None and reconcile.state == "succeeded":
                synchronize_reconciliation_evidence(reconcile.id)
                verify_observed_identity(capture, uin=uin)
                reconciled_capture_ids.add(capture.id)
            elif latest is not None:
                document_blockers.append(
                    (capture.id, latest.stage, latest.state, latest.error_code)
                )
        if len(reconciled_capture_ids) != len(captures):
            raise CommandError(
                f"Bundle stopped before rule extraction; current blockers={document_blockers}."
            )
        if options["documents_only"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Policy bundle {policy_version.id} reconciled all {len(captures)} documents."
                )
            )
            return
        base_membership = next((item for item in memberships if item.role == "base_wording"), None)
        if base_membership is None:
            raise CommandError("Bundle has no base-wording membership.")
        base_capture = next(
            item
            for item in captures
            if item.document_version_id == base_membership.document_version_id
        )
        reconcile = (
            ProcessingJob.objects.filter(
                source_capture=base_capture,
                adapter_version=ADAPTER_VERSION,
                stage="reconcile",
                state="succeeded",
            )
            .order_by("-created_at")
            .first()
        )
        assert reconcile is not None
        extraction_root = enqueue_stage(
            stage="extract", source_capture=base_capture, parent_job=reconcile
        )
        self._drain(base_capture)
        latest_extraction = (
            ProcessingJob.objects.filter(
                source_capture=base_capture,
                adapter_version=ADAPTER_VERSION,
                stage="extract",
                parent_job=reconcile,
                created_at__gte=extraction_root.created_at,
            )
            .order_by("-created_at", "-attempt_number")
            .first()
        )
        if latest_extraction is None or latest_extraction.state != "succeeded":
            raise self._stage_failure("extract", latest_extraction)
        latest_review = (
            ProcessingJob.objects.filter(
                source_capture=base_capture,
                adapter_version=ADAPTER_VERSION,
                stage="independent_review",
                parent_job=latest_extraction,
            )
            .order_by("-attempt_number", "-created_at")
            .first()
        )
        if latest_review is None or latest_review.state != "succeeded":
            raise self._stage_failure("independent_review", latest_review)
        latest_validation = (
            ProcessingJob.objects.filter(
                source_capture=base_capture,
                adapter_version=ADAPTER_VERSION,
                stage="validate",
                parent_job=latest_review,
            )
            .order_by("-attempt_number", "-created_at")
            .first()
        )
        if latest_validation is None or latest_validation.state != "succeeded":
            raise self._stage_failure("validate", latest_validation)
        latest_index = (
            ProcessingJob.objects.filter(
                source_capture=base_capture,
                adapter_version=ADAPTER_VERSION,
                stage="index",
                parent_job=latest_validation,
            )
            .order_by("-attempt_number", "-created_at")
            .first()
        )
        if latest_index is None or latest_index.state != "succeeded":
            raise self._stage_failure("index", latest_index)
        self.stdout.write(
            self.style.SUCCESS(
                f"Policy bundle {policy_version.id} processed, independently validated and indexed."
            )
        )
