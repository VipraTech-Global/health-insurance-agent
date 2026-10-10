"""Bound card projections to operative clauses, complete lists and named axes."""

import re

from .quotations import locate, normalized
from .table_cells import aligned

HEADINGS = {
    "entry_age": r"(?:Eligibility|Entry\s*age)",
    "ped_waiting": r"(?:Pre[ -]?Existing Diseases?[^\n]{0,80}|[^\n]{0,80}Excl\s*0?1\b[^\n]*)",
    "specified_waiting": r"(?:(?:Specific|Specified)[^\n]{0,80}(?:waiting|disease)[^\n]*|[^\n]{0,80}Excl\s*0?2\b[^\n]*)",
    "maternity": r"Maternity[^\n]*",
    "sum_insured": r"(?:Base )?Sum\s*Insured\s*(?:Options?|Choices|\(SI\))[^\n]*",
    "geography": r"(?:Zonal pricing|Premium (?:Tier|Zones)|Zone wise premium)[^\n]*",
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
            illustration = re.search(r"Benefit Illustration", raw, re.I)
            if illustration and illustration.start() > 0:
                raw_end = illustration.start()
                cite = clip(cite, raw, 0, raw_end, bundle)
                raw = cite["quote"]
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
            re.search(r"(?mi)^[ \t]*(?:((?:[A-Z]\.)?\d+(?:\.\d+)*\.?)[ \t]+)?" + pattern, raw)
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
                    r"(?m)^[ \t]*((?:[A-Z]\.)?\d+(?:\.\d+)*\.?)\s+[A-Z][^\n]{0,100}",
                    raw[found.end() :],
                ):
                    other = candidate[1].rstrip(".")
                    if other.count(".") == depth and other != number:
                        end = found.end() + candidate.start()
                        break
        if field in {"entry_age", "coverage_basis", "sum_insured", "family"}:
            starts = {
                "entry_age": r"(?mi)^.*?(?:Min/Max Entry Age|Entry Age [–:-] Minimum|Eligibility)",
                "coverage_basis": r"(?mi)^Policy Type\b",
                "sum_insured": r"(?mi)^Sum Insured (?:option|Options|\(SI\))",
                "family": r"(?mi)^Family Floater policy[-:]",
            }
            selected = re.search(starts[field], raw)
            if selected:
                start = selected.start()
                terminator = {
                    "entry_age": r"(?mi)^(?:Sum Insured option|Exit Age|Policy Term)",
                    "coverage_basis": r"(?mi)^Policy Term",
                    "sum_insured": r"(?mi)^(?:Policy Type|Zone wise premium|S\. No\.)",
                    "family": r"(?mi)^(?:Policy Renewal|[➢•])",
                }
                following = re.search(terminator[field], raw[selected.end() :])
                if following:
                    end = selected.end() + following.start()
        if field == "sum_insured":
            following = re.search(r"(?mi)^Zone wise premium", raw[start:end])
            if following:
                end = start + following.start()
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
    from .fact_fit_projection import basis_match

    return basis_match(" ".join(raw.split())) is not None


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
    if not value or not rows or any(not r or not aligned(r, value, "row") for r in rows):
        return False
    return any(
        c and aligned(c, value, "column") and normalized(c["text"])[0].casefold() == selected
        for c in labels
    )
