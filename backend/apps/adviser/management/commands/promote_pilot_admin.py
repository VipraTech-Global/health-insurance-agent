"""One-time promotion bound to an explicitly inspected user and login timestamp."""

import uuid
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils.dateparse import parse_datetime

from apps.accounts.models import User
from apps.adviser.models import ReviewEvent


class Command(BaseCommand):
    help = "Promote the uniquely most recently logged-in account to pilot staff."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--expected-user", required=True, type=uuid.UUID)
        parser.add_argument("--expected-login", required=True)

    def handle(self, *args: Any, **options: Any) -> None:
        expected_time = parse_datetime(options["expected_login"])
        if expected_time is None:
            raise CommandError("A valid expected login timestamp is required.")
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(71493801)")
            prior = ReviewEvent.objects.filter(object_type="pilot_admin_promotion").first()
            if prior:
                raise CommandError("Pilot administrator promotion has already been performed.")
            users = list(
                User.objects.select_for_update()
                .filter(is_active=True, deleted_at__isnull=True, last_login__isnull=False)
                .order_by("-last_login", "id")[:2]
            )
            if not users or (len(users) > 1 and users[0].last_login == users[1].last_login):
                raise CommandError("There is no uniquely most recently logged-in account.")
            user = users[0]
            if user.id != options["expected_user"] or user.last_login != expected_time:
                raise CommandError(
                    "The most recent login changed. Recheck the intended pilot account."
                )
            if User.objects.filter(is_staff=True).exclude(id=user.id).exists():
                raise CommandError(
                    "Another administrator already exists; review the pilot assignment."
                )
            user.is_staff = True
            user.save(update_fields=["is_staff"])
            ReviewEvent.objects.create(
                object_type="pilot_admin_promotion",
                object_id=user.id,
                expected_revision=expected_time.isoformat(),
                decision="promote",
                reason="Authorized one-time local pilot activation",
                reviewer=user,
            )
        self.stdout.write("Pilot administrator promoted; superuser permissions were not added.")
