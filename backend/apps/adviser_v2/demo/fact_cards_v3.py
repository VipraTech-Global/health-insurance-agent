"""Immutable cards assembled exclusively from version-two verified answers."""

import hashlib
import json
from pathlib import Path

from django.conf import settings

from .card_answers import answer_card_field
from .cards import FIELDS
from .contracts import CardField
from .evidence import atomic_json, digest
from .fact_rules_v3 import clauses, project

CARD_FIELDS = (*FIELDS, "plan_type", "coverage_basis", "treatment_territory")
QUESTIONS = {
    "entry_age": "Entry Age / Eligibility: minimum and maximum entry age for adults and dependent children, including printed days, months, years and each condition. Quote new business, not renewal.",
    "renewal_age": "Renewal: lifelong / lifetime renewability, maximum renewal age, no age limit, and renewal conditions. Do not substitute maximum entry age.",
    "ped_waiting": "STANDARD EXCLUSIONS — Pre-Existing Diseases (PED), Code Excl01 / Excl 01: expenses excluded until expiry of how many months of continuous coverage? Quote the baseline waiting period and all conditions. Keep optional waiting-period reduction or buy-back separately.",
    "specified_waiting": "STANDARD EXCLUSIONS — Specified Disease / Procedure waiting period, Code Excl02 / Excl 02: duration in months and all conditions, including accident exceptions and longer PED waits.",
    "maternity": "Base-plan maternity, childbirth and delivery: quoted inclusion or general exclusion and any waiting period and limits. Separately identify any optional add-on or rider requiring extra premium. Do not describe a rider as a base benefit.",
    "opd": "Base-plan outpatient (OPD) illness treatment and medical consultations: quoted inclusion or exclusion, limits and conditions. Preventive health-check vouchers are not OPD treatment. Separate optional add-on cover requiring extra premium.",
    "family": "Which exact family compositions, relationships and combinations can be insured, on each coverage basis?",
    "sum_insured": "Base Sum Insured / Sum Insured Options / Table of Benefits / Schedule: list every printed selectable sum insured amount, in rupees or lakhs, for this variant. Include list/table headings, age or family restrictions, and distinguish cumulative bonuses and benefit sublimits.",
    "geography": "What purchase eligibility or residence geography applies? Distinguish this from treatment territory and premium zones.",
    "plan_type": "What kind of insurance is this: medical indemnity, top-up, super top-up, critical illness or fixed benefit? Quote the explicit product description.",
    "coverage_basis": "Is the cover on an individual or family floater basis, and what restrictions apply?",
    "treatment_territory": "Where is treatment covered, and what territory restrictions apply?",
}


def build(index, root, accepted_run, questions, *, relay=None):
    from .services import bundle_for

    bundle = bundle_for(index)
    cache = root / "fields" / index.id
    cache.mkdir(parents=True, exist_ok=True)
    fields = {}
    provenance = {}
    for field in CARD_FIELDS:
        path = cache / (field + ".json")
        if path.exists():
            saved = json.loads(path.read_text())
        else:
            result = answer_card_field(
                bundle,
                QUESTIONS.get(
                    field,
                    questions[field]
                    if field in questions
                    else f"What are the {field.replace('_', ' ')} benefits and all conditions?",
                ),
                method="H",
                priority="background",
                relay=relay,
            )
            if result["status"] == "temporarily_unavailable":
                # A failed operational attempt remains resumable, never a
                # silently cached absence of policy evidence.
                atomic_json(cache / (field + ".failure.json"), result)
                raise RuntimeError(
                    f"{index.name}/{field}: {result.get('reason', result['status'])}"
                )
            saved = {
                "result": result,
                "provenance": {"method": "fresh_card_answer", "index": index.id},
            }
            atomic_json(path, saved)
        fields[field] = saved["result"]
        provenance[field] = saved["provenance"]
    base = dict(index.card)
    base.update(entry_ages=[], renewal_ages=[], family_rule=None, common_needs=[], status="partial")
    quoted = {}
    rules = []
    optional_fields = {}
    statuses = {}
    for field, result in fields.items():
        statements, optional, unrelated = clauses(result, field, bundle)
        optional_fields[field] = (
            {"status": "optional, extra premium", "statements": optional} if optional else None
        )
        stated = result["status"] == "answered" and bool(statements)
        value = CardField(
            state="stated" if stated else "not_stated",
            labels=[s["text"] for s in statements] if stated else [],
            citations=[c for s in statements for c in s["citations"]] if stated else [],
            conditions=[c for s in statements for c in [*s["conditions"], *s["restrictions"]]]
            if stated
            else [],
        ).model_dump()
        quoted[field] = value
        if field in {
            "sum_insured",
            "geography",
            "copay",
            "room_limit",
            "ped_waiting",
            "maternity",
            "opd",
        }:
            base[field] = value
        base["common_needs"].append({"field": field, "value": value})
        projected = project(field, statements, index.variant)
        rules.extend(projected)
        statuses[field] = (
            "not covered"
            if any(r["kind"] == "coverage" and r["value"] == "not_covered" for r in projected)
            else "stated"
            if stated
            else "not stated"
        )
    models = sorted({m for r in fields.values() for m in r.get("models", [])})
    base.update(
        card_schema_version=3,
        quoted_fields=quoted,
        executable_rules=rules,
        optional_covers=optional_fields,
        field_statuses=statuses,
        field_coverage={
            f: v["state"] == "stated" and bool(v["citations"]) for f, v in quoted.items()
        },
        rule_coverage={f: any(r["field"] == f for r in rules) for f in CARD_FIELDS},
        models=models,
        model=models[0] if len(models) == 1 else None,
    )
    # The existing validated chart is copied by content hash. It is never
    # reinterpreted, nor may a replacement index chart change an old card.
    chart = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer/premiums" / (index.id + ".json")
    if chart.exists():
        raw = chart.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        frozen = root / "prices" / (sha + ".json")
        frozen.parent.mkdir(exist_ok=True)
        if frozen.exists() and frozen.read_bytes() != raw:
            raise ValueError("Price hash collision.")
        if not frozen.exists():
            frozen.write_bytes(raw)
        base.update(pricing_artifact=str(frozen), pricing_sha256=sha)
    identity = digest(
        {
            "card": base,
            "provenance": provenance,
            "manifest": json.loads((root / "manifest.json").read_text()),
        }
    )
    base["card_version"] = identity
    audit = root / "cards" / (identity + ".json")
    atomic_json(audit, {"card": base, "provenance": provenance, "fields": fields})
    return identity, base, audit
