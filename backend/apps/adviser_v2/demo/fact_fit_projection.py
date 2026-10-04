"""Bounded projections for purchase eligibility and operative base benefits."""

import re


def raw_text(statement):
    return " ".join(" ".join(c["quote"].split()) for c in statement["citations"])


def rule_for(statement, field, kind, value, variant, printed, **extra):
    context = [*statement.get("conditions", []), *statement.get("restrictions", [])]
    return {
        "field": field,
        "kind": kind,
        "value": value,
        "variant": variant,
        "printed": printed,
        "scope": "base",
        "supported": True,
        "citations": [c for item in [statement, *context] for c in item["citations"]],
        "conditions": [item["text"] for item in context],
        "condition_mode": "quoted",
        "guards": [],
        **extra,
    }


def outpatient_exclusion(statement):
    raw = raw_text(statement)
    return bool(
        re.search(
            r"(?:exclusions?|will not pay|not payable|not liable)[\s\S]{0,550}out[ -]?patient",
            raw,
            re.I,
        )
    ) and not bool(re.search(r"We (?:will|shall) cover", raw, re.I))


def optional_unit(statement, field):
    if field == "opd" and outpatient_exclusion(statement):
        return False
    raw = raw_text(statement)
    conditions = " ".join(
        raw_text(s) for s in [*statement.get("conditions", []), *statement.get("restrictions", [])]
    )
    return bool(
        re.search(r"this optional (?:cover|benefit)|this (?:add[ -]?on|rider)", conditions, re.I)
        or (field == "room_limit" and re.search(r"Room Modifier|option to modify", raw, re.I))
        or (field == "copay" and re.search(r"Co[ -]?Payment\s+\d+%\s*,\s*\d+%", raw, re.I))
    )


def purchase_geography(statement, variant):
    raw = raw_text(statement)
    direct = re.search(
        r"(?:available|offered|sold).{0,65}(?:throughout India|across India|all India)|(?:residents?|residing|resident Indians).{0,35}in India|Indian (?:nationals|residents).{0,50}(?:residing in India|eligible)",
        raw,
        re.I,
    )
    premium = re.search(
        r"(?:premium (?:payment |computation )?(?:zones?|tier)|zone.{0,20}premium|premium.{0,60}zone|zonal pricing|pricing zone)",
        raw,
        re.I,
    )
    nationwide = re.search(
        r"rest of (?:the )?India|rest of (?:the )?country|all (?:over )?India", raw, re.I
    )
    restriction = re.search(
        r"(?:sold|available|purchase|eligible).{0,40}only (?:in|for residents of)", raw, re.I
    )
    country_scheme = re.search(
        r"(?:country|India) has been divided into the following (\d+) zones", raw, re.I
    )
    complete_scheme = bool(country_scheme) and all(
        re.search(r"\bZone " + str(n) + r"\s*:", raw, re.I)
        for n in range(1, int(country_scheme[1]) + 1)
    )
    if restriction or not (direct or (premium and (nationwide or complete_scheme))):
        return []
    # Premium geography is usable only as an explicit exhaustive nationwide
    # sales/pricing scheme, never from a treatment-territory clause alone.
    return [
        rule_for(
            statement,
            "geography",
            "geography",
            "india",
            variant,
            raw,
            geography_basis="residence" if direct else "nationwide_premium_zones",
        )
    ]


def base_coverage(statement, field, variant):
    from .fact_rules_v6 import KEYWORDS

    raw = raw_text(statement)
    keyword = KEYWORDS[field]
    named = re.search(keyword, raw, re.I)
    if not named:
        return []
    positive = re.search(
        r"(?:We (?:will|shall) (?:cover|pay|reimburse|indemnify)[^.]{0,160}(?:"
        + keyword
        + r")|(?:"
        + keyword
        + r")[^.]{0,650}(?:is |are |shall be |will be )?(?:covered|payable|reimbursed))",
        raw,
        re.I,
    )
    negative = re.search(
        r"(?:not (?:cover|pay)|exclude(?:d|s)?|exclusions?)[^.]{0,120}(?:"
        + keyword
        + r")|(?:"
        + keyword
        + r")[^.]{0,100}(?:not covered|not payable|not available|excluded)",
        raw,
        re.I,
    )
    # An exclusion heading must govern the named outpatient row. Merely
    # mentioning an excluded complication in a positive benefit is not enough.
    if positive and re.search(r"\bnot\s+(?:covered|payable|reimbursed)", positive[0], re.I):
        positive = None
    if field == "opd" and outpatient_exclusion(statement):
        return [rule_for(statement, field, "coverage", "not_covered", variant, raw)]
    if positive:
        value, printed = "covered", positive[0]
    elif negative:
        value, printed = "not_covered", negative[0]
    else:
        return []
    context = " ".join(
        [
            raw,
            *[raw_text(s) for s in statement.get("conditions", [])],
            *[raw_text(s) for s in statement.get("restrictions", [])],
        ]
    )
    waits = sorted(
        {
            int(m[1]) * (12 if m[2].lower().startswith("year") else 1)
            for m in re.finditer(
                r"(?:waiting period|continuous (?:coverage|period)|covered continuously)[^.]{0,70}?(\d+)\s*(months?|years?)",
                context,
                re.I,
            )
        }
    )
    if value == "not_covered" and (waits or re.search(r"until|first \d+", printed, re.I)):
        return []
    return [rule_for(statement, field, "coverage", value, variant, printed, waiting_months=waits)]


