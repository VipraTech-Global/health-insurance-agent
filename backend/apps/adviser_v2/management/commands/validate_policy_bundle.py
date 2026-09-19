"""Report exact bundle gates without mutating processing or publication state."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.adviser_v2.readiness import load_captured_manifest, validate_bundle


class Command(BaseCommand):
    help = "Validate one policy bundle against its exact captured manifest membership."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("policy_version_id", type=uuid.UUID)
        parser.add_argument("--manifest", required=True, type=Path)

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            manifest = load_captured_manifest(options["manifest"].resolve())
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        expected = str(options["policy_version_id"])
        product = next(
            (item for item in manifest["products"] if item.get("policy_version_id") == expected),
            None,
        )
        if product is None:
            raise CommandError("Policy version is not present in this captured manifest.")
        report = validate_bundle(product)
        self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        if not report["ready"]:
            raise CommandError("Policy bundle did not pass all publication gates.")
