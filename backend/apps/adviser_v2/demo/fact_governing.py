"""Bound card projections to operative clauses, complete lists and named axes."""

import re

from .quotations import locate, normalized

HEADINGS = {
    "entry_age": r"(?:Eligibility|Entry\s*age)",
    "ped_waiting": r"(?:Pre[ -]?Existing Diseases?[^\n]{0,80}|[^\n]{0,80}Excl\s*0?1\b[^\n]*)",
    "specified_waiting": r"(?:(?:Specific|Specified)[^\n]{0,80}(?:waiting|disease)[^\n]*|[^\n]{0,80}Excl\s*0?2\b[^\n]*)",
    "maternity": r"Maternity[^\n]*",
    "sum_insured": r"(?:Base )?Sum\s*Insured\s*(?:Options|Choices)[^\n]*",
    "room_limit": r"Room\s*(?:rent|boarding|accommodation)[^\n]*",
    "renewal_age": r"(?:Renewal|Renewability)[^\n]*",
    "deductible": r"(?:Aggregate )?Deductible[^\n]*",
    "no_claim_bonus": r"(?:Cumulative|No[ -]?claim)\s*Bonus[^\n]*",
}


def clip(cite, raw, start, end, bundle):
    selected = raw[start:end].strip()
    if selected == raw:
        return cite
    section = next(s for s in bundle["sections"] if s["id"] == cite["section_id"])
    segment = next(s for s in section["segments"] if s["page_id"] == cite["page_id"])
    origin, _ = locate(segment["text"], raw, cite.get("occurrence", 0))
    target = origin + start + normalized(raw[start:end])[1][0]
    occurrence = 0
    while locate(segment["text"], selected, occurrence)[0] != target:
        occurrence += 1
    return {**cite, "quote": selected, "occurrence": occurrence}


def governing(statement, field, bundle):
    if statement.get("table"):
        return statement
    from .card_clauses import without_boilerplate

    citations = []
    for cite in statement["citations"]:
        raw = cite["quote"]
        if field == "coverage_basis":
            headers = list(
                re.finditer(
                    r"Sum\s*Insured\s*on\s*(?:Individual|Floater)\s*Basis:\s*Limit[^\n]*(?:\nprocedure)?",
                    raw,
                    re.I,
                )
            )
            if len(headers) >= 2:
                for header in headers:
                    end = header.end()
                    currency = re.search(r"\s+Rs\.", raw[header.start() : end])
                    if currency:
                        end = header.start() + currency.end()
                    citations.append(clip(cite, raw, header.start(), end, bundle))
                continue
        pattern = HEADINGS.get(field)
        found = (
            re.search(r"(?mi)^[ \t]*(?:(\d+(?:\.\d+)*\.?)[ \t]+)?" + pattern, raw)
            if pattern
            else None
        )
        start, end = 0, len(raw)
        if found:
            start = found.start()
            number = (found[1] or "").rstrip(".")
            # A peer numbered heading ends this clause; nested list items do not.
            if number:
                depth = number.count(".")
                for candidate in re.finditer(
                    r"(?m)^[ \t]*(\d+(?:\.\d+)*\.?)\s+[A-Z][^\n]{0,100}", raw[found.end() :]
                ):
                    other = candidate[1].rstrip(".")
                    if other.count(".") == depth and other != number:
                        end = found.end() + candidate.start()
                        break
        # Do not expose unrelated addresses/preceding clauses as field quotes.
        for left, right in without_boilerplate(raw, start, end):
            citations.append(clip(cite, raw, left, right, bundle))
    return {
        **statement,
        "citations": citations,
        "text": "\n\n".join(c["quote"] for c in citations),
        "excerpts": [c["quote"] for c in citations],
    }


def operative_basis(statement):
    raw = " ".join(c["quote"] for c in statement["citations"])
    if re.search(r"coverage opted", raw, re.I) and re.search(
        r"premium|discount|single point", raw, re.I
    ):
        return False
    if statement.get("table") or re.search(
        r"illustrat|example|scenario|assum|not available|not offered|neither|except|excluding",
        raw,
        re.I,
    ):
        return False
    if re.search(r"Sum\s*Insured\s*on\s*Individual\s*Basis", raw, re.I) and re.search(
        r"Sum\s*Insured\s*on\s*Floater\s*Basis", raw, re.I
    ):
        return True
    return bool(
        re.search(
            r"(?:available|offered|issued|taken|opted|cover(?:age|ed)?|policy).{0,110}(?:individual|floater).{0,75}basis",
            raw,
            re.I | re.S,
        )
    )


def variant_proven(statement, bundle):
    """A shared benefit needs the actual selected column, not shared prose."""
    if statement.get("variant_axis_verified"):
        return True
    variants = bundle.get("variants", [])
    if len(variants) < 2:
        return True
    table = statement.get("table")
    if not table:
        raw = " ".join(c["quote"] for c in statement["citations"])
        return bool(
            re.search(
                r"(?:applicable|available|covered) (?:under|for|to) all (?:plans|variants)",
                raw,
                re.I,
            )
        )
    region = next((t for t in bundle.get("tables", []) if t["id"] == table["region_id"]), None)
    if not region:
        return False
    selected = normalized(bundle.get("variant", "Default"))[0].casefold()
    labels = [region["cells"].get(k) for k in table["column_label_ids"]]
    value = region["cells"].get(table["value_cell_id"])
    rows = [region["cells"].get(k) for k in table["row_label_ids"]]
    if (
        not value
        or not rows
        or any(not r or r["row"] != value["row"] or r["column"] >= value["column"] for r in rows)
    ):
        return False
    return any(
        c
        and c["column"] == value["column"]
        and c["row"] < value["row"]
        and normalized(c["text"])[0].casefold() == selected
        for c in labels
    )
