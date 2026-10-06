"""Premium charts an insurer publishes apart from a plan's documents.

A chart is pinned by its PDF hash with its own identity record (where and when
it was fetched, and every plan UIN it prints). It joins a plan's evidence only
when it prints that plan's exact UIN and a reviewed adapter exists for its
layout, and only for pricing and price citations: plan facts never read it.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from pathlib import Path

from .evidence import atomic_json, build_sections
from .extraction import extract

VERSION = "premium-source/1"
UIN = re.compile(r"\b[A-Z]{3}HLIP\d{5}V\d{6}\b")


def register(pdf: Path, *, url: str, retrieved_at: str, insurer_id: str, label: str, root: Path):
    """Pin one downloaded chart under the report root and record its identity."""
    payload = pdf.read_bytes()
    sha = hashlib.sha256(payload).hexdigest()
    stored = root / "objects" / (sha + ".pdf")
    if stored.exists():
        if stored.read_bytes() != payload:
            raise ValueError("Stored object differs from its content hash.")
    else:
        stored.parent.mkdir(parents=True, exist_ok=True)
        stored.write_bytes(payload)
    document = {
        "acquisition": "official_download",
        "bytes": len(payload),
        "document_key": f"{insurer_id}:premium_chart:{sha[:12]}",
        "document_version_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{sha}:premium-source")),
        "insurer_id": insurer_id,
        "label": label,
        "path": str(stored),
        "retrieved_at": retrieved_at,
        "role": "premium_chart",
        "sha256": sha,
        "url": url,
    }
    pages = extract(document, root)
    document["physical_pages"] = len(pages)
    document["observed_uins"] = sorted({u for p in pages for u in UIN.findall(p["passage"])})
    manifest = {"version": VERSION, "document": document, "pages": pages}
    atomic_json(root / "premium-sources" / (sha + ".json"), manifest)
    return manifest


def linked(uin: str, root: Path) -> list[dict]:
    """Reviewed charts that print this exact plan UIN."""
    from .reviewed_charts import ADAPTERS

    found = []
    for path in sorted((root / "premium-sources").glob("*.json")):
        manifest = json.loads(path.read_text())
        document = manifest["document"]
        if manifest["version"] != VERSION or path.stem != document["sha256"]:
            raise ValueError("Premium source record differs from its pinned hash.")
        if uin and uin in document["observed_uins"] and document["sha256"] in ADAPTERS:
            found.append(manifest)
    return found


def with_premium_sources(bundle: dict, uin: str, root: Path | None = None) -> dict:
    """The plan bundle plus its linked charts, sectioned under the plan's own ID."""
    if root is None:
        from django.conf import settings

        root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
    sources = linked(uin, root)
    known = {d["sha256"] for d in bundle["documents"]}
    sources = [m for m in sources if m["document"]["sha256"] not in known]
    if not sources:
        return bundle
    plan_ids = {s["plan_id"] for s in bundle["sections"]}
    if len(plan_ids) != 1:
        raise ValueError("The plan bundle's sections must belong to one plan.")
    merged = {
        **bundle,
        "documents": list(bundle["documents"]),
        "pages": list(bundle["pages"]),
        "sections": list(bundle["sections"]),
    }
    for manifest in sources:
        sections, _, _ = build_sections(
            plan_id=next(iter(plan_ids)),
            document=manifest["document"],
            pages=manifest["pages"],
            saved_map=None,
        )
        merged["documents"].append(manifest["document"])
        merged["pages"].extend(manifest["pages"])
        merged["sections"].extend(s.payload() for s in sections)
    return merged


def priced_bundle(index) -> dict:
    """A plan index's pinned bundle with its linked premium charts."""
    from .services import bundle_for

    return with_premium_sources(bundle_for(index), index.uin)
