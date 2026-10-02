"""Exact quantity normalization shared by the six demo checks."""

import re
from decimal import Decimal

_NUMBER = r"(?:\d[\d,]*(?:\.\d+)?|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)"
_WORDS = dict(
    zip(
        "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety".split(),
        (*range(21), 30, 40, 50, 60, 70, 80, 90),
        strict=True,
    )
)


def _decimal(value: str) -> Decimal:
    return Decimal(_WORDS[value] if value in _WORDS else value.replace(",", ""))


def normalized_quantity(value: str, unit: str) -> Decimal:
    """Equivalent printed scalar formats, never arbitrary expressions or formulas."""
    value = value.replace(",", "").strip().casefold()
    if unit == "money":
        value = re.sub(r"^(?:rs\.?|inr|₹)\s*", "", value).removesuffix("/-").strip()
    if unit == "ratio":
        if value.endswith("%"):
            return _decimal(value[:-1].strip()) / 100
        if re.fullmatch(r"\d+(?:\.\d+)?/\d+(?:\.\d+)?", value):
            numerator, denominator = value.split("/")
            return Decimal(numerator) / Decimal(denominator)
    return _decimal(value)


def quoted_quantities(quote: str) -> dict[str, set[Decimal]]:
    """Normalize printed units without changing a quotation or inventing conversions."""
    text = " ".join(quote.casefold().split())
    # Normalize an explicitly printed scale before collecting numbers, so
    # "Rupees Fifty thousand" supports 50000 rather than an unscaled 50.
    scales = {"hundred": 100, "thousand": 1000, "lakh": 100000, "lac": 100000, "crore": 10000000}
    text = re.sub(rf"(?<!\w)({_NUMBER})\s*(hundred|thousand|lakh|lac|crore)s?\b",
        lambda match: str(_decimal(match[1]) * scales[match[2]]), text)
    quantities: dict[str, set[Decimal]] = {
        unit: set() for unit in ("money", "ratio", "day", "month", "year", "hour", "count")
    }
    numbers = {_decimal(match.group()) for match in re.finditer(rf"(?<!\w){_NUMBER}(?!\w)", text)}
    for match in re.finditer(r"(?<!\w)(\d[\d,]*(?:\.\d+)?)\s*/-", text):
        quantities["money"].add(_decimal(match[1]))
    if re.search(r"\brs\.?|\brupees\b|\binr\b|₹", text):
        quantities["money"].update(numbers)
        for match in re.finditer(rf"({_NUMBER})\s*(lakh|lac|crore)s?\b", text):
            quantities["money"].add(
                _decimal(match[1]) * (10000000 if match[2] == "crore" else 100000)
            )
    for match in re.finditer(rf"({_NUMBER})\s*(?:%|percent|per cent)", text):
        quantities["ratio"].add(_decimal(match[1]) / 100)
    for unit in ("day", "month", "year", "hour"):
        for match in re.finditer(rf"\b{unit}\s*({_NUMBER})(?!\w)", text):
            quantities[unit].add(_decimal(match[1]))
        for match in re.finditer(
            rf"({_NUMBER})(?:\s*(?:-|–|to|and)\s*({_NUMBER}))?(?:st|nd|rd|th)?\s*{unit}s?\b", text
        ):
            quantities[unit].add(_decimal(match[1]))
            if match[2]:
                quantities[unit].add(_decimal(match[2]))
    quantities["month"].update(value * 12 for value in quantities["year"])
    quantities["year"].update(value / 12 for value in quantities["month"])
    for match in re.finditer(
        rf"({_NUMBER})\s*(?:(?:dependent|insured|dependent insured|in[- ]?patient)\s+)?(?:times?|occasions?|claims?|children|adults?|members?|deliveries|delivery|beds?)\b",
        text,
    ):
        quantities["count"].add(_decimal(match[1]))
    for word, number in (("once", 1), ("twice", 2), ("thrice", 3)):
        if re.search(rf"\b{word}\b", text):
            quantities["count"].add(Decimal(number))
    for match in re.finditer(rf"({_NUMBER})\s+in number\b|family size of\s+({_NUMBER})\s*a\b", text):
        quantities["count"].add(_decimal(match[1] or match[2]))
    # Printed plan-composition cells use abbreviations whose meaning must also
    # be quoted. For separate quotes, the fact validator combines them only
    # inside an explicitly checked same-page table region.
    for abbreviation, label in (("a", "adult"), ("c", "child")):
        if re.search(rf"\b{abbreviation}\s*[-–=:]\s*{label}\b", text):
            for match in re.finditer(rf"(?<!\w)(\d+)\s*{abbreviation}\b", text):
                quantities["count"].add(Decimal(match[1]))
    if re.search(r"\b(?:nil|zero|not applicable)\b|\bno\s+(?:co-?payment|deductible)\b", text):
        quantities["ratio"].add(Decimal(0))
        quantities["money"].add(Decimal(0))
    return quantities

