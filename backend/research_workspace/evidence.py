"""Original-file resolution for research evidence; lexical presence is not entailment review."""

import io
from pathlib import Path

import pdfplumber

from research_workspace.contracts import EvidenceLocation
from research_workspace.storage import read_object


def verify_locations(root: Path, locations: list[EvidenceLocation]) -> None:
    grouped: dict[str, list[EvidenceLocation]] = {}
    for location in locations:
        grouped.setdefault(location.source_sha256, []).append(location)
    for sha, evidence in grouped.items():
        content = read_object(root, sha)
        if not content.startswith(b"%PDF-"):
            raise ValueError("Evidence must resolve to an original PDF")
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            text_cache: dict[int, str] = {}
            for item in evidence:
                if item.page > len(pdf.pages):
                    raise ValueError("Evidence points beyond the original document")
                page = pdf.pages[item.page - 1]
                if item.bbox is not None:
                    x0, top, x1, bottom = item.bbox
                    if not (0 <= x0 < x1 <= page.width and 0 <= top < bottom <= page.height):
                        raise ValueError("Evidence region lies outside the original page")
                    region_text = " ".join((page.crop(item.bbox).extract_text() or "").split())
                    if " ".join(item.passage.split()) not in region_text:
                        raise ValueError("Evidence passage is outside its stated region")
                if item.page not in text_cache:
                    text_cache[item.page] = " ".join((page.extract_text() or "").split())
                if " ".join(item.passage.split()) not in text_cache[item.page]:
                    raise ValueError("Evidence passage cannot be resolved in the original page")
