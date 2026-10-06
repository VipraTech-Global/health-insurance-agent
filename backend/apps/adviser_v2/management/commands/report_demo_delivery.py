"""Summarize admitted app evidence without counting candidate downloads as plans."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.adviser_v2.demo.evidence import atomic_json, digest
from apps.adviser_v2.demo.services import bundle_for
from apps.adviser_v2.models import DemoRelease, EvidenceSpan, KnowledgeReleaseFact, PolicyRule


class Command(BaseCommand):
    help = __doc__

    def handle(self, **options):
        if settings.DATABASES["default"]["NAME"] != "coverguide_star_slice":
            raise CommandError("Report only the isolated local demo database.")
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
        repository = Path(settings.BASE_DIR).parent
        release = DemoRelease.objects.get(active=True)
        frozen = json.loads((root / "bakeoff-v2/frozen.json").read_text())
        if digest({"protocol_version": 2, "inputs": frozen["inputs"]}) != frozen["sha256"]:
            raise CommandError("Frozen evaluation inputs changed.")
        if (repository / "docs/ten-insurer-bakeoff-protocol.md").read_text() != frozen["inputs"][
            "protocol"
        ]:
            raise CommandError("Frozen protocol text changed.")
        for name, expected in frozen["inputs"]["source_hashes"].items():
            source = repository / "research/ten-insurer/protocol-v2-frozen-runtime" / name
            if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
                raise CommandError("Frozen source archive changed: " + name)
        rows, documents, pages, fallback = [], set(), set(), {}
        for index in release.indexes.order_by("insurer", "name", "variant"):
            bundle = bundle_for(index)
            documents.update(d["sha256"] for d in bundle["documents"])
            pages.update((p["document_sha256"], p["physical_page"]) for p in bundle["pages"])
            for document in bundle.get("document_status", []):
                if document["status"] == "fallback":
                    fallback[document["sha256"]] = document["reason"]
            prices = root / "premiums" / (index.id + ".json")
            chart = json.loads(prices.read_text()) if prices.exists() else {}
            rows.append(
                {
                    "plan_id": index.plan_key,
                    "index_version": index.id,
                    "insurer": index.insurer,
                    "name": index.name,
                    "variant": index.variant,
                    "uin": index.uin,
                    "edition": index.edition,
                    "card_status": index.card["status"],
                    "fields_with_citations": sum(
                        bool(f["value"]["citations"]) for f in index.card.get("common_needs", [])
                    ),
                    "models": index.models_used,
                    "coverage": index.coverage,
                    "premium_status": chart.get("status", "processing_pending"),
                    "accepted_prices": len(chart.get("prices", [])),
                }
            )
        acceptance = root / "application-acceptance" / str(release.id) / "summary.json"
        inventory = json.loads((root / "catalogue-inventory.json").read_text())
        acquisition = json.loads((root / "catalogue-acquisition/result.json").read_text())
        fetched = [d for d in acquisition["documents"] if d["status"] == "acquired_unreviewed"]
        output = {
            "schema_version": 1,
            "release_id": str(release.id),
            "method": release.method,
            "frozen_sha256": frozen["sha256"],
            "frozen_sources_verified": True,
            "insurers": len({r["insurer"] for r in rows}),
            "products": len({(r["insurer"], r["name"]) for r in rows}),
            "variants": len(rows),
            "physical_pdfs": len(documents),
            "physical_pages": len(pages),
            "sections_across_variant_indexes": sum(r["coverage"].get("sections", 0) for r in rows),
            "map_fallback_documents": len(fallback),
            "map_fallback_reasons": fallback,
            "card_statuses": dict(Counter(r["card_status"] for r in rows)),
            "premium_statuses": dict(Counter(r["premium_status"] for r in rows)),
            "accepted_prices": sum(r["accepted_prices"] for r in rows),
            "plans": rows,
            "broader_inventory": {
                "complete_current_catalogue": False,
                "register_entries_by_scope": dict(
                    Counter(r["scope"] for r in inventory["entries"])
                ),
                "acquired_unreviewed_responses": len(fetched),
                "distinct_candidate_pdfs": len({d["sha256"] for d in fetched}),
                "candidate_pdfs_already_in_release": len(
                    {d["sha256"] for d in fetched} & documents
                ),
                "unavailable_responses": sum(
                    d["status"] != "acquired_unreviewed" for d in acquisition["documents"]
                ),
            },
            "protected_database_counts": {
                "facts": KnowledgeReleaseFact.objects.count(),
                "rules": PolicyRule.objects.count(),
                "evidence_spans": EvidenceSpan.objects.count(),
            },
            "application_acceptance": json.loads(acceptance.read_text())
            if acceptance.exists()
            else None,
        }
        atomic_json(repository / "output/demo-delivery.json", output)
        self.stdout.write(
            json.dumps(
                {k: v for k, v in output.items() if k not in {"plans", "map_fallback_reasons"}}
            )
        )
