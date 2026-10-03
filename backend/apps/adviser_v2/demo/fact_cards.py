"""Immutable cards assembled exclusively from version-two verified answers."""

import hashlib
import json
from pathlib import Path

from django.conf import settings

from .answers import answer_plan
from .cards import FIELDS
from .contracts import CardField
from .evidence import atomic_json, digest
from .fact_rules import project

CARD_FIELDS = (*FIELDS, "plan_type", "coverage_basis", "treatment_territory")
QUESTIONS = {
    "entry_age": "What are all new-application entry-age limits for adults and children, including units and conditions?",
    "renewal_age": "What are the renewal-age limits and lifelong renewal conditions?",
    "family": "Which exact family compositions, relationships and combinations can be insured, on each coverage basis?",
    "sum_insured": "What are all new-business sum insured choices and their age, variant and other conditions?",
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
        elif (index.id, field) in accepted_run:
            saved = accepted_run[(index.id, field)]
            atomic_json(path, saved)
        else:
            result = answer_plan(
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
    for field, result in fields.items():
        statements = (result.get("answer") or {}).get("statements", [])
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
        projected, legacy = project(field, result, index.variant)
        rules.extend(projected)
        base.update(legacy)
    models = sorted({m for r in fields.values() for m in r.get("models", [])})
    base.update(
        card_schema_version=2,
        quoted_fields=quoted,
        executable_rules=rules,
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
