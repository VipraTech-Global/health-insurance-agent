import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.adviser_v2.demo.evidence import digest
from apps.adviser_v2.models import DemoFactCard, DemoRelease


class Command(BaseCommand):
    help = "Publish a local immutable-card release without rebuilding indexes."

    def add_arguments(self, parser):
        parser.add_argument("--run-id", required=True)
        parser.add_argument("--priority", action="store_true")
        parser.add_argument("--inactive", action="store_true")

    @transaction.atomic
    def handle(self, **options):
        if settings.DATABASES["default"]["NAME"] != "coverguide_star_slice":
            raise CommandError("Local isolated database only.")
        root = (
            Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer/fact-card-runs" / options["run_id"]
        )
        source = root / ("priority.json" if options["priority"] else "complete.json")
        if not source.exists():
            raise CommandError("Requested card batch is not complete.")
        saved = json.loads(source.read_text())
        if saved.get("failures"):
            raise CommandError("Resolve pending cards before publishing this batch.")
        ids = [r["id"] for r in saved["cards"]]
        cards = list(DemoFactCard.objects.filter(pk__in=ids).select_related("index"))
        if len(cards) != len(ids) or len({c.index.plan_key for c in cards}) != len(cards):
            raise CommandError("Incomplete or duplicate plan-card identities.")
        previous = DemoRelease.objects.select_for_update().get(active=True)
        identity = digest({"cards": sorted(ids), "method": "H"})
        existing = DemoRelease.objects.filter(manifest_sha256=identity).first()
        if existing:
            if not options["inactive"] and not existing.active:
                previous.active = False
                previous.save(update_fields=["active"])
                existing.active = True
                existing.save(update_fields=["active"])
            self.stdout.write(str(existing.id))
            return
        if not options["inactive"]:
            previous.active = False
            previous.save(update_fields=["active"])
        release = DemoRelease.objects.create(
            label="section16_cards",
            method="H",
            manifest_sha256=identity,
            bakeoff=previous.bakeoff,
            active=not options["inactive"],
        )
        release.indexes.set([c.index for c in cards])
        release.fact_cards.set(cards)
        self.stdout.write(
            json.dumps({"release": str(release.id), "cards": len(cards), "indexes_reused": True})
        )
