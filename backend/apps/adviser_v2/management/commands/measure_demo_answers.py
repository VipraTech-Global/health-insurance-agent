import json
import math
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User
from apps.adviser_v2.demo.bakeoff import QUESTIONS
from apps.adviser_v2.demo.contracts import PersonInput, Profile
from apps.adviser_v2.demo.evidence import atomic_json
from apps.adviser_v2.demo.relay import Relay
from apps.adviser_v2.demo.services import question_payload, run_question, save_profile, submit
from apps.adviser_v2.models import DemoQuestion, DemoRelease


def percentiles(values):
    ordered = sorted(values)
    return {'n': len(values), 'p50_ms': ordered[math.ceil(.50*len(ordered))-1],
            'p95_ms': ordered[math.ceil(.95*len(ordered))-1]} if ordered else {'n': 0}


class Command(BaseCommand):
    help = 'Measure actual three- and five-plan application chains with synthetic local profiles.'

    def add_arguments(self, parser):
        parser.add_argument('--samples', type=int, default=3)

    def handle(self, **options):
        if settings.DATABASES['default']['NAME'] != 'coverguide_star_slice':
            raise CommandError('Measurements are restricted to the local slice.')
        release = DemoRelease.objects.filter(active=True).first()
        if not release:
            raise CommandError('Publish the winning local release first.')
        indexes = [r for r in release.indexes.filter(revoked_at__isnull=True).order_by('insurer', 'name')
                   if r.card.get('status') != 'documents_unavailable']
        if len(indexes) < 5:
            raise CommandError('Five available plan indexes are required.')
        user, _ = User.objects.get_or_create(email='ten-insurer-measurements@example.invalid', defaults={'is_active': True})
        profile = Profile(people=[PersonInput(id='self', relationship='self', age_days=35*365)],
            city='Pune', zone=None, sum_insured=1000000, plan_type='medical_indemnity')
        session = save_profile(user, profile)
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / 'ten-insurer'
        observations = []
        started = time.time()
        for count in (3, 5):
            for sample in range(max(1, options['samples'])):
                text = QUESTIONS[sample % len(QUESTIONS)][1]
                question = submit(user, session.id, text, [r.plan_key for r in indexes[:count]])
                tick = time.monotonic()
                run_question(question.id)
                elapsed = round((time.monotonic() - tick)*1000)
                question = DemoQuestion.objects.select_related('session__owner').get(pk=question.id)
                value = question_payload(question)
                observations.append({'plans': count, 'sample': sample, 'question_id': str(question.id),
                    'total_ms': elapsed, 'statuses': [p['state'] for p in value['plans']],
                    'per_plan_ms': [r.total_ms for r in question.answers.all()]})
                atomic_json(root / 'timing-observations.json', observations)
                self.stdout.write(f'{count} plans sample {sample+1}: {elapsed} ms')
                self.stdout.flush()
        ended = time.time()
        records = [json.loads(line) for line in (root / 'relay-calls.jsonl').read_text().splitlines()]
        measured = [r for r in records if started <= r.get('started_at', 0) <= ended and r['priority'] == 'live']
        metrics = Relay.configured().state.redis.hgetall(Relay.configured().state.key('metrics'))
        output = {'method': release.method, 'samples': observations,
            'question_times': {str(n): percentiles([r['total_ms'] for r in observations if r['plans']==n]) for n in (3,5)},
            'queue_times': percentiles([r['queue_ms'] for r in measured]),
            'relay_peak_since_start': int(metrics.get('peak', 0)), 'measured_relay_calls': len(measured),
            'successful_calls_per_minute': sum(r['status']=='completed' for r in measured)/(ended-started)*60,
            'note': 'Observed local timings include queue time and competing background work; no unmeasured speedup is claimed.'}
        atomic_json(root / 'timings.json', output)
        self.stdout.write(json.dumps(output['question_times']))
