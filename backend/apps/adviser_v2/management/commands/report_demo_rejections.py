import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.adviser_v2.demo.evidence import atomic_json
from apps.adviser_v2.demo.rejection_report import summarize_rejections


class Command(BaseCommand):
    help = 'Report paraphrase-only rejections from completed, immutable bake-off pairs.'

    def handle(self, **options):
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / 'ten-insurer/bakeoff-v2'
        if not (root / 'result.json').exists():
            raise CommandError('Wait for the frozen bake-off to finish; no partial outcome inspection.')
        outcome = json.loads((root / 'result.json').read_text())
        rows = [json.loads(p.read_text()) for p in sorted((root / outcome.get('pairs_directory', 'pairs')).glob('*.json'))]
        value = summarize_rejections(rows)
        atomic_json(root / 'paraphrase-rejections.json', value)
        atomic_json(Path(settings.BASE_DIR).parent / 'output/paraphrase-rejections.json', value)
        self.stdout.write(json.dumps(value, indent=2))
