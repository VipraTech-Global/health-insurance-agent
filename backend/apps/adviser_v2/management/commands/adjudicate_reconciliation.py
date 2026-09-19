"""Resolve exact page-reader conflicts after explicit visual inspection."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, cast

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.adviser_v2.models import ProcessingJob
from apps.adviser_v2.processing.adjudication import (
    ReaderSelection,
    adjudicate_reconciliation,
)


class Command(BaseCommand):
    help = "Visually adjudicate the exact unresolved pages of one reconciliation job."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("job_id", type=uuid.UUID)
        parser.add_argument(
            "--selection",
            action="append",
            required=True,
            metavar="PAGE=READER",
            help="Select native, ocr or manual for one visually inspected physical page.",
        )
        parser.add_argument(
            "--transcription",
            action="append",
            default=[],
            metavar="PAGE=PATH",
            help="UTF-8 exact-page transcription required for each PAGE=manual selection.",
        )
        parser.add_argument("--review-note", required=True)

    def handle(self, *args: Any, **options: Any) -> None:
        selections: dict[int, ReaderSelection] = {}
        transcriptions: dict[int, str] = {}
        try:
            for raw in options["selection"]:
                page_text, reader = str(raw).split("=", 1)
                page_number = int(page_text)
                if page_number < 1 or reader not in {"native", "ocr", "manual"}:
                    raise ValueError
                if page_number in selections:
                    raise ValueError
                selections[page_number] = cast(ReaderSelection, reader)
            for raw in options["transcription"]:
                page_text, path_text = str(raw).split("=", 1)
                page_number = int(page_text)
                if page_number < 1 or page_number in transcriptions:
                    raise ValueError
                transcriptions[page_number] = Path(path_text).read_text(encoding="utf-8")
            job = adjudicate_reconciliation(
                options["job_id"],
                selections,
                str(options["review_note"]),
                manual_transcriptions=transcriptions,
            )
        except (OSError, UnicodeError, ValueError, ProcessingJob.DoesNotExist) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Reconciliation {job.id} succeeded after {len(selections)}-page visual adjudication."
            )
        )
