"""Current projection facade; historical query-run parsers stay hash-pinned."""

import re
from copy import deepcopy

from .fact_governing import governing, operative_basis, variant_proven
from .fact_rules_v6 import clauses as classify_clauses
from .fact_rules_v6 import project as legacy_project
from .quotations import locate, normalized

__all__ = ["clauses", "project"]


def clauses(result, field, bundle):
    # Source-location matching begins at the first non-whitespace character.
    # Remove only boundary whitespace before computing a relative field-row
    # offset, otherwise an indented quotation can select a later occurrence.
    saved = deepcopy(result)
    for statement in (saved.get("answer") or {}).get("statements", []):
        for citation in statement["citations"]:
            citation["quote"] = citation["quote"].strip()
    # Field blocks are clipped before scope classification, so a preceding
    # rider footnote or a following optional benefit does not reclassify the
    # independently headed eligibility clause. Source scope is still checked.
    if saved.get("answer") and field in {
        "entry_age",
        "coverage_basis",
        "sum_insured",
        "family",
        "geography",
    }:
        saved["answer"]["statements"] = (
            [governing(s, field, bundle) for s in (saved.get("answer") or {}).get("statements", [])]
            if saved.get("answer")
            else []
        )
    base, optional, unrelated = classify_clauses(saved, field, bundle)
    from .fact_fit_projection import optional_table, optional_unit

    if field == "plan_type":
        for statement in list(unrelated):
            raw = " ".join(c["quote"] for c in statement["citations"])
            if re.search(
                r"(?:shall|will) indemnify.{0,180}(?:Medical Expenses|Hospitalization|Insured Person)|indemnify Medical Expenses",
                raw,
                re.I | re.S,
            ):
                unrelated.remove(statement)
                base.append(statement)
    if field == "opd":
        from .fact_fit_projection import outpatient_exclusion

        for statement in list(optional):
            if outpatient_exclusion(statement):
                optional.remove(statement)
                base.append(statement)
    kept = []
    for statement in base:
        if optional_unit(statement, field) or optional_table(statement, bundle):
            optional.append(statement)
            continue
        statement = governing(statement, field, bundle)
        if field == "coverage_basis" and not operative_basis(statement):
            unrelated.append(statement)
            continue
        if (
            field
            in {
                "opd",
                "newborn",
                "restoration",
                "no_claim_bonus",
                "ayush",
                "room_limit",
            }
            and not variant_proven(statement, bundle)
            and not (field == "opd" and outpatient_exclusion(statement))
            and not (
                field == "room_limit"
                and re.search(
                    r"Room\s*rent\s*limit\s*(?:shall be|is|:)\s*['\"‘’“”]?At\s*Actuals",
                    " ".join(c["quote"] for c in statement["citations"]),
                    re.I,
                )
            )
        ):
            result.setdefault("projection_omissions", []).append(
                "Shared benefit has no verified selected-variant column: " + field
            )
            unrelated.append(statement)
            continue
        main = "\n".join(c["quote"] for c in statement["citations"])
        if (
            field == "opd"
            and re.search(r"health[ -]?check|voucher", main, re.I)
            and not re.search(r"illness|disease|injury", main, re.I)
        ):
            unrelated.append(statement)
            continue
        if field == "sum_insured":
            if re.search(
                r"preventive|health[ -]?check|reinstatement|family visit|booster|worked example|illustrat|accumulat|carry forward",
                main,
                re.I,
            ):
                unrelated.append(statement)
                continue
            trimmed = []
            for cite in statement["citations"]:
                raw = cite["quote"]
                head = re.search(r"(?mi)^[^\n]*sum\s*insured\s*(?:options?|choices?)[^\n]*\n", raw)
                if head:
                    following = re.search(r"\n\s*(?:What\b|[A-Z][A-Za-z ]{3,}:)", raw[head.end() :])
                    end = head.end() + following.start() if following else len(raw)
                    selected = raw[head.start() : end]
                    section = next(
                        (s for s in bundle["sections"] if s["id"] == cite["section_id"]), None
                    )
                    segment = (
                        next(
                            (p for p in section["segments"] if p["page_id"] == cite["page_id"]),
                            None,
                        )
                        if section
                        else None
                    )
                    if segment:
                        origin, _ = locate(segment["text"], raw, cite.get("occurrence", 0))
                        target = origin + head.start() + normalized(selected)[1][0]
                        occurrence = 0
                        while locate(segment["text"], selected, occurrence)[0] != target:
                            occurrence += 1
                        cite = {**cite, "quote": selected, "occurrence": occurrence}
                trimmed.append(cite)
            statement = {
                **statement,
                "citations": trimmed,
                "text": "\n\n".join(c["quote"] for c in trimmed),
                "excerpts": [c["quote"] for c in trimmed],
            }
        kept.append(statement)
    if field == "sum_insured":
        from .fact_list_projection import complete_sum_list

        kept = [complete_sum_list(result, bundle, s) for s in kept]
        from .fact_table_projection import resolve_sum_grid

        kept = resolve_sum_grid(result, bundle, kept)
    if field == "opd" and len(bundle.get("variants", [])) > 1:
        from .fact_table_projection import resolve_sum_grid

        kept = resolve_sum_grid(result, bundle, [], field="opd") or kept
    if field == "room_limit" and len(bundle.get("variants", [])) > 1:
        from .fact_table_projection import resolve_sum_grid

        kept = resolve_sum_grid(result, bundle, [], field="room_limit") or kept
    return kept, optional, unrelated


