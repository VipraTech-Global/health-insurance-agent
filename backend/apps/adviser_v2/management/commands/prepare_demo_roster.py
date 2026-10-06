import json
import uuid
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.adviser_v2.demo.acquisition import INSURERS
from apps.adviser_v2.demo.contracts import CardField, PlanCard
from apps.adviser_v2.demo.evidence import atomic_json, digest
from apps.adviser_v2.models import DemoPlanIndex

FLAGSHIPS = {
    "star": ("Star Comprehensive", "star-comprehensive"),
    "care": ("Care Supreme", "care-supreme"),
    "niva": ("ReAssure 3.0", "niva-reassure-3"),
    "hdfc": ("my: Optima Secure", "hdfc-optima-secure"),
    "icici": ("Elevate", "icici-elevate"),
    "aditya": ("Activ One MAX", "aditya-activ-one-max"),
    "bajaj": ("My Health Care Plan EDGE+ (Plan 9)", "bajaj-mhcp-edge"),
    "newindia": ("New India Floater Mediclaim", "newindia-floater"),
    "tata": ("TATA AIG MediCare Premier", "tata-medicare-premier"),
    "manipal": ("ProHealth Prime — Protect", "manipal-prohealth-prime-protect"),
}


class Command(BaseCommand):
    help = "Preserve thirteen evaluation slots and make unavailable insurer flagships visible in the picker."

    def handle(self, **options):
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
        corpus = json.loads((root / "corpus.json").read_text())
        by_key = {p["plan"]: p for p in corpus["plans"]}
        slots = [
            {"id": "existing-" + p["plan"], "name": p["plan"], "plan_id": p["policy_version_id"]}
            for p in corpus["plans"][:3]
        ]
        for insurer_id, insurer, url in INSURERS:
            name, key = FLAGSHIPS[insurer_id]
            plan = by_key.get(key)
            slot = {"id": "flagship-" + insurer_id, "name": name, "insurer": insurer}
            if plan:
                slot["plan_id"] = plan["policy_version_id"]
                if insurer_id == "star":
                    slot["note"] = (
                        "Repeated Star Comprehensive slot; physical PDFs deduplicated and fixed evaluation weighting retained."
                    )
            else:
                reason = "Current official flagship documents could not be acquired and edition applicability remains unresolved."
                if insurer_id == "niva":
                    reason = "Official PDF endpoints returned non-PDF/CAPTCHA responses; source files unavailable."
                if insurer_id == "icici":
                    reason = "Current product page UIN ICIHLIP27057V062627 differs from the older located wording; no current applicable PDF acquired."
                slot.update(plan_id=None, unavailable_reason=reason)
                plan_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "coverguide-demo-unavailable:" + key))
                bundle = {
                    "policy_version_id": plan_id,
                    "plan": key,
                    "name": name,
                    "insurer": insurer,
                    "variant": "Default",
                    "plan_type": "medical_indemnity",
                    "documents": [],
                    "pages": [],
                    "sections": [],
                    "navigation": [],
                    "availability": "documents_unavailable",
                    "unavailable_reason": reason,
                    "source_url": url,
                }
                index_id = digest(bundle)
                bundle["index_id"] = index_id
                path = root / "indexes" / (index_id + ".json")
                atomic_json(path, bundle)
                unknown = CardField(state="not_stated")
                card = PlanCard(
                    plan_id=plan_id,
                    index_version=index_id,
                    insurer=insurer,
                    name=name,
                    variant="Default",
                    plan_type="medical_indemnity",
                    model=None,
                    status="documents_unavailable",
                    entry_ages=[],
                    renewal_ages=[],
                    family_rule=None,
                    sum_insured=unknown,
                    geography=unknown,
                    copay=unknown,
                    room_limit=unknown,
                    ped_waiting=unknown,
                    maternity=unknown,
                    opd=unknown,
                )
                DemoPlanIndex.objects.get_or_create(
                    id=index_id,
                    defaults={
                        "plan_key": plan_id,
                        "insurer": insurer,
                        "name": name,
                        "plan_type": "medical_indemnity",
                        "bundle_path": str(path),
                        "card": card.model_dump(),
                        "coverage": {
                            "status": "documents_unavailable",
                            "documents": 0,
                            "pages": 0,
                            "sections": 0,
                            "map_fallbacks": 0,
                            "reason": reason,
                        },
                        "edition": "Unresolved; no executable evidence",
                    },
                )
            slots.append(slot)
        atomic_json(root / "evaluation-slots.json", slots)
        self.stdout.write("Thirteen slots retained, including repeated Star and unavailable cases.")
