import ipaddress
import socket
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from apps.adviser.models import DocumentVersion, SourceLocator, SourceObservation
from apps.adviser.source_maps import DocumentValidationError, store_pdf_bytes

DEFAULT_ALLOWED_HOSTS = {
    "joinditto.in",
    "cdn.joinditto.in",
    "s3.ap-south-1.amazonaws.com",
}


def validate_public_host(url: str, allowed_hosts: set[str]) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        raise CommandError("Source URL is outside the configured HTTPS host allowlist.")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise CommandError("Source host could not be resolved.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise CommandError("Source host resolved to a non-public address.")


class Command(BaseCommand):
    help = "Download and preserve one PDF without activating its evidence."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("url")
        parser.add_argument("--identity", required=True)
        parser.add_argument("--type", default="policy_wording")
        parser.add_argument("--allow-host", action="append", default=[])

    def handle(self, *args: Any, **options: Any) -> None:
        source_url = str(options["url"])
        allowed = DEFAULT_ALLOWED_HOSTS | set(options["allow_host"])
        validate_public_host(source_url, allowed)
        try:
            with httpx.Client(
                timeout=httpx.Timeout(30.0, connect=5.0),
                follow_redirects=False,
                headers={"User-Agent": "CoverGuide-local-pilot/0.1"},
            ) as client:
                current_url = source_url
                for redirect_count in range(6):
                    validate_public_host(current_url, allowed)
                    with client.stream("GET", current_url) as response:
                        if response.is_redirect:
                            location = response.headers.get("location")
                            if not location:
                                raise CommandError("Redirect response had no destination.")
                            if redirect_count == 5:
                                raise CommandError("Document download exceeded five redirects.")
                            next_url = urljoin(str(response.url), location)
                            validate_public_host(next_url, allowed)
                            current_url = next_url
                            continue
                        response.raise_for_status()
                        chunks: list[bytes] = []
                        size = 0
                        for chunk in response.iter_bytes():
                            size += len(chunk)
                            if size > 25_000_000:
                                raise CommandError("Document exceeded the 25 MB limit.")
                            chunks.append(chunk)
                        content = b"".join(chunks)
                        final_url = str(response.url)
                        status_code = response.status_code
                        break
                else:
                    raise CommandError("Document download exceeded five redirects.")
        except httpx.HTTPError as exc:
            raise CommandError(f"Document download failed: {exc.__class__.__name__}") from exc
        try:
            blob = store_pdf_bytes(content)
        except DocumentValidationError as exc:
            raise CommandError(str(exc)) from exc
        with transaction.atomic():
            locator, _ = SourceLocator.objects.get_or_create(
                url=source_url,
                source_organisation=urlparse(source_url).hostname or "unknown",
                expected_document_type=str(options["type"]),
            )
            SourceObservation.objects.create(
                locator=locator,
                fetched_at=timezone.now(),
                status_code=status_code,
                final_url=final_url,
                content_sha256=blob.sha256,
                available=True,
            )
            document, created = DocumentVersion.objects.get_or_create(
                blob=blob,
                document_type=str(options["type"]),
                identity=str(options["identity"]),
            )
        action = "Created" if created else "Reused"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} document {document.id} from immutable blob {blob.sha256}."
            )
        )
