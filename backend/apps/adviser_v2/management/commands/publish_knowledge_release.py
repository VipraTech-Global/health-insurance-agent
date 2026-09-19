"""Atomically activate one already-ready knowledge release."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.adviser_v2.models import KnowledgeRelease
from apps.adviser_v2.services.releases import publish_release


class Command(BaseCommand):
    help = "Publish and atomically select one release after rechecking all gates."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("release_id", type=uuid.UUID)

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            release = publish_release(options["release_id"])
        except KnowledgeRelease.DoesNotExist as exc:
            raise CommandError("Knowledge release does not exist.") from exc
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Published release {release.release_number} ({release.id}) at {release.published_at}."
            )
        )
