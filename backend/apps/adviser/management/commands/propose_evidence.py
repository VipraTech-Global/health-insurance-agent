import uuid
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.adviser.evidence import create_evidence_bundle
from apps.adviser.models import DocumentPage
from apps.adviser.source_maps import DocumentValidationError


class Command(BaseCommand):
    help = "Create a pending evidence bundle from frozen application reference lines."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("extraction_revision_id", type=uuid.UUID)
        parser.add_argument("page", type=int, help="One-based physical PDF page")
        parser.add_argument("start_line", type=int)
        parser.add_argument("end_line", type=int)
        parser.add_argument("--label", required=True)

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            page = DocumentPage.objects.select_related("extraction_revision").get(
                extraction_revision_id=options["extraction_revision_id"],
                physical_index=int(options["page"]) - 1,
            )
            bundle = create_evidence_bundle(
                page,
                int(options["start_line"]),
                int(options["end_line"]),
                str(options["label"]),
            )
        except DocumentPage.DoesNotExist as exc:
            raise CommandError("Extraction page does not exist.") from exc
        except DocumentValidationError as exc:
            raise CommandError(str(exc)) from exc
        span = bundle.spans.get()
        self.stdout.write(
            self.style.SUCCESS(
                f"Created pending bundle {bundle.id}; evidence span {span.id}: {span.quote}"
            )
        )
