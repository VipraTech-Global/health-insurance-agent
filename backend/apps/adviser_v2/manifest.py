"""Closed fixed-manifest contract and bounded direct official-source acquisition."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
from typing import Literal
from urllib.parse import urljoin, urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

MAX_SOURCE_BYTES = 50 * 1024 * 1024
MAX_PDF_TRAILING_BYTES = 64 * 1024

type DocumentRole = Literal[
    "base_wording",
    "customer_information_sheet",
    "prospectus",
    "premium_table",
    "proposal_form",
    "endorsement",
    "addon_wording",
    "addon_cis",
    "revision_notice",
    "product_page",
    "provider_network",
]

ALL_DOCUMENT_ROLES = {
    "base_wording",
    "customer_information_sheet",
    "prospectus",
    "premium_table",
    "proposal_form",
    "endorsement",
    "addon_wording",
    "addon_cis",
    "revision_notice",
    "product_page",
    "provider_network",
}

POLICY_MEMBERSHIP_ROLE_BY_DOCUMENT_ROLE = {
    "base_wording": "base_wording",
    "customer_information_sheet": "customer_information_sheet",
    "prospectus": "prospectus",
    "premium_table": "referenced_schedule",
    "proposal_form": "other_dependency",
    "endorsement": "endorsement",
    "addon_wording": "endorsement",
    "addon_cis": "other_dependency",
    "revision_notice": "regulatory_modification",
    "product_page": "other_dependency",
    "provider_network": "other_dependency",
}


class ManifestRoleDecision(BaseModel):
    """Human-reviewed declaration that makes omitted document roles explicit."""

    model_config = ConfigDict(extra="forbid")

    role: DocumentRole
    applicability: Literal["applicable", "not_applicable", "conditional"]
    reason: str = Field(min_length=1, max_length=1000)


class ManifestDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_key: str = Field(min_length=1, max_length=160)
    role: DocumentRole
    url: HttpUrl
    authority: Literal["insurer_issued", "regulator_issued"]
    expected_media_type: Literal["application/pdf", "text/html"]
    required: bool
    applicability: Literal["applicable", "not_applicable", "conditional"]
    applicability_reason: str = Field(min_length=1, max_length=1000)
    expected_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class ManifestProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_key: str = Field(min_length=1, max_length=100)
    insurer: str = Field(min_length=1, max_length=250)
    name: str = Field(min_length=1, max_length=250)
    uin: str = Field(min_length=5, max_length=100)
    variant: str = Field(min_length=1, max_length=200)
    role_decisions: list[ManifestRoleDecision]
    documents: list[ManifestDocument]

    @model_validator(mode="after")
    def complete_minimum_bundle(self) -> ManifestProduct:
        decisions = {item.role: item for item in self.role_decisions}
        if len(decisions) != len(self.role_decisions) or set(decisions) != ALL_DOCUMENT_ROLES:
            raise ValueError("Every document role must have exactly one applicability decision.")
        documents_by_role = {
            role: [item for item in self.documents if item.role == role]
            for role in ALL_DOCUMENT_ROLES
        }
        for role, decision in decisions.items():
            documents = documents_by_role[role]
            if decision.applicability == "not_applicable" and documents:
                raise ValueError(f"Role {role} is not applicable but has manifest entries.")
            if decision.applicability != "not_applicable" and not documents:
                raise ValueError(f"Role {role} requires at least one reviewed manifest entry.")
            if any(item.applicability != decision.applicability for item in documents):
                raise ValueError(f"Role {role} document applicability conflicts with its decision.")
        applicable_roles = {
            role
            for role, decision in decisions.items()
            if decision.applicability != "not_applicable"
        }
        minimum = {
            "base_wording",
            "customer_information_sheet",
            "prospectus",
            "product_page",
        }
        missing = minimum - applicable_roles
        if missing:
            raise ValueError("A bundle is missing required roles: " + ", ".join(sorted(missing)))
        keys = [item.document_key for item in self.documents]
        if len(keys) != len(set(keys)):
            raise ValueError("Document keys must be unique within a product bundle.")
        return self


class CuratedManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    manifest_id: str = Field(min_length=1, max_length=160)
    freeze_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    official_hosts: list[str]
    products: list[ManifestProduct]

    @model_validator(mode="after")
    def exactly_five_distinct_products(self) -> CuratedManifest:
        if len(self.products) != 5:
            raise ValueError("The curated release manifest must contain exactly five products.")
        keys = [item.product_key for item in self.products]
        if len(keys) != len(set(keys)):
            raise ValueError("Product keys must be unique.")
        if len({item.uin for item in self.products}) != 5:
            raise ValueError("Every selected product must have a distinct exact UIN.")
        return self


def load_manifest(path: Path) -> CuratedManifest:
    return CuratedManifest.model_validate_json(path.read_text(encoding="utf-8"))


def manifest_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def html_text(payload: bytes) -> str:
    source = payload.decode("utf-8", errors="replace")
    source = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", source)
    return " ".join(unescape(re.sub(r"(?s)<[^>]+>", " ", source)).split())


def is_complete_pdf(payload: bytes) -> bool:
    """Accept a complete PDF while bounding official-server trailing response bytes."""

    if not payload.startswith(b"%PDF-"):
        return False
    eof_position = payload.rfind(b"%%EOF")
    return eof_position >= max(0, len(payload) - MAX_PDF_TRAILING_BYTES)


def validate_public_url(url: str, allowed_hosts: set[str]) -> None:
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Source URL is invalid.") from exc
    host = (parsed.hostname or "").lower()
    if (
        parsed.scheme != "https"
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
        or host not in allowed_hosts
        or parsed.fragment
    ):
        raise ValueError("Source URL is outside the reviewed HTTPS host allowlist.")
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("Source host could not be resolved.") from exc
    if not addresses:
        raise ValueError("Source host did not resolve.")
    for address in addresses:
        if not ipaddress.ip_address(address[4][0]).is_global:
            raise ValueError("Source host resolved to a non-public address.")


def download_manifest_entry(
    entry: ManifestDocument,
    allowed_hosts: set[str],
    client: httpx.Client,
) -> tuple[bytes, dict[str, object]]:
    current = str(entry.url)
    started = datetime.now(UTC)
    for redirect_count in range(6):
        validate_public_url(current, allowed_hosts)
        with client.stream("GET", current, follow_redirects=False) as response:
            if response.is_redirect:
                location = response.headers.get("location")
                if not location or redirect_count == 5:
                    raise ValueError("Source exceeded the five-redirect limit.")
                current = urljoin(str(response.url), location)
                continue
            response.raise_for_status()
            chunks: list[bytes] = []
            size = 0
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > MAX_SOURCE_BYTES:
                    raise ValueError("Source exceeded the 50 MiB limit.")
                chunks.append(chunk)
            payload = b"".join(chunks)
            digest = hashlib.sha256(payload).hexdigest()
            if entry.expected_sha256 and digest != entry.expected_sha256:
                raise ValueError("Downloaded bytes did not match the reviewed expected SHA-256.")
            if entry.expected_media_type == "application/pdf":
                if not is_complete_pdf(payload):
                    raise ValueError(
                        "The manifest expected a complete PDF but received other bytes."
                    )
            elif payload.startswith(b"%PDF-"):
                raise ValueError("The manifest expected HTML but received a PDF.")
            return payload, {
                "captured_at": started.isoformat(),
                "final_url": str(response.url),
                "http_status": response.status_code,
                "sha256": digest,
                "byte_count": len(payload),
                "content_type": response.headers.get("content-type", ""),
            }
    raise ValueError("Source exceeded the five-redirect limit.")
