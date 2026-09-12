"""Bounded acquisition of explicitly supplied research URLs; no recursive crawler."""

import io
import re
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urljoin, urlsplit

import httpx
import pdfplumber

from research_workspace.storage import digest, put_object, read_json, write_json

MAX_BYTES = 50 * 1024 * 1024
VERSION = "research-acquisition/2"
OUTSIDE_SELECTED_INSURERS = {
    "Iffco Tokio",
    "Navi",
    "Reliance",
    "Royal Sundaram",
    "Universal Sompo",
    "Zuno",
}


def allowed_url(url: str, hosts: list[str]) -> bool:
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return False
    host = (parts.hostname or "").lower()
    return (
        parts.scheme == "https"
        and parts.username is None
        and parts.password is None
        and port in (None, 443)
        and any(host == domain or host.endswith("." + domain) for domain in hosts)
    )


class Links(HTMLParser):
    """Retain the original anchor and nearby text as discovery evidence, not identity."""

    def __init__(self, base: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base = base
        self.links: list[dict[str, str]] = []
        self.recent = ""
        self.anchor: dict[str, str] | None = None
        self.base_seen = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        href = attributes.get("href")
        if tag == "base" and href and not self.base_seen:
            self.base = urljoin(self.base, href)
            self.base_seen = True
        if tag == "a" and href:
            self.anchor = {
                "url": urldefrag(urljoin(self.base, href))[0],
                "raw_href": href,
                "label": "",
                "preceding_text": self.recent[-700:],
            }

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text:
            self.recent = (self.recent + " " + text)[-700:]
            if self.anchor is not None:
                self.anchor["label"] += text + " "

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.anchor is not None:
            self.anchor["label"] = self.anchor["label"].strip()
            self.links.append(self.anchor)
            self.anchor = None


def document_links(html: str, base: str) -> list[dict[str, str]]:
    parser = Links(base)
    parser.feed(html)
    # Extensionless document servers are retained too. Never infer policy identity here.
    return [
        link
        for link in parser.links
        if re.search(r"\.pdf(?:[?#/]|$)|/documents/|/document/", link["url"], re.I)
    ]


def acquire(
    root: Path,
    url: str,
    hosts: list[str],
    client: httpx.Client,
    *,
    insurer_id: str,
    linking_url: str = "",
    expected_pdf: bool = False,
) -> dict[str, Any]:
    """Each call creates an attempt; original bytes and failed HTTP bodies remain available."""
    started = datetime.now(UTC)
    record: dict[str, Any] = {
        "format_version": 1,
        "component_version": VERSION,
        "insurer_id": insurer_id,
        "url": url,
        "linking_url": linking_url,
        "acquired_at": started.isoformat(),
        "status": "running",
        "issues": [],
        "sha256": None,
        "page_count": None,
        "document_type": "unclassified",
        "language": "unknown",
        "associations": [],
        "effective_from": None,
        "effective_to": None,
        "review_status": "not_reviewed",
    }
    identity = digest(f"{insurer_id}:{url}:{started.isoformat()}".encode())
    attempt_path = root / "registers" / "attempts" / f"{identity}.json"
    write_json(attempt_path, record)
    record["status"] = "failed"
    current = url
    try:
        for _ in range(6):
            if not allowed_url(current, hosts):
                record["issues"].append("host_not_approved")
                break
            with client.stream("GET", current, follow_redirects=False) as response:
                record["http_status"] = response.status_code
                record["final_url"] = str(response.url)
                if response.is_redirect:
                    current = urljoin(current, response.headers["location"])
                    continue
                chunks = bytearray()
                for chunk in response.iter_bytes():
                    chunks.extend(chunk)
                    if len(chunks) > MAX_BYTES:
                        record["issues"].append("size_limit_exceeded")
                        break
                else:
                    content = bytes(chunks)
                    record["sha256"] = put_object(root, content)
                    record["byte_count"] = len(content)
                    record["content_type"] = response.headers.get("content-type", "")
                    if not response.is_success:
                        record["issues"].append(f"http_{response.status_code}")
                    elif content.startswith(b"%PDF-"):
                        record["status"] = "acquired"
                        record["document_type"] = "pdf_unclassified"
                        try:
                            if b"%%EOF" not in content[-8192:]:
                                raise ValueError("PDF end marker missing")
                            with pdfplumber.open(io.BytesIO(content)) as pdf:
                                record["page_count"] = len(pdf.pages)
                                if not pdf.pages:
                                    raise ValueError("PDF has no pages")
                                record["pages"] = [
                                    {
                                        "page": n + 1,
                                        "status": "preserved_not_read",
                                        "width": float(page.width),
                                        "height": float(page.height),
                                        "tables": "not_inventoried",
                                        "figures": "not_inventoried",
                                    }
                                    for n, page in enumerate(pdf.pages)
                                ]
                        except Exception as exc:
                            # Readers may throw several library-specific exceptions; retain failure.
                            record["issues"].append(f"pdf_unreadable:{type(exc).__name__}")
                            record["status"] = "unreadable"
                    elif expected_pdf:
                        record["issues"].append("expected_pdf_received_other_content")
                    elif "html" in response.headers.get("content-type", ""):
                        record["status"] = "acquired"
                        record["document_type"] = "source_page"
                        record["links"] = document_links(
                            content.decode(response.encoding or "utf-8", errors="replace"),
                            str(response.url),
                        )
                    else:
                        record["issues"].append("unsupported_media_type")
                break
        else:
            record["issues"].append("redirect_limit_exceeded")
    except httpx.HTTPError as exc:
        record["issues"].append(type(exc).__name__)
    record["latency_ms"] = round((datetime.now(UTC) - started).total_seconds() * 1000)
    write_json(attempt_path, record)
    return record


def reconcile_legacy(legacy: Path, insurers: Path) -> list[dict[str, Any]]:
    source = read_json(legacy)
    aliases = {
        alias: insurer["id"] for insurer in read_json(insurers) for alias in insurer["aliases"]
    }
    seen: set[str] = set()
    rows = []
    for listing in source["listings"]:
        identity = listing["ditto_path"]
        if identity in seen:
            raise ValueError(f"Duplicate legacy identity: {identity}")
        seen.add(identity)
        insurer = aliases.get(listing["insurer__name"])
        status = "unresolved_product_identity"
        issue = "Requires insurer-original identity and scope evidence"
        if insurer is None:
            status = "unresolved_insurer_identity"
            issue = "Historical insurer succession or identity requires original evidence"
            if listing["insurer__name"] in OUTSIDE_SELECTED_INSURERS:
                status = "outside_selected_insurers"
                issue = "Legacy insurer label falls outside the selected 20-insurer scope"
        rows.append(
            {
                "format_version": 1,
                "legacy_identity": identity,
                "legacy_source_sha256": digest(legacy.read_bytes()),
                "legacy_name": listing["displayed_name"],
                "legacy_insurer": listing["insurer__name"],
                "insurer_id": insurer,
                "status": status,
                "product_version_id": None,
                "variant_id": None,
                "issues": [issue],
                "evidence": [],
            }
        )
    return rows
