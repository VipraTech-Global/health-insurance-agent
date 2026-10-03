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
    base, optional, unrelated = classify_clauses(saved, field, bundle)
    kept = []
    for statement in base:
        statement = governing(statement, field, bundle)
        if field == "coverage_basis" and not operative_basis(statement):
            unrelated.append(statement)
            continue
        if field in {
            "opd",
            "newborn",
            "restoration",
            "no_claim_bonus",
            "ayush",
        } and not variant_proven(statement, bundle):
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
            if re.search(r"preventive|health[ -]?check|reinstatement|family visit", main, re.I):
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
    return kept, optional, unrelated


def selectable_sums(statement, variant):
    """Recognize an explicit selectable list, never a benefit/premium sublimit."""
    import re
    from decimal import Decimal

    main = "\n".join(c["quote"] for c in statement["citations"])
    heading = re.search(r"sum\s*insured\s*(?:options?|choices?)\b[^\n]*\n", main, re.I)
    if heading:
        rest = main[heading.end() :]
        end = re.search(r"\n\s*(?:[A-Z][A-Za-z ]{3,}:|What\b)", rest)
        values_text = rest[: end.start()] if end else rest
        if re.search(r"subject to|provided|only|age|premium|limit", values_text, re.I):
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
    if re.search(r"\b(?:to|between|from)\b|[-–]\s*\d", values_text):
        return []
    from .fact_rule_grounding import money

    amounts = [v for v, _ in money(values_text)]
    unit = r"(?:lakhs?|lacs?|crores?|Cr\.?)"
    for match in re.finditer(
        r"(\d+(?:\.\d+)?(?:\s*[/,&]\s*\d+(?:\.\d+)?)*)\s*(" + unit + r")\b", values_text, re.I
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
    if field == "entry_age":
        from .fact_age_projection import project_ages

        return project_ages(statements, variant)
    if field == "sum_insured":
        rules = []
        for statement in statements:
            found = selectable_sums(statement, variant)
            if not found and re.search(
                r"sum\s*insured\s*(?:options?|choices?)",
                " ".join(c["quote"] for c in statement["citations"]),
                re.I,
            ):
                found = legacy_project(field, [statement], variant)
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
                result.extend(proposed)
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
                result.extend(legacy_project(field, [statement], variant))
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
                result.extend(legacy_project(field, [statement], variant))
        return result
    if field == "coverage_basis":
        rules = []
        for statement in statements:
            if not operative_basis(statement):
                continue
            raw = " ".join(" ".join(c["quote"].split()) for c in statement["citations"])
            match = re.search(
                r"Sum\s*Insured\s*on\s*Individual\s*Basis.*Sum\s*Insured\s*on\s*Floater\s*Basis",
                raw,
                re.I,
            )
            if match is None:
                match = re.search(
                    r"(?:available|offered|issued|taken|opted|cover(?:age|ed)?|policy).{0,110}(?:individual|floater).{0,75}basis",
                    raw,
                    re.I,
                )
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
    return rules


def project(field, statements, variant):
    from .fact_rule_grounding import grounded

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
        key = (rule["kind"], rule["value"], rule.get("relationship"), rule.get("unit"))
        if key not in distinct:
            distinct[key] = rule
        else:
            for cite in rule["citations"]:
                if cite not in distinct[key]["citations"]:
                    distinct[key]["citations"].append(cite)
    return list(distinct.values())
