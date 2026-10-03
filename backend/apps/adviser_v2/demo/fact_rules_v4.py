"""Typed values extracted by bounded grammars from original verified clauses.

Every numeric value comes from a regex capture in its cited clause. Unit
conversion is explicit and the printed expression is preserved. Optional cover
is retained for display, never projected into a base-plan requirement.
"""

import json
import re
from decimal import Decimal

from .quotations import normalized

KEYWORDS = {
    "entry_age": r"entry|eligible|eligibility|aged|age of|age at|age limit",
    "renewal_age": r"renew",
    "family": r"family|adult|children|child|spouse|parent",
    "sum_insured": r"sum\s*insured",
    "coverage_basis": r"individual|floater",
    "plan_type": r"indemnity|top.up|critical illness|fixed benefit",
    "maternity": r"maternity|delivery|deliveries|childbirth|child.birth|pregnan",
    "newborn": r"new.born|newborn",
    "opd": r"out.patient|outpatient|\bopd\b",
    "ped_waiting": r"pre.existing|\bPED\b|Excl\s*0?1",
    "specified_waiting": r"specified|specific disease|Excl\s*0?2",
    "copay": r"co.pay|copay|co.payable",
    "room_limit": r"room|boarding",
    "restoration": r"restor|recharg|reinstate",
    "no_claim_bonus": r"bonus|no.claim",
    "deductible": r"deductible",
    "ayush": r"AYUSH|Ayurveda|Unani|Siddha|Homeopath",
}
OPTIONAL = re.compile(
    r"\b(?:optional|add[ -]?on|rider|additional premium|extra premium|Parenthood|Optima Wellbeing|Fetal Flourish)\b",
    re.I,
)
NEGATIVE = re.compile(
    r"\b(?:not covered|not payable|not available|excluded|shall not pay|will not pay|no cover)\b",
    re.I,
)
POSITIVE = re.compile(
    r"\b(?:covered|cover|payable|pay|reimburse|indemnify|expenses|benefit)\b", re.I
)
MONEY = re.compile(
    r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(lakhs?|lacs?|crores?)?|\b(\d+(?:\.\d+)?)\s*(lakhs?|lacs?|crores?)\b",
    re.I,
)


def text(statement):
    return " ".join(
        " ".join(c["quote"].split())
        for item in [
            statement,
            *statement.get("conditions", []),
            *statement.get("restrictions", []),
        ]
        for c in item["citations"]
    )


def money(raw):
    found = []
    for match in MONEY.finditer(raw):
        amount = Decimal((match[1] or match[3]).replace(",", ""))
        unit = (match[2] or match[4] or "").lower()
        amount *= 10000000 if unit.startswith("crore") else 100000 if unit else 1
        if amount == int(amount):
            found.append((int(amount), match[0]))
    return found


def scope(statement, field, bundle):
    raw = text(statement)
    selected = {c["section_id"] for c in statement["citations"]}
    sections = [s for s in bundle["sections"] if s["id"] in selected]
    optional = bool(OPTIONAL.search(raw)) or any(
        s["role"] in {"rider", "add_on", "addon", "optional_cover"} for s in sections
    )
    # A scope heading can precede the selected clause. Inspect the same source
    # section, never PageIndex navigation descriptions or another document.
    for section in sections:
        for segment in section["segments"]:
            for c in statement["citations"]:
                if c["page_id"] != segment["page_id"]:
                    continue
                original = segment["text"]
                target = normalized(c["quote"])[0]
                normalized_source, offsets = normalized(original)
                found = normalized_source.find(target)
                if found < 0:
                    continue
                before = original[max(0, offsets[found] - 1600) : offsets[found]]
                headings = list(
                    re.finditer(
                        r"(?im)^\s*(?:\d+(?:\.\d+)*[.)]?\s*)?(?:optional[^\n]{0,100}|[^\n]{0,65}(?:add[ -]?on|rider)[^\n]{0,65})\s*$",
                        before,
                    )
                )
                if headings:
                    optional = True
    if field == "opd" and re.search(r"health[ -]?check|check.up|voucher", raw, re.I):
        # Preventive services do not establish illness-related OPD treatment.
        if not re.search(
            r"(?:out.patient|outpatient|\bOPD\b).{0,160}(?:consultation|treatment|illness|diagnostic)",
            raw,
            re.I,
        ):
            return "not_opd"
    return "optional, extra premium" if optional else "base"


