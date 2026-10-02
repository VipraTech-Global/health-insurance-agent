from django.core.management.base import BaseCommand

from apps.adviser_v2.demo.vectors import serve


class Command(BaseCommand):
    help = "Run the single resident BGE-M3 CPU worker on loopback port 8022."

    def handle(self, **options):
        serve()
