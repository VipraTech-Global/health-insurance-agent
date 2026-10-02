"""Run via isolated manage shell; acquire official flagship candidates for edition review."""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from apps.adviser_v2.demo.acquisition import acquire, discover_one
from apps.adviser_v2.demo.evidence import atomic_json
from django.conf import settings

root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
extra = [
    ("hdfc-prospectus", "HDFC ERGO", "https://www.hdfcergo.com/download/prospectus/health"),
    ("hdfc-brochure", "HDFC ERGO", "https://www.hdfcergo.com/download/brochures/health"),
    ("aditya-one", "Aditya Birla Health Insurance", "https://www.adityabirlacapital.com/healthinsurance/activ-one"),
    ("icici-elevate", "ICICI Lombard", "https://www.icicilombard.com/health-insurance/elevate"),
    ("newindia-family", "New India Assurance", "https://www.newindia.co.in/health-insurance/floater-mediclaim-policy"),
    ("manipal-prime", "ManipalCigna", "https://www.manipalcigna.com/hospitalization-cover/prohealth-prime"),
    ("care-supreme", "Care Health Insurance", "https://www.careinsurance.com/product/care-supreme"),
]
with ThreadPoolExecutor(max_workers=7) as pool:
    for row in pool.map(lambda seed: discover_one(seed, root / "discovery"), extra):
        print(row["insurer_id"], row["status"], len(row["documents"]), flush=True)
patterns = {"hdfc": r"optima.*secure", "tata": r"medicare.premier", "bajaj": r"mhcp.edge|mhcpedge",
            "niva": r"reassure.?3|reassure30", "newindia": r"floater|family",
            "aditya": r"activ.?one|active.one", "icici": r"elevate", "manipal": r"prime", "care": r"supreme"}
selected = {}
for path in (root / "discovery").glob("*-discovery.json"):
    row = json.loads(path.read_text())
    key = row["insurer_id"].split("-")[0]
    pattern = patterns.get(key)
    if not pattern:
        continue
    for doc in row["documents"]:
        if doc["role"] != "excluded" and re.search(pattern, doc["url"] + " " + doc["label"], re.I):
            selected[doc["url"]] = {**doc, "insurer_id": key, "insurer": row["insurer"]}
results = []
with ThreadPoolExecutor(max_workers=6) as pool:
    jobs = {pool.submit(acquire, doc, root): doc for doc in selected.values()}
    for future in as_completed(jobs):
        row = future.result()
        results.append(row)
        atomic_json(root / "flagship-candidates.json", results)
        print(row["insurer_id"], row["status"], row["label"][:80], flush=True)
print("Candidate acquisitions", len(results), flush=True)