def selectable_sums(statement, variant):
    """Recognize an explicit selectable list, never a benefit/premium sublimit."""
    import re
    from decimal import Decimal

    main = "\n".join(c["quote"] for c in statement["citations"])
    if re.search(r"booster|worked example|illustrat|accumulat|carry forward", main, re.I):
        return []
    heading = re.search(
        r"sum\s*insured\s*(?:(?:options?|choices?)\b|\(SI\))[^\n:]*[:\n]", main, re.I
    )
    if heading:
        rest = main[heading.end() :]
        end = re.search(
            r"(?:\n\s*(?:[A-Z][A-Za-z ]{3,}:|What\b)|The Sum Insured opted|\bPolicy Coverage\b)",
            rest,
        )
        values_text = rest[: end.start()] if end else rest
        if re.search(r"subject to|provided|only|\bage\b|premium|\blimit\b", values_text, re.I):
            return []
    elif statement.get("table") and re.search(r"sum\s*insured", main, re.I):
        numeric = [
            c["quote"]
            for c in statement["citations"]
            if re.fullmatch(r"[\d\s.,/&₹()-]+(?:lakhs?|lacs?|crores?|Cr\.?)?", c["quote"], re.I)
        ]
        if len(numeric) != 1:
            return []
        values_text = numeric[0]
        if not re.search(r"lakh|lac|crore|\bCr\b|₹|Rs\b|INR", values_text, re.I):
            unit_heading = re.search(r"\bin\s+(lakhs?|lacs?|crores?)\b", main, re.I)
            if not unit_heading:
                return []
            values_text += " " + unit_heading[1]
    else:
        return []
    if re.search(
        r"up to|upto|booster|example|illustrat|\b(?:to|between|from)\b|[-–]\s*\d", values_text, re.I
    ):
        return []
    from .fact_rule_grounding import money

    amounts = [v for v, _ in money(values_text)]
    unit = r"(?:lakhs?|lacs?|crores?|Cr\.?|L)"
    for match in re.finditer(
        r"(\d+(?:\.\d+)?(?:\s*[/,&]\s*\d+(?:\.\d+)?)*)\s*(" + unit + r")(?=\b|\d)",
        values_text,
        re.I,
    ):
        multiplier = 10000000 if match[2].lower().startswith("cr") else 100000
        amounts.extend(int(Decimal(n) * multiplier) for n in re.findall(r"\d+(?:\.\d+)?", match[1]))
    if not amounts or any(v <= 0 for v in amounts):
        return []
    from .fact_rules_v6 import text

    return [
        {
            "field": "sum_insured",
            "kind": "choices",
            "value": "|".join(map(str, sorted(set(amounts)))),
            "printed": next(c["quote"] for c in statement["citations"]),
            "choices": sorted(set(amounts)),
            "unit": "rupees",
            "unlimited_choice": bool(re.search(r"\bunlimited\b", values_text, re.I)),
            "variant": variant,
            "scope": "base",
            "citations": [
                c
                for item in [
                    statement,
                    *statement.get("conditions", []),
                    *statement.get("restrictions", []),
                ]
                for c in item["citations"]
            ],
            "conditions": [
                text(item)
                for item in [*statement.get("conditions", []), *statement.get("restrictions", [])]
            ],
            "condition_mode": "quoted",
            "guards": [],
            "supported": True,
            "exhaustive": bool(statement.get("complete_options")),
        }
    ]


