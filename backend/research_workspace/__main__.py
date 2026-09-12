"""Research CLI. It has no Django settings, database writes, queue, or publication path."""

import argparse
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import httpx

from research_workspace.acquisition import VERSION, acquire, document_links, reconcile_legacy
from research_workspace.cases import build_drafts
from research_workspace.storage import digest, read_json, read_object, write_csv, write_json


def build_register(root: Path) -> dict[str, Any]:
    insurers = read_json(root / "seeds/insurers.json")
    attempts = [read_json(p) for p in sorted((root / "registers/attempts").glob("*.json"))]
    attempts.sort(key=lambda row: row["acquired_at"])
    latest = {(row["insurer_id"], row["url"]): row for row in attempts}
    discovered: dict[tuple[str, str], dict[str, Any]] = {}
    seen_pages: set[tuple[str, str, str]] = set()
    for page in attempts:
        if page["document_type"] != "source_page" or page["status"] != "acquired":
            continue
        page_key = (page["insurer_id"], page["url"], page["sha256"])
        if page_key in seen_pages:
            continue
        seen_pages.add(page_key)
        links = document_links(
            read_object(root, page["sha256"]).decode(errors="replace"),
            page.get("final_url", page["url"]),
        )
        for link in links:
            key = (page["insurer_id"], link["url"])
            row = discovered.setdefault(
                key,
                {
                    "source_id": digest((key[0] + ":" + key[1]).encode()),
                    "insurer_id": key[0],
                    "url": key[1],
                    "observations": [],
                    "product_associations": [],
                    "scope_status": "unresolved",
                    "document_type": "unclassified",
                    "processing_result": "not_acquired",
                    "issues": ["Document identity, scope and version require original review"],
                },
            )
            observation = {
                "reader_version": VERSION,
                "linking_url": page["url"],
                "page_sha256": page["sha256"],
                **link,
            }
            if observation not in row["observations"]:
                row["observations"].append(observation)
    for key, row in discovered.items():
        attempt = latest.get(key)
        if attempt:
            row["processing_result"] = attempt["status"]
            row["latest_attempt"] = attempt
    rows = list(discovered.values())
    write_json(root / "registers/sources.json", rows)
    write_csv(
        root / "registers/source-index.csv",
        [
            {
                "source_id": row["source_id"],
                "insurer_id": row["insurer_id"],
                "url": row["url"],
                "processing_result": row["processing_result"],
                "scope_status": row["scope_status"],
                "sha256": row.get("latest_attempt", {}).get("sha256"),
                "page_count": row.get("latest_attempt", {}).get("page_count"),
                "linking_url": row["observations"][0]["linking_url"],
                "label": row["observations"][0]["label"],
            }
            for row in rows
        ],
        [
            "source_id",
            "insurer_id",
            "url",
            "processing_result",
            "scope_status",
            "sha256",
            "page_count",
            "linking_url",
            "label",
        ],
    )
    counts = []
    sample_path = root / "registers/rule-inventory-sample.json"
    sample_rules = read_json(sample_path)["rules"] if sample_path.exists() else []
    for insurer in insurers:
        sources = [r for r in rows if r["insurer_id"] == insurer["id"]]
        observations = [r for r in attempts if r["insurer_id"] == insurer["id"]]
        pdfs = {
            r["sha256"]: r
            for r in observations
            if r["document_type"] == "pdf_unclassified" and r["status"] == "acquired"
        }
        counts.append(
            {
                "insurer_id": insurer["id"],
                "name": insurer["name"],
                "expected_bundle_inventory": "incomplete",
                "discovered_document_urls": len(sources),
                "unique_acquired_pdfs": len(pdfs),
                "preserved_pdf_pages": sum(r["page_count"] or 0 for r in pdfs.values()),
                "acquisition_results": dict(Counter(r["processing_result"] for r in sources)),
                "products_and_versions": None,
                "variants_and_addons": None,
                "independent_rule_denominator": None,
                "original_rule_instances_in_sample": sum(
                    rule["insurer_id"] == insurer["id"] for rule in sample_rules
                ),
                "rule_coverage_percent": None,
                "reviewed_rules": 0,
                "recommendable_configurations": 0,
            }
        )
    report = {
        "format_version": 1,
        "release_ready": False,
        "insurers": counts,
        "insurer_count": len(insurers),
        "document_url_count": len({row["url"] for row in rows}),
        "insurer_document_associations": len(rows),
        "unique_acquired_pdfs": len(
            {
                r["sha256"]
                for r in attempts
                if r["document_type"] == "pdf_unclassified" and r["status"] == "acquired"
            }
        ),
        "attempt_count": len(attempts),
        "rule_coverage_percent": None,
        "limitations": [
            "Explicit seed-page snapshot only; complete product and bundle inventory is not established",
            "An acquired file is not reviewed knowledge; page/table/figure reading remains pending",
            "Unknown rule denominators prohibit coverage percentages",
            "No replacement database, adviser or cutover is published by this workspace",
        ],
    }
    write_json(root / "reports/source-coverage.json", report)
    write_csv(
        root / "reports/insurer-coverage.csv",
        counts,
        [
            "insurer_id",
            "name",
            "discovered_document_urls",
            "unique_acquired_pdfs",
            "preserved_pdf_pages",
            "products_and_versions",
            "variants_and_addons",
            "independent_rule_denominator",
            "rule_coverage_percent",
            "reviewed_rules",
            "recommendable_configurations",
            "expected_bundle_inventory",
        ],
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("research"))
    sub = parser.add_subparsers(dest="command", required=True)
    reconcile = sub.add_parser("reconcile")
    reconcile.add_argument("--legacy", type=Path, required=True)
    snapshot = sub.add_parser("snapshot")
    snapshot.add_argument("--insurer", action="append", default=[])
    download = sub.add_parser("acquire")
    download.add_argument("--insurer", action="append", default=[])
    download.add_argument(
        "--limit", type=int, default=0, help="0 means every registered document URL"
    )
    download.add_argument("--retry-failed", action="store_true")
    download.add_argument("--match", help="Research selection regex over original link and context")
    sub.add_parser("report")
    sub.add_parser("draft-cases")
    args = parser.parse_args()
    root: Path = args.root
    if args.command == "draft-cases":
        build_drafts(root)
        return
    if args.command == "reconcile":
        rows = reconcile_legacy(args.legacy, root / "seeds/insurers.json")
        write_json(root / "registers/legacy-reconciliation.json", rows)
        print(
            json.dumps({"entries": len(rows), "outcomes": dict(Counter(r["status"] for r in rows))})
        )
        return
    if args.command == "report":
        report = build_register(root)
        print(json.dumps({k: v for k, v in report.items() if k != "insurers"}))
        return
    insurers = {i["id"]: i for i in read_json(root / "seeds/insurers.json")}
    if set(args.insurer) - set(insurers):
        parser.error("Unknown insurer ID")
    work: list[tuple[str, str, str]] = []
    if args.command == "snapshot":
        for key, insurer in insurers.items():
            if not args.insurer or key in args.insurer:
                work.extend((key, url, "") for url in insurer["pages"])
    else:
        build_register(root)
        for row in read_json(root / "registers/sources.json"):
            if args.insurer and row["insurer_id"] not in args.insurer:
                continue
            if args.match and not re.search(args.match, json.dumps(row["observations"]), re.I):
                continue
            status = row["processing_result"]
            if status in ("acquired", "running") or (
                status != "not_acquired" and not args.retry_failed
            ):
                continue
            work.append((row["insurer_id"], row["url"], row["observations"][0]["linking_url"]))
        if args.limit > 0:
            work = work[: args.limit]

    def run(item: tuple[str, str, str]) -> None:
        insurer_id, url, linking = item
        with httpx.Client(
            timeout=httpx.Timeout(30, connect=10),
            headers={
                "User-Agent": "CoverGuide-Research/1.0 (official document inventory)",
                "Accept": "text/html,application/pdf,*/*",
            },
        ) as client:
            result = acquire(
                root,
                url,
                insurers[insurer_id]["hosts"],
                client,
                insurer_id=insurer_id,
                linking_url=linking,
                expected_pdf=args.command == "acquire",
            )
        print(
            json.dumps(
                {
                    "insurer": insurer_id,
                    "status": result["status"],
                    "issues": result["issues"],
                    "url": url,
                }
            ),
            flush=True,
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(run, work))
    build_register(root)


if __name__ == "__main__":
    main()
