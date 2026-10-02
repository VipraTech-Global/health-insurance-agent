"""Official-source discovery and SHA-addressed acquisition with visible failures.

A fetched file is a candidate, not an applicable policy edition. Promotion to a
plan index requires explicit identity/edition/role accounting in its manifest.
"""

from __future__ import annotations

import hashlib
import io
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import httpx
import pdfplumber

from .evidence import atomic_json, digest

INSURERS = (
    ("star", "Star Health", "https://www.starhealth.in/downloads/"),
    ("care", "Care Health Insurance", "https://www.careinsurance.com/download-forms.html"),
    ("niva", "Niva Bupa", "https://www.nivabupa.com/downloads.html"),
    ("hdfc", "HDFC ERGO", "https://www.hdfcergo.com/download/policy-wordings/health"),
    ("icici", "ICICI Lombard", "https://www.icicilombard.com/downloads?download=true"),
    ("aditya", "Aditya Birla Health Insurance", "https://www.adityabirlacapital.com/healthinsurance/downloads"),
    ("bajaj", "Bajaj General Insurance", "https://www.bajajgeneralinsurance.com/health-insurance-plans/health-insurance-documents.html"),
    ("newindia", "New India Assurance", "https://www.newindia.co.in/health/all-products"),
    ("tata", "Tata AIG", "https://www.tataaig.com/downloads"),
    ("manipal", "ManipalCigna", "https://www.manipalcigna.com/downloads/products"),
)
EXCLUDED = re.compile(r"(?:proposal|claim[-_ ]form|kyc|personal[-_ ]accident|\bgroup\b|travel|motor|car[-_ ]insurance)", re.I)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None
        self.context = []
        self.heading = None
        self.heading_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"h1", "h2", "h3", "h4", "h5"}:
            self.heading, self.heading_text = tag, []
        if tag == "a" and attrs.get("href"):
            self.current = {"href": attrs["href"], "text": attrs.get("title", ""), "context": self.context[-2:]}

    def handle_data(self, text):
        if self.current is not None:
            self.current["text"] += " " + text.strip()
        if self.heading:
            self.heading_text.append(text)

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.current["text"] = " ".join(self.current["text"].split())
            self.links.append(self.current)
            self.current = None
        if tag == self.heading:
            self.context.append(" ".join("".join(self.heading_text).split()))
            self.heading = None


def document_role(label: str) -> str:
    text = unquote(label).casefold()
    if EXCLUDED.search(text):
        return "excluded"
    if re.search(r"premium|rate[-_ ]?(?:chart|table)|pricing", text):
        return "premium_chart"
    if re.search(r"customer[-_ ]?information|\bcis\b", text):
        return "customer_information_sheet"
    if "prospectus" in text:
        return "prospectus"
    if "brochure" in text:
        return "brochure"
    if re.search(r"wording|policy[-_ ]?(?:clause|document)|terms|\bt&c\b|\btnc\b", text):
        return "base_wording"
    return "unresolved"


def discover_one(insurer: tuple[str, str, str], root: Path) -> dict:
    key, name, url = insurer
    row = {"insurer_id": key, "insurer": name, "source_url": url,
           "retrieved_at": datetime.now(UTC).isoformat(), "documents": [],
           "catalogue_complete": False, "status": "pending"}
    try:
        response = httpx.get(url, follow_redirects=True, timeout=35,
                             headers={"User-Agent": "CoverGuide local source audit/1"})
        row["http_status"] = response.status_code
        response.raise_for_status()
        parser = Links()
        parser.feed(response.text)
        html_sha = hashlib.sha256(response.content).hexdigest()
        root.mkdir(parents=True, exist_ok=True)
        (root / (html_sha + ".html")).write_bytes(response.content)
        row["source_sha256"] = html_sha
        urls = set()
        for link in parser.links:
            target = urljoin(str(response.url), link["href"])
            pdf_candidate = ".pdf" in unquote(urlparse(target).path).casefold()
            pdf_candidate |= (key.startswith("manipal") and "/documents/" in urlparse(target).path)
            if not pdf_candidate or target in urls:
                continue
            urls.add(target)
            label = link["text"] or unquote(urlparse(target).path.rsplit("/", 1)[-1])
            role = document_role(label + " " + unquote(urlparse(target).path))
            row["documents"].append({"url": target, "label": label, "role": role,
                "source_context": link["context"], "source_url": url,
                "status": "excluded" if role == "excluded" else "discovered",
                "applicability": "unresolved", "uin": None, "edition": None})
        row["product_links"] = [{"url": urljoin(url, link["href"]), "label": link["text"]}
            for link in parser.links if "health" in link["href"].casefold()
            and not link["href"].casefold().endswith(".pdf")]
        row["status"] = "links_discovered" if row["documents"] else "dynamic_or_no_pdf_links"
    except httpx.HTTPError as exc:
        row["status"] = "unavailable"
        row["reason"] = f"{type(exc).__name__}: official source could not be retrieved"
    atomic_json(root / (key + "-discovery.json"), row)
    return row


def discover_all(root: Path) -> list[dict]:
    with ThreadPoolExecutor(max_workers=10) as pool:
        jobs = [pool.submit(discover_one, insurer, root) for insurer in INSURERS]
        return [job.result() for job in as_completed(jobs)]


def acquire(document: dict, root: Path) -> dict:
    row = {**document, "retrieved_at": datetime.now(UTC).isoformat()}
    if document["role"] == "excluded":
        return {**row, "status": "excluded"}
    if shutil.disk_usage(root).free < 3 * 1024**3:
        return {**row, "status": "paused_disk", "reason": "Below 3 GB free; source retained in roster."}
    try:
        response = httpx.get(document["url"], follow_redirects=True, timeout=45)
        response.raise_for_status()
        if not response.content.startswith(b"%PDF-"):
            return {**row, "status": "unavailable", "reason": "Official URL returned non-PDF data.",
                    "http_status": response.status_code}
        payload = response.content
        with pdfplumber.open(io.BytesIO(payload)) as pdf:
            count = len(pdf.pages)
            if count < 1:
                raise ValueError("Empty PDF")
            # Force each physical page to parse, not merely the file header.
            for page in pdf.pages:
                if page.width <= 0 or page.height <= 0:
                    raise ValueError("Invalid PDF page")
        sha = hashlib.sha256(payload).hexdigest()
        path = root / "objects" / (sha + ".pdf")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise ValueError("Content-addressed object failed its integrity check.")
        if not path.exists():
            path.write_bytes(payload)
        return {**row, "status": "acquired_unreviewed", "sha256": sha,
                "path": str(path), "physical_pages": count, "bytes": len(payload)}
    except (httpx.HTTPError, ValueError, OSError) as exc:
        return {**row, "status": "unavailable", "reason": type(exc).__name__}


def manifest_hash(rows: list[dict]) -> str:
    return digest(rows)
