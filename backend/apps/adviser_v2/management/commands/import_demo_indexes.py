import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.adviser_v2.demo.contracts import CardField, PlanCard
from apps.adviser_v2.demo.evidence import Section, atomic_json, digest
from apps.adviser_v2.demo.search import embed
from apps.adviser_v2.models import DemoPlanIndex, DemoSectionVector, PolicyVersion


class Command(BaseCommand):
    help = "Persist immutable demo indexes; facts remain not-stated until winner-based card extraction."

    def add_arguments(self, parser):
        parser.add_argument("--embed", action="store_true")

    def handle(self, **options):
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
        source = root / "sections.json"
        if not source.exists():
            raise CommandError("Map/section processing has not completed.")
        corpus = json.loads(source.read_text())
        for plan in corpus["plans"]:
            version = PolicyVersion.objects.select_related("product__insurer").filter(pk=plan["policy_version_id"]).first()
            if version:
                name = version.product.name
                insurer = version.product.insurer.name
                uin = version.uin or ""
                plan_type = version.product.benefit_type
            else:
                name, insurer, uin = plan["name"], plan["insurer"], plan.get("uin", "")
                plan_type = plan["plan_type"]
            bundle = {k: v for k, v in plan.items() if k not in {"chunks", "references"}}
            key = digest(bundle)
            bundle["index_id"] = key
            path = root / "indexes" / (key + ".json")
            if path.exists() and json.loads(path.read_text()) != bundle:
                raise CommandError("Immutable index collision.")
            atomic_json(path, bundle)
            unknown = CardField(state="not_stated")
            card = PlanCard(plan_id=plan["policy_version_id"], index_version=key, insurer=insurer,
                name=name, variant=plan.get("variant", "Default"), plan_type=plan_type, model=None,
                status="partial", entry_ages=[], renewal_ages=[], family_rule=None, sum_insured=unknown,
                geography=unknown, copay=unknown, room_limit=unknown, ped_waiting=unknown,
                maternity=unknown, opd=unknown)
            model_names = set()
            for doc in plan["documents"]:
                map_path = root / "maps" / (doc["sha256"] + ".json")
                if map_path.exists():
                    model_names.update(json.loads(map_path.read_text()).get("models", []))
            index, created = DemoPlanIndex.objects.get_or_create(id=key, defaults={
                "plan_key": plan["policy_version_id"], "insurer": insurer, "name": name,
                "variant": card.variant, "plan_type": plan_type, "uin": uin,
                "edition": str(plan.get("edition", "Preserved source bundle; currentness pending")),
                "bundle_path": str(path), "card": card.model_dump(), "models_used": sorted(model_names),
                "coverage": {"status": "partial", "documents": len(plan["documents"]),
                    "pages": len(plan["pages"]), "sections": len(plan["sections"]),
                    "map_fallbacks": sum(d["status"] == "fallback" for d in plan["document_status"]),
                    "pending_documents": sum(d["status"] == "pending" for d in plan["document_status"])}})
            if options["embed"]:
                for payload in plan["sections"]:
                    section = Section.from_payload(payload)
                    text_hash = digest(section.index_text)
                    existing = DemoSectionVector.objects.filter(index=index, section_id=section.id).first()
                    if existing:
                        if existing.text_sha256 != text_hash:
                            raise CommandError("Section embedding source changed.")
                        continue
                    reusable = DemoSectionVector.objects.filter(section_id=section.id, text_sha256=text_hash).first()
                    cached_path = root / "vectors" / (text_hash + ".json")
                    if reusable:
                        vector = reusable.embedding
                    elif cached_path.exists():
                        cached = json.loads(cached_path.read_text())
                        if (cached["text_sha256"] != text_hash or cached["model"] != "BAAI/bge-m3"
                                or cached["revision"] != "5617a9f61b028005a4858fdac845db406aefb181"):
                            raise CommandError("Staged vector cache identity differs.")
                        vector = cached["vector"]
                    else:
                        vector = embed([section.index_text], priority="background")[0]
                    DemoSectionVector.objects.create(index=index, section_id=section.id,
                                                     embedding=vector, text_sha256=text_hash)
            self.stdout.write(f"{name}: {len(plan['sections'])} sections; index {key}; new={created}")
