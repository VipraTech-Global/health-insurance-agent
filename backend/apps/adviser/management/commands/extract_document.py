import uuid
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.adviser.models import DocumentVersion
from apps.adviser.source_maps import DocumentValidationError, extract_native_document


class Command(BaseCommand):
    help = "Create an immutable native-text source-map revision."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("document_id", type=uuid.UUID)

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            document = DocumentVersion.objects.select_related("blob").get(id=options["document_id"])
            revision = extract_native_document(document)
        except DocumentVersion.DoesNotExist as exc:
            raise CommandError("Document does not exist.") from exc
        except DocumentValidationError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Created extraction revision {revision.revision}: {revision.id} (pending review)."
            )
        )