def clauses(result, field, bundle):
    base = []
    optional = []
    unrelated = []
    for statement in (result.get("answer") or {}).get("statements", []):
        raw = text(statement)
        if field in KEYWORDS and not re.search(KEYWORDS[field], raw, re.I):
            unrelated.append(statement)
            continue
        kind = scope(statement, field, bundle)
        if kind == "base":
            base.append(statement)
        elif kind == "optional, extra premium":
            optional.append(statement)
        else:
            unrelated.append(statement)
    return base, optional, unrelated


def project(field, statements, variant):
    rules = []
    for statement in statements:
        raw = text(statement)
        main = " ".join(" ".join(c["quote"].split()) for c in statement["citations"])
        if field not in KEYWORDS or not re.search(KEYWORDS[field], main, re.I):
            continue
        if OPTIONAL.search(raw):
            continue
        citations = [
            c
            for item in [
                statement,
                *statement.get("conditions", []),
                *statement.get("restrictions", []),
            ]
            for c in item["citations"]
        ]
        citations = list(
            {
                (c["section_id"], c["page_id"], c["quote"], c.get("occurrence", 0)): c
                for c in citations
            }.values()
        )
        context = [
            c["quote"]
            for item in [*statement.get("conditions", []), *statement.get("restrictions", [])]
            for c in item["citations"]
        ]

        def add(kind, value, printed, *, raw=raw, citations=citations, context=context, **values):
            if printed not in raw:
                raise ValueError("Typed expression is not in its governing source.")
            rules.append(
                {
                    "field": field,
                    "kind": kind,
                    "value": str(value),
                    "printed": printed,
                    "variant": variant,
                    "scope": "base",
                    "citations": citations,
                    "conditions": context,
                    "condition_mode": "quoted",
                    "guards": [],
                    "supported": True,
                    **values,
                }
            )

        if field in {"entry_age", "renewal_age"}:
            if field == "renewal_age" and re.search(r"renew", raw, re.I):
                match = re.search(
                    r"life[ -]?long|life[ -]?time|no (?:upper|maximum) (?:renewal )?age limit",
                    raw,
                    re.I,
                )
                if match:
                    add("renewal", "lifetime", match[0], unit="years", maximum_unbounded=True)
            # Explicit ranges, including different printed lower/upper units.
            pattern = r"(\d+)\s*(days?|months?|years?)?\s*(?:to|and|[-–])\s*(\d+)\s*(days?|months?|years?)"
            for m in re.finditer(pattern, main, re.I):
                near = main[max(0, m.start() - 100) : m.end() + 70]
                if not re.search(r"age|aged|adult|child|entry|eligible", near, re.I):
                    continue
                low, high = int(m[1]), int(m[3])
                u1 = (m[2] or m[4]).lower().rstrip("s") + "s"
                u2 = m[4].lower().rstrip("s") + "s"
                if u1 == u2 and low > high:
                    continue
                preceding = list(
                    re.finditer(
                        r"child(?:ren)?|dependent|adult",
                        main[max(0, m.start() - 100) : m.start()],
                        re.I,
                    )
                )
                applicability = preceding[-1][0] if preceding else near
                relation = (
                    "child"
                    if re.search(r"child|dependent", applicability, re.I)
                    else "adult"
                    if re.search(r"adult", applicability, re.I)
                    else "person"
                )
                add(
                    "age",
                    f"{low}:{u1}:{high}:{u2}",
                    m[0],
                    minimum=low,
                    minimum_unit=u1,
                    maximum=high,
                    maximum_unit=u2,
                    inclusive=True,
                    relationship=relation,
                )
            lower = re.search(
                r"(?:minimum|entry) (?:entry )?age[^.]{0,65}?(\d+)\s*(days?|months?|years?)",
                main,
                re.I,
            )
            upper = re.search(
                r"maximum (?:entry )?age[^.]{0,50}?(\d+)\s*(days?|months?|years?)", main, re.I
            )
            unbounded = re.search(
                r"no (?:limit on )?maximum (?:entry )?age|no upper age limit", main, re.I
            )
            if lower and (upper or unbounded):
                low = int(lower[1])
                high = int(upper[1]) if upper else None
                add(
                    "age",
                    f"{low}:{high}",
                    lower[0],
                    minimum=low,
                    minimum_unit=lower[2].lower().rstrip("s") + "s",
                    maximum=high,
                    maximum_unit=upper[2].lower().rstrip("s") + "s" if upper else None,
                    maximum_unbounded=bool(unbounded),
                    inclusive=True,
                    relationship="child" if re.search(r"child", main, re.I) else "adult",
                )
        elif field == "sum_insured":
            if re.search(
                r"sum\s*insured\s*(?:options?|choices?|available|\()", main, re.I
            ) and not re.search(r"only (?:for|on) renewal", main, re.I):
                values = money(main)
                list_match = re.search(
                    r"((?:\d+(?:\.\d+)?\s*[/,]\s*)+\d+(?:\.\d+)?)\s*(lakhs?|lacs?)", main, re.I
                )
                if list_match:
                    values.extend(
                        (int(Decimal(n) * 100000), list_match[0])
                        for n in re.findall(r"\d+(?:\.\d+)?", list_match[1])
                    )
                # A range is not an enumerated list of selectable sums.
                if (
                    values
                    and not statement.get("table")
                    and not re.search(
                        r"(?:from|between)\s*(?:Rs\.?|INR|₹)?\s*[\d,]+.{0,20}(?:to|and)|(?:lakhs?|lacs?|crores?|(?:Rs\.?|INR|₹)\s*[\d,]+)\s+(?:to|–)\s+(?:Rs\.?|INR|₹|\d)",
                        main,
                        re.I,
                    )
                ):
                    add(
                        "choices",
                        "|".join(str(v) for v in sorted({v for v, _ in values})),
                        values[0][1],
                        choices=sorted({v for v, _ in values}),
                        unit="rupees",
                        restricted_scope=bool(
                            re.search(r"subject to|provided|only|age|room|co.pay", main, re.I)
                        ),
                        exhaustive=len(set(v for v, _ in values)) > 1
                        and not re.search(
                            r"subject to|provided|only|age|room|limit|co.pay", main, re.I
                        ),
                    )
        elif field == "coverage_basis":
            if NEGATIVE.search(main):
                continue
            values = [
                word
                for word in ("individual", "floater")
                if re.search(r"\b" + word + r"\b", main, re.I)
            ]
            if values and re.search(r"basis|available|policy|cover", main, re.I):
                add("basis", "|".join(values), re.search(r"individual|floater", main, re.I)[0])
        elif field == "plan_type":
            for pattern, value in [
                (r"super[ -]?top[ -]?up", "super_top_up"),
                (r"top[ -]?up", "top_up"),
                (r"indemnity", "medical_indemnity"),
                (r"critical illness", "critical_illness"),
                (r"fixed benefit", "fixed_benefit"),
            ]:
                match = re.search(pattern, main, re.I)
                if match:
                    add("type", value, match[0])
                    break
        elif field == "family":
            adult = re.search(r"(?:maximum(?: of)?|up to|upto)\s*(\d+)\s*adults?", main, re.I)
            child = re.search(
                r"(?:maximum(?: of)?|up to|upto|and)\s*(\d+)\s*(?:dependent )?child(?:ren)?",
                main,
                re.I,
            )
            relatives = [
                r
                for r, pattern in [
                    ("self", r"\bself\b"),
                    ("spouse", r"\bspouse\b"),
                    ("parent_in_law", r"parents?[ -]*in[ -]*laws?"),
                    ("parent", r"\bparents?\b(?![ -]*in[ -]*laws?)"),
                    ("child", r"\bchild(?:ren)?\b"),
                ]
                if re.search(pattern, main, re.I)
            ]
            if adult and child and relatives:
                add(
                    "family",
                    f"{adult[1]}A{child[1]}C",
                    adult[0],
                    maximum_adults=int(adult[1]),
                    maximum_children=int(child[1]),
                    relationships=relatives,
                    dependent_children=bool(re.search(r"dependent child", main, re.I)),
                    coverage_basis="floater" if re.search(r"floater", main, re.I) else None,
                )
        elif field in {"ped_waiting", "specified_waiting"}:
            for m in re.finditer(
                r"(?:expiry of|after|period of|for|is|:)\s*(\d+)\s*(months?|years?)", main, re.I
            ):
                if not re.search(r"wait|excluded|exclusion|continuous|coverage", main, re.I):
                    continue
                months = int(m[1]) * (12 if m[2].lower().startswith("year") else 1)
                if 0 < months <= 120:
                    add("maximum", months, m[0], unit="months")
        elif field == "copay":
            percentages = list(re.finditer(r"(\d+(?:\.\d+)?)\s*%", main))
            for m in percentages:
                near = main[max(0, m.start() - 90) : m.end() + 90]
                if re.search(r"co.pay|copay", near, re.I) and not re.search(
                    r"discount", near, re.I
                ):
                    add("maximum", m[1], m[0], unit="percent")
                    guard = re.search(
                        r"(?:age|aged)[^.]{0,70}?(\d+)\s*years?\s*(?:and above|or above|and over)",
                        main,
                        re.I,
                    )
                    if guard:
                        rules[-1]["guards"] = [
                            {
                                "field": "entry_age",
                                "operator": "gte",
                                "value": int(guard[1]),
                                "unit": "years",
                                "quote": guard[0],
                            }
                        ]
                    rules[-1]["restricted_scope"] = bool(
                        re.search(
                            r"outside|zone|non.network|voluntary|option|disease|treatment in|subject to",
                            main,
                            re.I,
                        )
                    )
        elif field == "room_limit":
            categories = [
                (r"(?:any|all) room(?:s)?(?: (?:except|excluding)[^.]{0,70})?", "any_room"),
                (r"(?:private single|single private)[^.]{0,30}room", "single_private"),
                (r"single standard[^.]{0,30}room", "single_standard"),
                (r"twin sharing", "twin_sharing"),
                (r"shared room|general (?:ward|room)", "shared"),
                (r"no limit|at actuals", "actuals"),
            ]
            for pattern, value in categories:
                match = re.search(pattern, main, re.I)
                if match:
                    add(
                        "room",
                        "any_room_except_suite"
                        if value == "any_room"
                        and re.search(r"(?:except|excluding).{0,30}suite", main, re.I)
                        else value,
                        match[0],
                    )
                    break
            percent = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(?:the )?sum\s*insured", main, re.I)
            if percent:
                add(
                    "room",
                    "percent_of_si",
                    percent[0],
                    percent=percent[1],
                    unit="percent_per_day" if re.search(r"per day", main, re.I) else "percent",
                )
        elif field == "no_claim_bonus":
            increment = re.search(
                r"(?:increas(?:e|es|ed)?(?: by| of)?|bonus(?: of| at)?|additional)\s*(\d+(?:\.\d+)?)\s*%",
                main,
                re.I,
            )
            cap = re.search(
                r"(?:maximum(?: of)?|up to|upto|cap(?: of)?)\s*(\d+(?:\.\d+)?)\s*%", main, re.I
            )
            if increment and (
                not cap or increment.start() < cap.start() or increment.start() > cap.end()
            ):
                add(
                    "bonus",
                    increment[1],
                    increment[0],
                    unit="percent",
                    cap_percent=cap[1] if cap else None,
                )
        elif field == "deductible":
            values = money(main)
            if re.search(r"no deductible|deductible[^.]{0,20}(?:nil|zero)", main, re.I):
                match = re.search(r"no deductible|deductible[^.]{0,20}(?:nil|zero)", main, re.I)
                add("maximum", "0", match[0], unit="rupees")
            elif len({v for v, _ in values}) == 1:
                add("maximum", values[0][0], values[0][1], unit="rupees")
        elif field in {"maternity", "newborn", "opd", "restoration", "ayush"}:
            # An exclusion only establishes contrary cover when it governs the
            # named benefit, not a neighboring disease or an optional rider.
            keyword = KEYWORDS[field]
            named = re.search(keyword, main, re.I)
            if named:
                nearby = main[max(0, named.start() - 90) : named.end() + 220]
                negative = re.search(
                    r"(?:"
                    + keyword
                    + r")(?: treatment| expenses| benefit| cover)?\s*(?:is |are |shall be |will be )?(?:not covered|not payable|not available|excluded)\b",
                    nearby,
                    re.I,
                )
                positive = (
                    POSITIVE.search(nearby) if not re.search(r"not|exclu", nearby, re.I) else None
                )
                if negative and re.search(r"until|unless|except|waiting|first \d+", nearby, re.I):
                    continue
                if negative or positive:
                    add("coverage", "not_covered" if negative else "covered", named[0])
                    amounts = money(main)
                    rules[-1]["limits_rupees"] = sorted({v for v, _ in amounts})
                    rules[-1]["waiting_months"] = [
                        int(m[1]) * (12 if m[2].lower().startswith("year") else 1)
                        for m in re.finditer(
                            r"(?:waiting period|continuous period)[^.]{0,30}?(\d+)\s*(months?|years?)",
                            raw,
                            re.I,
                        )
                    ]
                    if field == "opd" and re.search(r"only|asthma|specific|specified", main, re.I):
                        rules[-1]["restricted_scope"] = True
    unique = {}
    for rule in rules:
        key = json.dumps(rule, sort_keys=True)
        if key not in unique:
            unique[key] = rule
    return list(unique.values())
