import json
import os
import tempfile
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from apps.adviser.models import (
    CatalogueListing,
    DocumentVersion,
    ExtractionRevision,
    PlanVersion,
    VerifiedFact,
)


class Command(BaseCommand):
    help = "Write a reproducible catalogue and evidence coverage report."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--output", required=True)

    def handle(self, *args: Any, **options: Any) -> None:
        database_listings = list(
            CatalogueListing.objects.select_related("insurer")
            .order_by("ditto_path")
            .values(
                "ditto_path",
                "displayed_name",
                "insurer__name",
                "status",
                "status_reason",
                "last_observed_at",
            )
        )
        counts: dict[str, int] = {}
        listings: list[dict[str, Any]] = []
        for listing in database_listings:
            status = str(listing["status"])
            counts[status] = counts.get(status, 0) + 1
            listings.append(
                {
                    **listing,
                    "last_observed_at": listing["last_observed_at"].isoformat(),
                }
            )
        report = {
            "schema_version": 1,
            "generated_at": timezone.now().isoformat(),
            "summary": {
                "discovered": len(listings),
                "status_counts": counts,
                "plan_versions": PlanVersion.objects.count(),
                "documents": DocumentVersion.objects.count(),
                "extraction_revisions": ExtractionRevision.objects.count(),
                "published_extractions": ExtractionRevision.objects.filter(published=True).count(),
                "verified_facts": VerifiedFact.objects.filter(
                    verification_state="verified", conflict=False
                ).count(),
                "active_for_recommendation": counts.get("active", 0),
            },
            "listings": listings,
        }
        output = Path(str(options["output"])).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        content = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
        with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, output)
        self.stdout.write(self.style.SUCCESS(f"Wrote {len(listings)} listings to {output}."))
