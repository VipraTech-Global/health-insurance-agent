import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.adviser_v2.demo.evidence import digest
from apps.adviser_v2.demo.services import bundle_for
from apps.adviser_v2.models import DemoPlanIndex, DemoRelease


class Command(BaseCommand):
    help = 'Activate the local variable-count demo using the protocol-v2 winner and immutable index pins.'

    def handle(self, **options):
        if settings.DATABASES['default']['NAME'] != 'coverguide_star_slice':
            raise CommandError('Only the isolated local database may receive a demo release.')
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / 'ten-insurer'
        outcome_file = root / 'bakeoff-v2/result.json'
        if not outcome_file.exists():
            raise CommandError('Finish the frozen two-arm comparison first.')
        outcome = json.loads(outcome_file.read_text())
        if outcome.get('protocol_version') != 2 or outcome.get('winner') not in {'H', 'P'}:
            raise CommandError('No valid protocol-v2 winner.')
        rows = list(DemoPlanIndex.objects.filter(revoked_at__isnull=True).order_by('plan_key', '-created_at').distinct('plan_key'))
        for row in rows:
            bundle_for(row)
            if row.card['status'] != 'documents_unavailable' and not (root / 'cards' / (row.id + '.json')).exists():
                raise CommandError('Offline card generation is pending: ' + row.name)
        fingerprint = digest({'indexes': [(r.id, digest(r.card)) for r in rows], 'outcome': outcome})
        with transaction.atomic():
            existing = DemoRelease.objects.filter(manifest_sha256=fingerprint).first()
            DemoRelease.objects.filter(active=True).update(active=False)
            if existing:
                existing.active = True
                existing.save(update_fields=['active'])
                release = existing
            else:
                release = DemoRelease.objects.create(method=outcome['winner'], manifest_sha256=fingerprint, bakeoff=outcome, active=True)
                release.indexes.set(rows)
        self.stdout.write(f'Local retrieval_demo {release.id}: {len(rows)} plans, method {release.method}.')
