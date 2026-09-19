"""Verify cited PDF pages in the ten-case live audit against preserved source bytes."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import django  # noqa: E402

django.setup()

from apps.adviser_v2.models import EvidenceSpan  # noqa: E402
from apps.adviser_v2.storage import read_public  # noqa: E402


def tokens(value: str) -> list[str]:
    return re.findall(r"\w+", value.casefold())


def quote_on_page(quote: str, page_text: str) -> bool:
    quoted = tokens(quote)
    page = " ".join(tokens(page_text))
    return any(
        " ".join(quoted[index : index + 8]) in page
        for index in range(max(1, len(quoted) - 7))
    )


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "data/reports/ten-live-cases"
    page_cache: dict[tuple[str, int], str] = {}
    results: list[dict[str, object]] = []
    for case in range(1, 11):
        audit = json.loads((root / f"case-acceptance-{case}.json").read_text())
        if audit["turn_state"] != "completed":
            raise ValueError(f"Case {case} is not completed")
        citations = [
            citation
            for statement in audit["recommendation"]["statements"]
            for citation in statement["citations"]
        ]
        for citation in citations:
            span = EvidenceSpan.objects.select_related("page__original_file").get(
                pk=citation["evidence_span_id"]
            )
            page = span.page
            if page is None or page.original_file.owner_id is not None:
                raise ValueError(f"Case {case} cites an unavailable public PDF page")
            if (
                citation["page"] != page.page_number
                or span.locator.get("physical_page") != page.page_number
                or span.verification != "reviewed"
                or page.review_state != "fully_reviewed"
                or citation["document_version_id"]
                != citation["source"]["document_version_id"]
            ):
                raise ValueError(f"Case {case} has an invalid citation locator or review state")
            key = (page.original_file.sha256, page.page_number)
            if key not in page_cache:
                preserved = read_public(
                    page.original_file.storage_key, page.original_file.sha256
                )
                extracted = subprocess.run(
                    [
                        "pdftotext", "-f", str(page.page_number),
                        "-l", str(page.page_number), "-layout", "-", "-",
                    ],
                    input=preserved, capture_output=True, check=True,
                )
                page_cache[key] = extracted.stdout.decode("utf-8", errors="replace")
            if not quote_on_page(span.quote, page_cache[key]):
                raise ValueError(f"Case {case} quote is absent from PDF page {page.page_number}")
            results.append({
                "case": case,
                "evidence_span_id": str(span.id),
                "physical_page": page.page_number,
                "source_url": citation["source"]["url"],
                "status": "verified",
            })
    destination = root / "citation-page-check.json"
    destination.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Verified {len(results)} citations across {len(page_cache)} preserved PDF pages")
    print(destination)


if __name__ == "__main__":
    main()
