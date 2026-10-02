"""Build shared demo maps and source sections without touching historical artifacts."""

import json
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.adviser_v2.demo.mapping import build_corpus


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--corpus", type=Path)
        parser.add_argument("--workers", type=int, default=4)
        parser.add_argument("--resume-pending", action="store_true")

    def handle(self, **options):
        root = Path(settings.COVERGUIDE_REPORT_ROOT)
        corpus = options["corpus"] or root / "retrieval-benchmark/corpus.json"
        while True:
            result = build_corpus(json.loads(corpus.read_text()), root / "ten-insurer", workers=options["workers"])
            self.stdout.write(json.dumps({"plans": len(result["plans"]), "failures": result["failures"]}))
            self.stdout.flush()
            if not options["resume_pending"] or not any(f["status"] == "pending" for f in result["failures"].values()):
                return
            time.sleep(30)
