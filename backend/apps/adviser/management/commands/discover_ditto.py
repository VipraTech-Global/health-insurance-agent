from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from defusedxml import ElementTree
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from apps.adviser.models import CatalogueListing, Insurer, SourceLocator, SourceObservation

from .ingest_document import validate_public_host

DITTO_HOST = "joinditto.in"
ROOT_SITEMAP = "https://joinditto.in/sitemap.xml"
NON_INSURER_SECTIONS = {"articles", "compare-plans", "glossary"}


def xml_locations(content: bytes) -> list[str]:
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise CommandError("Ditto returned an invalid sitemap document.") from exc
    return [
        element.text.strip()
        for element in root.iter()
        if element.tag.endswith("loc") and element.text
    ]


def plan_identity(url: str) -> tuple[str, str] | None:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if (
        parsed.scheme != "https"
        or parsed.hostname != DITTO_HOST
        or len(parts) != 3
        or parts[0] != "health-insurance"
        or parts[1] in NON_INSURER_SECTIONS
        or parts[2] == "reviews"
    ):
        return None
    return parts[1], parts[2]


class Command(BaseCommand):
    help = "Discover Ditto health plan inventory without activating any policy."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--minimum", type=int, default=180)

    def handle(self, *args: Any, **options: Any) -> None:
        observed_at = timezone.now()
        timeout = httpx.Timeout(20.0, connect=5.0)
        limits = httpx.Limits(max_connections=2, max_keepalive_connections=2)
        documents: list[tuple[str, bytes, httpx.Response]] = []
        with httpx.Client(
            timeout=timeout,
            limits=limits,
            follow_redirects=False,
            headers={"User-Agent": "CoverGuide-local-pilot/0.1"},
        ) as client:
            root_response = self._fetch(client, ROOT_SITEMAP)
            child_urls = [
                url
                for url in xml_locations(root_response.content)
                if urlparse(url).hostname == DITTO_HOST
                and urlparse(url).path.startswith("/sitemap-")
            ]
            if not child_urls:
                raise CommandError("No Ditto catalogue sitemaps were found.")
            for child_url in child_urls:
                response = self._fetch(client, child_url)
                documents.append((child_url, response.content, response))

        discovered: dict[str, tuple[str, str]] = {}
        for _, content, _ in documents:
            for url in xml_locations(content):
                identity = plan_identity(url)
                if identity:
                    discovered[urlparse(url).path] = identity
        minimum = int(options["minimum"])
        if len(discovered) < minimum:
            raise CommandError(
                f"Implausibly small catalogue ({len(discovered)} listings; expected at least {minimum})."
            )

        with transaction.atomic():
            for source_url, content, response in documents:
                import hashlib

                locator, _ = SourceLocator.objects.get_or_create(
                    url=source_url,
                    source_organisation="Ditto",
                    expected_document_type="catalogue_sitemap",
                )
                SourceObservation.objects.create(
                    locator=locator,
                    fetched_at=observed_at,
                    status_code=response.status_code,
                    final_url=str(response.url),
                    content_sha256=hashlib.sha256(content).hexdigest(),
                    available=True,
                )
            for path, (insurer_slug, plan_slug) in discovered.items():
                insurer, _ = Insurer.objects.get_or_create(
                    name=insurer_slug.replace("-", " ").title(),
                    defaults={"aliases": [insurer_slug], "official_domains": []},
                )
                CatalogueListing.objects.update_or_create(
                    ditto_path=path,
                    defaults={
                        "displayed_name": plan_slug.replace("-", " ").title(),
                        "insurer": insurer,
                        "last_observed_at": observed_at,
                    },
                )
        self.stdout.write(
            self.style.SUCCESS(
                f"Recorded {len(discovered)} discovered listings; 0 activated for recommendation."
            )
        )

    def _fetch(self, client: httpx.Client, url: str) -> httpx.Response:
        try:
            current_url = url
            for redirect_count in range(6):
                validate_public_host(current_url, {DITTO_HOST})
                response = client.get(current_url)
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise CommandError("Sitemap redirect had no destination.")
                    if redirect_count == 5:
                        raise CommandError("Sitemap fetch exceeded five redirects.")
                    next_url = urljoin(str(response.url), location)
                    validate_public_host(next_url, {DITTO_HOST})
                    current_url = next_url
                    continue
                response.raise_for_status()
                break
            else:
                raise CommandError("Sitemap fetch exceeded five redirects.")
        except httpx.HTTPError as exc:
            raise CommandError(f"Could not fetch {url}: {exc.__class__.__name__}") from exc
        if len(response.content) > 10_000_000:
            raise CommandError(f"Sitemap exceeded the 10 MB limit: {url}")
        media_type = response.headers.get("content-type", "")
        if "xml" not in media_type and not response.content.lstrip().startswith(b"<?xml"):
            raise CommandError(f"Unexpected sitemap content from {url}")
        return response