def _project(field, statements, variant):
    from .fact_fit_projection import base_coverage, family_rule, purchase_geography

    if field == "plan_type":
        result = legacy_project(field, statements, variant)
        if result:
            return result
        from .fact_fit_projection import raw_text, rule_for

        for statement in statements:
            raw = raw_text(statement)
            match = re.search(
                r"(?:shall|will) indemnify.{0,180}(?:Medical Expenses|Hospitalization|Insured Person)|indemnify Medical Expenses",
                raw,
                re.I,
            )
            if match:
                result.append(
                    rule_for(statement, field, "type", "medical_indemnity", variant, match[0])
                )
        return result
    if field == "geography":
        return [r for s in statements for r in purchase_geography(s, variant)]
    if field == "family":
        rules = legacy_project(field, statements, variant) or [
            r for s in statements for r in family_rule(s, variant)
        ]
        for rule in rules:
            raw = " ".join(" ".join(c["quote"].split()) for c in rule["citations"])
            if re.search(
                r"relationship between the Insureds will always have to be Primary Insured and their Spouse",
                raw,
                re.I,
            ):
                rule["primary_spouse_pair_only"] = True
        return rules
    if field == "entry_age":
        from .fact_age_projection import project_ages

        return project_ages(statements, variant)
    if field == "sum_insured":
        rules = []
        for statement in statements:
            found = selectable_sums(statement, variant)
            rules.extend(found)
        return rules
    if field in {"ped_waiting", "specified_waiting"}:
        result = []
        for statement in statements:
            raw = " ".join(c["quote"] for c in statement["citations"])
            target = (
                r"Pre[ -]?Existing|Excl\s*0?1\b"
                if field == "ped_waiting"
                else r"Specified|Specific|Excl\s*0?2\b"
            )
            heading = re.search(target, raw, re.I)
            if not heading:
                continue
            operative = raw[heading.start() :]
            other = re.search(
                r"Pre[ -]?Existing|Excl\s*0?1\b"
                if field == "specified_waiting"
                else r"Specified|Specific|Excl\s*0?2\b",
                operative[1:],
                re.I,
            )
            if other:
                operative = operative[: other.start() + 1]
            durations = list(
                re.finditer(
                    r"(?:expiry of|after|period of|for|is|:)\s*(\d+)\s*(months?|years?)",
                    operative,
                    re.I,
                )
            )
            # Exactly one governing duration; a later PED condition cannot set
            # the specified-disease duration.
            values = {int(m[1]) * (12 if m[2].lower().startswith("year") else 1) for m in durations}
            if len(values) != 1:
                continue
            for rule in legacy_project(field, [statement], variant):
                if rule["value"] == str(next(iter(values))):
                    result.append(rule)
        return result
    if field == "room_limit":
        result = []
        explicit = []
        for statement in statements:
            raw = " ".join(c["quote"] for c in statement["citations"])
            match = re.search(
                r"Room\s*rent\s*limit\s*(?:shall be|is|:)\s*['\"‘’“”]?(At\s*Actuals)", raw, re.I
            )
            proposed = legacy_project(field, [statement], variant)
            if match and proposed:
                rule = {**proposed[0], "kind": "room", "value": "actuals", "printed": match[1]}
                rule.pop("percent", None)
                rule.pop("unit", None)
                explicit.append(rule)
            else:
                for rule in proposed:
                    if rule["value"] in {"any_room", "any_room_except_suite"} and re.search(
                        r"(?:except|excluding).{0,20}deluxe.{0,12}suite", raw, re.I
                    ):
                        rule = {**rule, "value": "any_room_except_deluxe_suite"}
                    result.append(rule)
        return explicit or result
    if field in {"opd", "newborn", "restoration", "ayush"}:
        result = []
        for statement in statements:
            raw = " ".join(c["quote"] for c in statement["citations"])
            if statement.get("table") and re.search(
                r"\bNot\s+Available\b|\bNot\s+Covered\b", raw, re.I
            ):
                negative = re.search(r"\bNot\s+Available\b|\bNot\s+Covered\b", raw, re.I)
                result.append(
                    {
                        "field": field,
                        "kind": "coverage",
                        "value": "not_covered",
                        "printed": negative[0],
                        "variant": variant,
                        "scope": "base",
                        "citations": statement["citations"],
                        "conditions": [
                            i["text"]
                            for i in [
                                *statement.get("conditions", []),
                                *statement.get("restrictions", []),
                            ]
                        ],
                        "condition_mode": "quoted",
                        "guards": [],
                        "supported": True,
                    }
                )
            else:
                result.extend(
                    base_coverage(statement, field, variant)
                    or legacy_project(field, [statement], variant)
                )
        return result
    if field == "maternity":
        result = []
        for statement in statements:
            raw = " ".join(c["quote"] for c in statement["citations"])
            exclusion = re.search(r"Maternity.{0,65}Excl\s*\d+", raw, re.I | re.S)
            if exclusion:
                result.append(
                    {
                        "field": field,
                        "kind": "coverage",
                        "value": "not_covered",
                        "printed": exclusion[0],
                        "variant": variant,
                        "scope": "base",
                        "citations": statement["citations"],
                        "conditions": [
                            i["text"]
                            for i in [
                                *statement.get("conditions", []),
                                *statement.get("restrictions", []),
                            ]
                        ],
                        "condition_mode": "quoted",
                        "guards": [],
                        "supported": True,
                    }
                )
            else:
                result.extend(
                    base_coverage(statement, field, variant)
                    or legacy_project(field, [statement], variant)
                )
        return result
    if field == "coverage_basis":
        rules = []
        for statement in statements:
            if not operative_basis(statement):
                continue
            raw = " ".join(" ".join(c["quote"].split()) for c in statement["citations"])
            from .fact_fit_projection import basis_match

            match = basis_match(raw)
            if match is None:
                continue
            values = [
                v for v in ("individual", "floater") if re.search(r"\b" + v + r"\b", match[0], re.I)
            ]
            rules.append(
                {
                    "field": field,
                    "kind": "basis",
                    "value": "|".join(values),
                    "printed": match[0],
                    "variant": variant,
                    "scope": "base",
                    "citations": statement["citations"],
                    "conditions": [
                        i["text"]
                        for i in [
                            *statement.get("conditions", []),
                            *statement.get("restrictions", []),
                        ]
                    ],
                    "condition_mode": "quoted",
                    "guards": [],
                    "supported": True,
                    "exhaustive": len(values) == 2
                    or bool(
                        re.search(
                            r"only.{0,30}(?:individual|floater)|(?:individual|floater).{0,30}only",
                            match[0],
                            re.I,
                        )
                    ),
                }
            )
        return rules
    rules = legacy_project(field, statements, variant)
    if field == "copay":
        for rule in rules:
            raw = " ".join(c["quote"] for c in rule["citations"])
            if re.search(
                r"room categor|failure to intimate|fail to intimate|breach|category claimed",
                raw,
                re.I,
            ):
                rule["restricted_scope"] = True
    return rules


