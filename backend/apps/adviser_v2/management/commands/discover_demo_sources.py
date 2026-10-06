import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.adviser_v2.demo.acquisition import discover_all
from apps.adviser_v2.demo.evidence import atomic_json


class Command(BaseCommand):
    help = "Refresh official ten-insurer source links; never imply applicability from download success."

    def handle(self, **options):
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer/discovery"
        rows = discover_all(root)
        atomic_json(root / "register.json", rows)
        self.stdout.write(
            json.dumps(
                [
                    {
                        "insurer": r["insurer"],
                        "status": r["status"],
                        "documents": len(r["documents"]),
                    }
                    for r in rows
                ]
            )
        )
