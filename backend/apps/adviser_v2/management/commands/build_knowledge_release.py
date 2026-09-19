"""Build an immutable-membership candidate release from one captured manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.adviser_v2.services.releases import build_release


class Command(BaseCommand):
    help = "Build a release from one exact five-product manifest."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("manifest", type=Path)
        parser.add_argument(
            "--three-product-demo",
            action="store_true",
            help=(
                "Publish only the first three fully ready manifest products as an explicitly "
                "restricted development demo."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            release, report = build_release(
                options["manifest"].resolve(),
                comparison_product_count=3 if options["three_product_demo"] else 5,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            json.dumps(
                {"release_id": str(release.id), "state": release.state, "report": report},
                indent=2,
                sort_keys=True,
            )
        )
        if release.state != "ready" and release.state != "published":
            raise CommandError("Release was recorded as blocked; no publication occurred.")
