"""Preflight for the OmniRoute gateway: settings, reachability and allowlisted model ids.

Sends no customer or health data; it only reads the model catalogue.
"""

from __future__ import annotations

from typing import Any

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.adviser.providers import omniroute_models, omniroute_problems, provider_config


class Command(BaseCommand):
    help = "Check OmniRoute settings and that every allowlisted model is in its live catalogue."

    def handle(self, *args: Any, **options: Any) -> None:
        problems = omniroute_problems()
        if problems:
            raise CommandError("; ".join(problems))
        if not settings.OMNIROUTE_ENABLED:
            raise CommandError("OMNIROUTE_ENABLED is not set to 1.")
        config = provider_config("omniroute")
        try:
            with httpx.Client(trust_env=False, timeout=15, follow_redirects=False) as client:
                response = client.get(
                    f"{config.base_url}/v1/models",
                    headers={"Authorization": f"Bearer {config.api_key}"},
                )
            response.raise_for_status()
            catalogue = {str(item["id"]) for item in response.json()["data"]}
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise CommandError(f"OmniRoute catalogue unavailable ({type(exc).__name__}).") from exc
        missing = sorted(set(omniroute_models()) - catalogue)
        if missing:
            raise CommandError("Not in the live catalogue: " + ", ".join(missing))
        self.stdout.write(
            self.style.SUCCESS(
                f"OmniRoute reachable; {len(omniroute_models())} allowlisted models present."
            )
        )
