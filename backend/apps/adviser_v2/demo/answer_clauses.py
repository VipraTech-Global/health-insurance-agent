"""Answer governing boundaries without crossing an identified heading.

Offsets refer to the original source; no normalized wording is displayed.
"""

import re
from bisect import bisect_left, bisect_right
from functools import lru_cache

from .quotations import boundaries_for

BOILERPLATE = re.compile(
    r"(?im)^[^\n]*(?:REGISTERED\s*(?:&|AND)?\s*CORPORATE OFFICE|CORPORATE OFFICE:|REGISTERED OFFICE:|UIN\s*:|CIN\s*:|IRDAI\s+REG|STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED\s*\|)[^\n]*(?:\n|$)|^\s*Page\s+\d+\s+of\s+\d+\s*(?:\n|$)"
)
QUALIFIER = re.compile(
    r"\s*(?:subject to|provided|however|except|excluding|only|unless|note|notwithstanding|no |not |this .*?not )",
    re.I,
)


@lru_cache(maxsize=64)
def indexed(text):
    boundaries, headings = boundaries_for(text)
    headings = set(headings)
    headings.update(
        m.start()
        for m in re.finditer(
            r"(?m)^\s*(?:[A-Z]\.[ \t\x07]+[A-Z][^\n]{0,90}:|\d+\.[ \t\x07]*\n?[ \t\x07]*[A-Z][^\n]{0,90}:)",
            text,
        )
    )
    # CIS benefit headings often use a bullet and sentence case, rather than
    # title case. Do not pull a preceding illness list into the new benefit.
    headings.update(
        m.start()
        for m in re.finditer(r"(?m)^[ \t]*[•➢][ \t]+[A-Z][A-Za-z /-]{2,70}[ \t]*$", text)
        if not re.search(r"\b(?:if|unless|only|not|except|subject|provided)\b", m[0], re.I)
    )
    headings.update(
        m.start()
        for m in re.finditer(
            r"(?mi)^[ \t]*(?:(?:\d+|[ivx]+)[.)][ \t\x07]*)?(?:Sub[ -]?limits|Pre[ -]?existing diseases|Co[ -]?payment|Deductible|Room (?:category|eligibility|rent criteria))(?:[ \t]*:?[^\n]{0,70})?$",
            text,
        )
    )
    boilerplate = list(BOILERPLATE.finditer(text))
    edges = {p for m in boilerplate for p in (m.start(), m.end())}
    return (
        sorted(set(boundaries) | headings | edges),
        headings,
        [(m.start(), m.end()) for m in boilerplate],
    )


def clause_bounds(text, start, end):
    boundaries, headings, _ = indexed(text)
    left = boundaries[max(0, bisect_right(boundaries, start) - 1)]
    right = boundaries[min(len(boundaries) - 1, bisect_left(boundaries, end))]
    # A heading starts a new governing unit. A preceding note or a colon in a
    # previous benefit must never drag its table/footer into this one.
    before = boundaries[max(0, bisect_left(boundaries, left) - 1)]
    if left not in headings and QUALIFIER.match(text[before:left]):
        left = before
    governing = max((p for p in headings if p <= start), default=0)
    prefix = text[left:start]
    if left not in headings and re.search(r"(?:^|\n)\s*(?:\(?[a-zivx]+[.)]|[•*-])\s", prefix, re.I):
        intro = text.rfind(":", max(governing, left - 2000), start)
        if intro >= 0:
            left = max(governing, boundaries[max(0, bisect_right(boundaries, intro) - 1)])
    while right < len(text) and right not in headings:
        after = boundaries[min(len(boundaries) - 1, bisect_right(boundaries, right))]
        following = text[right:after]
        if not (
            QUALIFIER.match(following)
            or re.match(r"\s*(?:\(?[a-zivx]+[.)]\s|[•*])", following, re.I)
            or re.search(
                r"\b(?:subject to|provided|with regard|will|shall|must|required|only|except|excluded|condition|limit)\b",
                following,
                re.I,
            )
        ):
            break
        right = after
    return left, right


def without_boilerplate(text, start, end):
    """Return original, disjoint spans; do not stitch removed text into prose."""
    cursor = start
    for a, b in indexed(text)[2]:
        if b <= cursor or a >= end:
            continue
        if a > cursor and text[cursor:a].strip():
            yield cursor, a
        cursor = max(cursor, b)
    if cursor < end and text[cursor:end].strip():
        yield cursor, end
