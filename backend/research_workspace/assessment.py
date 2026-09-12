"""Offline, conservative document triage. Never creates policy facts or completed cases.

The first two physical pages help prioritise manual reading. Keyword matches are
explicitly provisional: they cannot resolve scope, product identity or rule coverage.
Run: PYTHONPATH=backend .venv/bin/python -m research_workspace.assessment
"""

import argparse
import json
import re
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from research_workspace.storage import digest, read_json, read_object, write_json

VERSION = "original-document-triage/1"
SIGNALS = {
    "medical_expense_candidate": r"mediclaim|health insurance|medical expenses|hospitalisation|hospitalization|arogya|sanjeevani",
    "other_business_candidate": r"motor insurance|marine cargo|burglary|fire insurance|aviation|machinery breakdown|crop insurance|professional indemnity",
    "fixed_benefit_or_mixed_candidate": r"personal accident|critical illness|hospital cash|hospi.cash|daily cash",
    "travel_or_mixed_candidate": r"travel insurance|overseas travel",
}


def title_signals(text: str) -> list[str]:
    return [label for label, pattern in SIGNALS.items() if re.search(pattern, text, re.I)]


def inspect_pdf(root: Path, sha: str) -> dict[str, Any]:
    """Verify bytes before invoking a local reader; failure remains a first-class row."""
    base: dict[str, Any] = {
        "sha256": sha,
        "reader": VERSION,
        "scope_status": "unresolved",
        "review_status": "not_manually_reviewed",
        "rule_inventory_status": "not_inventoried",
        "signals": [],
        "uin_candidates": [],
        "physical_pages_requested": [1, 2],
    }
    try:
        content = read_object(root, sha)
        if not content.startswith(b"%PDF-"):
            raise ValueError("Object is not a PDF")
        result = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "2", "-layout", "-", "-"],
            input=content,
            capture_output=True,
            timeout=30,
            check=True,
        )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        if isinstance(exc, subprocess.TimeoutExpired):
            category = "reader_timeout"
        elif isinstance(exc, subprocess.CalledProcessError):
            category = "reader_rejected_pdf"
        elif isinstance(exc, OSError):
            category = "filesystem_or_reader_unavailable"
        else:
            category = "original_integrity_or_media_error"
        return {
            **base,
            "reading_status": "failed",
            "error_type": type(exc).__name__,
            "error_category": category,
            "diagnostic": str(exc)[:500],
            "reader_diagnostic": (
                exc.stderr.decode("utf-8", errors="replace")[:500]
                if isinstance(exc, subprocess.CalledProcessError) and isinstance(exc.stderr, bytes)
                else None
            ),
        }
    text = result.stdout.decode("utf-8", errors="replace")
    pages = text.split("\f")
    preview = [" ".join(page.split()) for page in pages[:2] if page.strip()]
    if not preview:
        return {**base, "reading_status": "no_text_requires_visual_or_ocr"}
    return {
        **base,
        "reading_status": "text_preview_only",
        "physical_page_previews": preview,
        "reader_warning": bool(result.stderr),
        "signals": title_signals(" ".join(preview)),
        "uin_candidates": sorted(set(re.findall(r"\b[A-Z]{3,8}\d{4,7}V\d{2,3}\d{4,6}\b", text))),
        "limitations": "Title signals and UIN strings need original review; absence is not exclusion. No tables, figures, footnotes or connected clauses were reviewed.",
    }


def build_triage(root: Path, workers: int = 4) -> dict[str, Any]:
    if not 1 <= workers <= 8:
        raise ValueError("workers must be between 1 and 8")
    attempts = [read_json(path) for path in sorted((root / "registers/attempts").glob("*.json"))]
    provenance: dict[str, list[dict[str, str]]] = {}
    for row in attempts:
        if row["status"] == "acquired" and row["document_type"] == "pdf_unclassified":
            provenance.setdefault(row["sha256"], []).append(
                {key: row[key] for key in ("insurer_id", "url", "acquired_at")}
            )
    # Inventory every preserved original, including legacy imports absent from the
    # acquisition register. Do not silently attribute an orphan to an insurer.
    hashes = set(provenance)
    object_counts: Counter[str] = Counter()
    for path in (root / "objects").glob("*/*"):
        if not path.is_file():
            continue
        object_counts["scanned"] += 1
        content = path.read_bytes()
        if digest(content) != path.name:
            object_counts["integrity_failure"] += 1
            hashes.add(path.name)
        elif content.startswith(b"%PDF-"):
            object_counts["pdf"] += 1
            hashes.add(path.name)
        else:
            object_counts["verified_non_pdf"] += 1
    # Registers are inputs, not trusted filenames. Reject before any report write.
    if any(not isinstance(sha, str) or not re.fullmatch(r"[a-f0-9]{64}", sha) for sha in hashes):
        raise ValueError("Invalid SHA-256 in original inventory; no triage report written")
    output = root / "assessment/document-previews"
    output.mkdir(parents=True, exist_ok=True)

    def inspect(sha: str) -> dict[str, Any]:
        row = inspect_pdf(root, sha)
        row["acquisition_provenance"] = provenance.get(sha, [])
        row["provenance_status"] = (
            "acquisition_recorded" if sha in provenance else "requires_import_reconciliation"
        )
        write_json(output / f"{sha}.json", row)
        return row

    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(inspect, sorted(hashes)))
    summary = {
        "version": VERSION,
        "objects_considered": len(rows),
        "all_preserved_objects": dict(object_counts),
        "reading_status": dict(Counter(row["reading_status"] for row in rows)),
        "provenance_status": dict(Counter(row["provenance_status"] for row in rows)),
        "signals_nonexclusive": dict(Counter(signal for row in rows for signal in row["signals"])),
        "resolved_scope_count": 0,
        "independent_rule_denominator": None,
        "design_ready": False,
        "input_hashes": {
            "attempts": digest(json.dumps(attempts, sort_keys=True).encode()),
            "pdf_object_names": digest("\n".join(sorted(hashes)).encode()),
        },
    }
    write_json(root / "reports/document-triage.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("research"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(build_triage(args.root, args.workers), sort_keys=True))


if __name__ == "__main__":
    main()
