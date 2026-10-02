import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from apps.adviser_v2.demo.cards import PROJECTION_VERSION, build_card, reproject_card
from apps.adviser_v2.demo.charts import parse_chart
from apps.adviser_v2.demo.contracts import PlanCard
from apps.adviser_v2.demo.evidence import atomic_json
from apps.adviser_v2.demo.services import bundle_for
from apps.adviser_v2.models import DemoPlanIndex


class Command(BaseCommand):
    help = 'Generate cited offline cards and structural premium tables using only the frozen winner.'

    def add_arguments(self, parser):
        parser.add_argument('--charts', action='store_true')

    def handle(self, **options):
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / 'ten-insurer'
        outcome_file = root / 'bakeoff-v2/result.json'
        if not outcome_file.exists():
            raise CommandError('The single frozen bake-off must finish first.')
        outcome = json.loads(outcome_file.read_text())
        method = outcome['winner']
        rows = list(DemoPlanIndex.objects.order_by('plan_key', '-created_at').distinct('plan_key'))
        close_old_connections()

        def build(row):
            close_old_connections()
            try:
                card = PlanCard.model_validate(row.card)
                if card.status == 'documents_unavailable':
                    return row.name + ': documents unavailable'
                if row.demorelease_set.exists():
                    return row.name + ': already pinned in a release; preserved'
                close_old_connections()  # Do not hold a pool slot while child field jobs run.
                path = root / 'cards' / (row.id + '.json')
                bundle = bundle_for(row)
                if path.exists():
                    saved = json.loads(path.read_text())
                    if saved['method'] != method:
                        raise ValueError('Card cache uses a different retrieval method.')
                    card = PlanCard.model_validate(saved['card'])
                    if saved['audit'].get('projection_version') != PROJECTION_VERSION:
                        card = reproject_card(card, saved['audit'])
                        saved['card'] = card.model_dump()
                        saved['audit']['projection_version'] = PROJECTION_VERSION
                        atomic_json(path, saved)
                else:
                    card, audit = build_card(bundle, card, method, cache_root=root / 'card-groups')
                    atomic_json(path, {'method': method, 'card': card.model_dump(), 'audit': audit})
                row.card = card.model_dump()
                row.coverage = {**row.coverage, 'card_status': card.status}
                row.save(update_fields=['card', 'coverage'])
                if options['charts']:
                    parse_chart(bundle, root)
                return row.name + ': ' + card.status
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=4) as pool:
            jobs = {pool.submit(build, row): row for row in rows}
            failed = []
            for future in as_completed(jobs):
                try:
                    self.stdout.write(future.result())
                except Exception as exc:
                    # A failed plan must not discard completed work for other insurers.
                    failed.append({'index': jobs[future].id, 'reason': str(exc)})
                    self.stderr.write(jobs[future].name + ': pending: ' + str(exc))
                self.stdout.flush()
            atomic_json(root / 'card-failures.json', failed)
            if failed:
                raise CommandError(f'{len(failed)} cards remain pending; completed groups are cached.')
