"""Assemble reviewed flagship associations; retain every other candidate outside evidence."""

import json
import uuid
from pathlib import Path

from apps.adviser_v2.demo.evidence import atomic_json, digest
from apps.adviser_v2.demo.extraction import extract
from apps.adviser_v2.models import KnowledgeReleaseFact, PolicyVersionDocument
from django.conf import settings

root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
corpus = json.loads((root.parent / "retrieval-benchmark/corpus.json").read_text())
for plan in corpus["plans"]:
    roles = dict(PolicyVersionDocument.objects.filter(policy_version_id=plan["policy_version_id"])
                 .values_list("document_version_id", "role"))
    for doc in plan["documents"]:
        doc["role"] = roles[uuid.UUID(doc["document_version_id"])]
    plan["edition"] = "Preserved and reviewed Star manifest 2026-09-30"

admissions = [
    {"key": "hdfc-optima-secure", "name": "my: Optima Secure", "insurer": "HDFC ERGO",
     "uin": "HDFHLIP26058V082526", "variant": "Optima Secure", "variants": ["Optima Secure", "Optima Super Secure", "Optima Secure+"],
     "edition": "Official wording register: periods starting 2026-04-02 onwards; current paired prospectus",
     "hashes": ["195eb0499db9", "c882c2b1bd9b"]},
    {"key": "tata-medicare-premier", "name": "TATA AIG MediCare Premier", "insurer": "Tata AIG",
     "uin": "TATHLIP26052V052526", "variant": "Default", "variants": [],
     "edition": "2025 revision, new policies 2025-04-29 onwards; current downloads register and revision notice",
     "hashes": ["392feaeeb26c", "673c37dbe7d9", "4ed850042fd8", "449bdd6b7191"]},
    {"key": "bajaj-mhcp-edge", "name": "My Health Care Plan EDGE+ (Plan 9)", "insurer": "Bajaj General Insurance",
     "uin": "BAJHLIP26074V022526", "variant": "Plan 9", "variants": [f"Plan {i}" for i in range(1, 10)],
     "edition": "Current official EDGE+ downloads group; Plan 9 identified in prospectus; SMART rider unselected",
     "hashes": ["5e988f3df94f", "0c06eb9f18f1", "5d814e56e156", "8f41d9d4aa29", "1bc8982cdced"]},
    {"key": "manipal-prohealth-prime-protect", "name": "ProHealth Prime — Protect", "insurer": "ManipalCigna",
     "uin": "MCIHLIP26036V022526", "variant": "Protect", "variants": ["Protect", "Advantage", "Active"],
     "edition": "June 2025 wording with current Protect CIS, P&A prospectus and benefit-illustration annexures",
     "hashes": ["667c64813a3c", "b31bf0ab2bea", "85e575187372", "4741f2fec2ef", "c6b8580eeda9", "82fece393d13"]},
]
rows = json.loads((root / "flagship-candidates.json").read_text()) + json.loads((root / "manipal-candidates.json").read_text())
accepted = set()
for admission in admissions:
    plan_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "coverguide-demo:" + admission["key"] + ":" + admission["uin"]))
    documents, pages = [], []
    for prefix in admission["hashes"]:
        matches = [r for r in rows if r.get("sha256", "").startswith(prefix)]
        if len(matches) != 1:
            raise ValueError("Reviewed document association is missing or ambiguous: " + prefix)
        row = matches[0]
        if row["status"] != "acquired_unreviewed":
            raise ValueError("Reviewed document bytes are unavailable.")
        doc = {**row, "document_version_id": str(uuid.uuid5(uuid.NAMESPACE_URL, row["sha256"])),
               "document_key": admission["key"] + ":" + row["role"] + ":" + prefix,
               "uin": admission["uin"], "edition": admission["edition"],
               "evidence_use": "executable", "applicability": "current_official_association",
               "status": "acquired"}
        if prefix == "4741f2fec2ef":
            doc["role"] = "brochure"
        documents.append(doc)
        pages.extend(extract(doc, root))
        accepted.add(row["sha256"])
    corpus["plans"].append({**admission, "plan": admission["key"], "policy_version_id": plan_id,
        "plan_type": "medical_indemnity", "documents": documents, "pages": pages, "references": {}})
    print(admission["name"], len(documents), "PDFs", len(pages), "pages", flush=True)
references = {ref["id"] for p in corpus["plans"] for refs in p["references"].values() for ref in refs}
if len(references) != 236 or KnowledgeReleaseFact.objects.count() != 39:
    raise ValueError("The preserved Star regression counts changed.")
reference_snapshot = {"facts": 39, "distinct_reference_spans": len(references),
    "criterion_memberships": sum(len(refs) for p in corpus["plans"] for refs in p["references"].values()),
    "references_sha256": digest([{k: p[k] for k in ("policy_version_id", "references")} for p in corpus["plans"][:3]]),
    "facts_sha256": digest([{**row, "policy_version_id": str(row["policy_version_id"])} for row in KnowledgeReleaseFact.objects.order_by("policy_version_id", "criterion").values("policy_version_id", "criterion", "fact_sha256")])}
# UUIDs need a stable string representation for the public snapshot hash.
atomic_json(root / "corpus.json", corpus)
atomic_json(root / "reference-integrity.json", reference_snapshot)
atomic_json(root / "reference-only-candidates.json", [{**r, "evidence_use": "reference_only", "reason": "Not admitted to the selected flagship variant/edition."} for r in rows if r.get("sha256") not in accepted])
print("Corpus prepared", len(corpus["plans"]), "plans; Star references preserved", flush=True)
