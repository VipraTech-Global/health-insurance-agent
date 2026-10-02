import time
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from apps.adviser_v2.demo.relay import Relay
from apps.adviser_v2.demo.tasks import demo_question
from apps.adviser_v2.models import DemoQuestion


class Command(BaseCommand):
    help = 'Recover queued or abandoned local demo questions without repeating completed plan results.'

    def add_arguments(self, parser):
        parser.add_argument('--loop', action='store_true')

    def handle(self, **options):
        if settings.DATABASES['default']['NAME'] != 'coverguide_star_slice':
            raise CommandError('Recovery is restricted to the isolated slice database.')
        while True:
            Relay.configured().probe_due(deadline=time.monotonic() + 60)
            stale = timezone.now() - timedelta(minutes=5)
            pending = Q(state='queued') | (Q(state='running') & (Q(heartbeat_at__lt=stale) | Q(heartbeat_at__isnull=True)))
            for key in DemoQuestion.objects.filter(pending, cancelled_at__isnull=True).values_list('pk', flat=True):
                demo_question.apply_async(args=[str(key)], queue='demo_live')
            if not options['loop']:
                return
            time.sleep(30)