def project(field, statements, variant):
    from .fact_fit_projection import optional_unit
    from .fact_rule_grounding import grounded

    statements = [s for s in statements if not optional_unit(s, field)]
    rules = [r for r in _project(field, statements, variant) if grounded(r)]
    if field == "coverage_basis" and len(rules) > 1:
        values = {v for rule in rules for v in rule["value"].split("|")}
        if values == {"individual", "floater"} and not any(
            r.get("exhaustive") and "|" not in r["value"] for r in rules
        ):
            combined = {
                **rules[0],
                "value": "individual|floater",
                "exhaustive": True,
                "citations": [c for r in rules for c in r["citations"]],
                "conditions": list(dict.fromkeys(c for r in rules for c in r["conditions"])),
            }
            rules = [combined]
    distinct = {}
    for rule in rules:
        # Never merge different conditions or applicability into a single rule.
        import json

        key = json.dumps(
            {k: v for k, v in rule.items() if k not in {"citations", "printed", "conditions"}},
            sort_keys=True,
        )
        if key not in distinct:
            distinct[key] = rule
        else:
            distinct[key]["conditions"] = list(
                dict.fromkeys([*distinct[key].get("conditions", []), *rule.get("conditions", [])])
            )
            for cite in rule["citations"]:
                if cite not in distinct[key]["citations"]:
                    distinct[key]["citations"].append(cite)
    return list(distinct.values())
