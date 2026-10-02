import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.adviser_v2.demo.evaluation import freeze_run, make_jobs, run_job, score_rows, write_report
from apps.adviser_v2.demo.evidence import atomic_json
from apps.adviser_v2.models import DemoPlanIndex, DemoSectionVector


class Command(BaseCommand):
    help = 'Freeze or resume the single protocol-v2 H/P comparison; never tune a scored run.'

    def add_arguments(self, parser):
        parser.add_argument('--freeze-only', action='store_true')
        parser.add_argument('--workers', type=int, default=6)

    def handle(self, **options):
        repository = Path(settings.BASE_DIR).parent
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / 'ten-insurer'
        source = root / 'sections.json'
        slots_file = root / 'evaluation-slots.json'
        if not source.exists() or not slots_file.exists():
            raise CommandError('Complete maps/sections and the reviewed thirteen-slot roster first.')
        plans = json.loads(source.read_text())['plans']
        slots = json.loads(slots_file.read_text())
        required = {s['plan_id'] for s in slots if s.get('plan_id')}
        if {p['policy_version_id'] for p in plans} != required:
            raise CommandError('Evaluation roster differs from frozen source bundles.')
        for p in plans:
            if any(d['status'] == 'pending' for d in p['document_status']):
                raise CommandError('Document processing is pending; do not score yet.')
            # Index identity is checked by the source bundle, never by latest-plan selection.
            from apps.adviser_v2.demo.evidence import digest
            key = digest({k: v for k, v in p.items() if k not in {'chunks', 'references'}})
            index = DemoPlanIndex.objects.filter(pk=key, revoked_at__isnull=True).first()
            if index is None or DemoSectionVector.objects.filter(index=index).count() != len(p['sections']):
                raise CommandError('Both-arm indexes must be complete before any scored call: ' + p['plan'])
            p['index_id'] = key
        queries = json.loads((repository / 'research/pilots/star/retrieval-queries.json').read_text())['queries']
        jobs = make_jobs(plans, queries, slots)
        run_root = root / 'bakeoff-v2'
        fingerprint = freeze_run(run_root, plans, queries, slots, repository)
        self.stdout.write('Frozen inputs ' + fingerprint)
        if options['freeze_only']:
            return
        by_plan = {p['policy_version_id']: p for p in plans}
        rows = []
        with ThreadPoolExecutor(max_workers=max(1, min(options['workers'], 8))) as pool:
            pending = {pool.submit(run_job, job, by_plan.get(job['plan_id']), run_root): job['id'] for job in jobs}
            for future in as_completed(pending):
                rows.append(future.result())
                atomic_json(run_root / 'progress.json', {'completed': len(rows), 'total': len(jobs), 'frozen': fingerprint})
                self.stdout.write(f"{len(rows)}/{len(jobs)} {pending[future]}")
                self.stdout.flush()
        outcome = score_rows(rows, queries, plans)
        outcome['frozen_sha256'] = fingerprint
        write_report(run_root, repository, rows, outcome, slots)
        self.stdout.write(json.dumps(outcome))
