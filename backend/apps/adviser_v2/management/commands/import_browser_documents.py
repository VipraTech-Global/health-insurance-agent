import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.adviser_v2.demo.browser_sources import import_candidate
from apps.adviser_v2.demo.evidence import atomic_json


class Command(BaseCommand):
    help = "Validate official browser PDF responses; retain candidates outside the frozen corpus."

    def handle(self, **options):
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
        rows = []
        for path in sorted((root / "browser-documents").glob("*.json")):
            for value in json.loads(path.read_text()):
                row = import_candidate(value, root)
                rows.append(row)
                self.stdout.write(
                    json.dumps(
                        {
                            k: row.get(k)
                            for k in (
                                "insurer_id",
                                "role",
                                "status",
                                "physical_pages",
                                "sha256",
                                "reason",
                            )
                        }
                    )
                )
        atomic_json(root / "retry-flagship-candidates.json", rows)
