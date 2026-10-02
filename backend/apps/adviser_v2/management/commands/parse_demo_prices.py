"""Parse source premium tables independently of card and release publication."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from apps.adviser_v2.demo.charts import parse_chart
from apps.adviser_v2.demo.evidence import atomic_json
from apps.adviser_v2.demo.services import bundle_for
from apps.adviser_v2.models import DemoPlanIndex


class Command(BaseCommand):
    help = __doc__

    def handle(self, **options):
        if settings.DATABASES['default']['NAME'] != 'coverguide_star_slice':
            raise CommandError('Premium processing is restricted to the isolated demo database.')
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / 'ten-insurer'
        rows = list(DemoPlanIndex.objects.filter(revoked_at__isnull=True).order_by('plan_key', '-created_at').distinct('plan_key'))
        close_old_connections()

        def parse(row):
            if row.card.get('status') == 'documents_unavailable':
                return 'documents unavailable'
            result = parse_chart(bundle_for(row), root)
            return f"{result['status']}; {len(result['prices'])} exact printed prices"

        failures = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = {pool.submit(parse, row): row for row in rows}
            for future in as_completed(jobs):
                row = jobs[future]
                try:
                    self.stdout.write(row.name + ': ' + future.result())
                except Exception as exc:
                    failures.append({'index_id': row.id, 'reason': str(exc)})
                    self.stderr.write(row.name + ': pending: ' + str(exc))
                self.stdout.flush()
        atomic_json(root / 'premium-failures.json', failures)
        if failures:
            raise CommandError(f'{len(failures)} price jobs remain pending; successful tables are cached.')
