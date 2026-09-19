"""Record an explicit decision for one blocked document classification."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.adviser_v2.models import ProcessingJob
from apps.adviser_v2.pipeline import enqueue_stage
from apps.adviser_v2.processing.adjudication import adjudicate_classification


class Command(BaseCommand):
    help = "Adjudicate one preserved classifier disagreement after exact-document review."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("job_id", type=uuid.UUID)
        parser.add_argument("--kind", required=True)
        parser.add_argument("--note", required=True)

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            job = adjudicate_classification(options["job_id"], options["kind"], options["note"])
            enqueue_stage(
                stage="read",
                source_capture=job.source_capture if job.source_capture_id else None,
                customer_uploaded_document_id=job.customer_uploaded_document_id,
                owner_id=job.owner_id,
                parent_job=job,
            )
        except (ValueError, OSError, ProcessingJob.DoesNotExist) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Classification {job.id} accepted as {options['kind']}; read stage queued."
            )
        )