# The proposer is the customer; "Proposer’s Spouse" names someone else.
SELF = r"\bself\b|\bInsured;|\bYou and your immediate family|\bProposer\b(?!\s*[’']s)"
WORD_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}
# A printed count: digits, or a number word bound to the noun it counts.
COUNT = r"(\d+|" + "|".join(WORD_NUMBERS) + r")"


def count(text):
    return int(text) if text.isdigit() else WORD_NUMBERS[text.casefold()]


def family_rule(statement, variant):
    raw = raw_text(statement)
    # "The entire family under a Single Sum Insured" is a floater in other words.
    if not re.search(r"floater|family under a single sum insured", raw, re.I) or re.search(
        r"illustrat|example|coverage opted|multi.individual", raw, re.I
    ):
        return []
    adult = re.search(r"(?:maximum.{0,65}|up to\s*|upto\s*)" + COUNT + r"\s*adults?", raw, re.I)
    child = re.search(
        r"(?:\+|and|up to|upto|maximum(?: of)?)\s*" + COUNT + r"\s*(?:dependent )?child", raw, re.I
    ) or re.search(
        r"\bchild(?:ren)?\s*(?:\([^)]*\)\s*)?not exceeding\s*" + COUNT + r"\b", raw, re.I
    )
    members = re.search(r"(?:up\s*to|maximum(?: of)?)\s*" + COUNT + r"\s*members", raw, re.I)
    compact = re.search(r"[Ff]loater[^.]{0,70}?(\d+)\s*A\s*\+?\s*(\d+)\s*C", raw)
    if compact:
        adult_count, child_count = int(compact[1]), int(compact[2])
    else:
        adult_count = count(adult[1]) if adult else None
        child_count = count(child[1]) if child else None
    relatives = [
        name
        for name, pattern in [
            ("self", SELF),
            ("spouse", r"\bspouse\b"),
            ("child", r"\bchild|\bson\b|\bdaughter\b"),
            ("parent", r"\bparents?\b(?![ -]*in[ -]*law)"),
            ("parent_in_law", r"parents?[ -]*in[ -]*laws?"),
        ]
        if re.search(pattern, raw, re.I)
    ]
    if not relatives or (not adult and not members and not {"self", "spouse"} <= set(relatives)):
        return []
    relative_limits = {}
    for relation, pattern in [
        ("parent", r"(?:up to|upto)\s*" + COUNT + r"\s*parents?\b(?![ -]*in)"),
        ("parent_in_law", r"(?:up to|upto)\s*" + COUNT + r"\s*parents?[ -]*in[ -]*laws?"),
    ]:
        match = re.search(pattern, raw, re.I)
        if match:
            relative_limits[relation] = count(match[1])
    member_count = count(members[1]) if members else None
    value = f"{adult_count}A{child_count}C:{member_count or '-'}M:" + "|".join(relatives)
    return [
        rule_for(
            statement,
            "family",
            "family",
            variant=variant,
            value=value,
            printed=raw,
            relationship_limits=relative_limits,
            maximum_adults=adult_count,
            maximum_members=member_count,
            maximum_children=child_count,
            relationships=relatives,
            dependent_children=bool(re.search(r"dependent child", raw, re.I)),
            coverage_basis="floater",
        )
    ]


def basis_match(raw):
    patterns = [
        r"Sum\s*Insured\s*on\s*Individual\s*Basis.*Sum\s*Insured\s*on\s*Floater\s*Basis",
        r"(?:Coverage Options|Cover Type|Type of Policy|Policy Type)[^.]{0,160}(?:individual|floater)[^.]{0,100}",
        r"Individual (?:and|/) (?:Family )?Floater Policy",
        r"(?:can be issued|issued|available|offered).{0,70}individual.{0,180}family floater",
        r"Individual (?:Policies|Sum Insured).{0,260}(?:Family )?Floater (?:policies|Sum Insured).{0,100}",
        r"(?:available|offered|issued|taken|opted|cover(?:age|ed)?|policy).{0,110}(?:individual|floater).{0,75}basis",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw, re.I | re.S)
        if match:
            return match
    return None


def optional_table(statement, bundle):
    table = statement.get("table")
    if not table:
        return False
    region = next((t for t in bundle.get("tables", []) if t["id"] == table["region_id"]), None)
    if not region:
        return False
    value = region["cells"].get(table["value_cell_id"])
    if not value:
        return False
    headings = sorted(
        (c["row"], c["text"])
        for c in region["cells"].values()
        if c["row"] < value["row"]
        and re.fullmatch(r"(?:Optional|Base|Standard) (?:Benefits|Covers)", c["text"].strip(), re.I)
    )
    return bool(headings and headings[-1][1].lower().startswith("optional"))
