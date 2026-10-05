"""Printed annual premiums across the open plans, lowest first; never a recommendation.

Each axis is chosen only by an exact printed label: the age band that contains
the customer's age, the sum insured printed as that amount, and the premium zone
from the insurer's own cited zone list. Anything that cannot be matched exactly
is reported as not found rather than estimated.
"""

import hashlib
import json
import re
from pathlib import Path

from .charts import load_prices
from .chat_rules import remaining_ids
from .pricing import lookup

STATES = (
    "andaman and nicobar islands",
    "andhra pradesh",
    "arunachal pradesh",
    "assam",
    "bihar",
    "chandigarh",
    "chhattisgarh",
    "dadra and nagar haveli",
    "daman and diu",
    "delhi",
    "goa",
    "gujarat",
    "haryana",
    "himachal pradesh",
    "jammu and kashmir",
    "jharkhand",
    "karnataka",
    "kerala",
    "ladakh",
    "lakshadweep",
    "madhya pradesh",
    "maharashtra",
    "manipur",
    "meghalaya",
    "mizoram",
    "nagaland",
    "odisha",
    "puducherry",
    "punjab",
    "rajasthan",
    "sikkim",
    "tamil nadu",
    "telangana",
    "tripura",
    "uttar pradesh",
    "uttarakhand",
    "west bengal",
)
ZONE_HEADER = re.compile(r"\bZone\s*[-–]?\s*([A-Z]|[0-9]{1,2}|I{1,3}|IV|V)\s*:", re.I)
COUNTRY_REST = re.compile(
    r"^(?:rest of (?:the )?(?:india|country)|all other (?:cities|areas|places|locations))\b"
)
REASONS = {
    "source_unavailable": "no premium chart in its documents",
    "invalid_chart": "its printed chart isn’t one I can match exactly yet",
    "no_exact_combination": "no printed premium for these details",
    "zone": "its printed zone list doesn’t place your city",
}


def load_chart(card, root=None):
    """The pinned premium artifact for a card, or None when none was published."""
    if card.get("pricing_artifact"):
        path = Path(card["pricing_artifact"])
    else:
        from django.conf import settings

        base = Path(root or settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
        path = base / "premiums" / (card["index_version"] + ".json")
    if not path.exists():
        return None
    chart = json.loads(path.read_text())
    if chart["index_id"] != card["index_version"]:
        raise ValueError("Price source differs from the pinned index.")
    if card.get("pricing_sha256"):
        if hashlib.sha256(path.read_bytes()).hexdigest() != card["pricing_sha256"]:
            raise ValueError("Pinned pricing artifact changed.")
    return chart


# A city printed under its wider name: New Delhi lies within Delhi.
ALIASES = {"new delhi": "delhi"}


def place(city):
    """Names the customer's place could go by, and their state when they named it."""
    text = " ".join(re.sub(r"[^a-z ]+", " ", (city or "").casefold()).split())
    state = next((s for s in STATES if re.search(rf"\b{s}\b", text)), None)
    names = [text]
    if text in ALIASES:
        names.append(ALIASES[text])
    if state and text != state:
        names.append(" ".join(text.replace(state, " ").split()))
    return [n for n in names if n], state


def zone_lists(card):
    """Every cited printed zone list on the card: (zones, citation)."""
    found, seen = [], set()

    def walk(value):
        if isinstance(value, dict):
            if isinstance(value.get("quote"), str) and len(ZONE_HEADER.findall(value["quote"])) > 1:
                key = value["quote"]
                if key not in seen:
                    seen.add(key)
                    found.append((parse_zones(key), value))
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(card)
    return found


def parse_zones(text):
    text = " ".join(text.replace("\u0007", " ").split())
    headers = list(ZONE_HEADER.finditer(text))
    zones = {}
    for i, header in enumerate(headers):
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        # "Delhi including Faridabad" or "Rest of NCR (including Meerut, …)"
        # names each listed place in this zone.
        segment = re.sub(r"\(\s*including\b([^)]*)\)", r",\1,", text[header.end() : end])
        segment = re.sub(r"\bincluding\b", ",", segment)
        entries = [
            e.strip(" .;").casefold()
            for e in re.split(r",|\band\b(?=\s+(?:rest of\s+)?[A-Z])", segment)
        ]
        zones["Zone " + header[1].upper()] = [e for e in entries if e]
    return zones


def zone_for(zones, city):
    """The single zone the printed list assigns to this city, or None."""
    names, state = place(city)
    if not names:
        return None

    def named(entry, name):
        # An entry names the place itself, not a "Rest of …" remainder.
        return not entry.startswith("rest of") and bool(
            re.fullmatch(rf"{re.escape(name)}(?: mmr)?(?: \(.*\))?", entry)
        )

    hits = set()
    for name in names:
        hits = hits or {z for z, es in zones.items() if any(named(e, name) for e in es)}
    if not hits and state:
        hits = {
            z
            for z, entries in zones.items()
            if any(named(e, state) or e.startswith("rest of " + state) for e in entries)
        }
    if not hits:
        # A country-wide remainder applies only once the state is known and
        # appears in no zone; otherwise a state remainder may apply instead.
        mentions_states = any(s in e for es in zones.values() for e in es for s in STATES)
        if state or not mentions_states:
            hits = {
                z for z, entries in zones.items() if any(COUNTRY_REST.match(e) for e in entries[:1])
            }
    return next(iter(hits)) if len(hits) == 1 else None


def amount(label):
    """A printed sum-insured label in rupees, or None when it is not one figure."""
    text = label.casefold().replace("₹", "").replace("rs.", "").replace("inr", "").strip()
    if re.fullmatch(r"[0-9][0-9,]*(?:/-)?", text):
        return int(re.sub(r"\D", "", text))
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*(lakhs?|lacs?|l|crores?|cr)", text)
    if match:
        unit = 10_000_000 if match[2].startswith("c") else 100_000
        return round(float(match[1]) * unit)
    return None


def band(label, years):
    """Whether a printed age band contains this whole-year age."""
    text = label.casefold().strip()
    match = re.fullmatch(r"(\d+)\s*(m|months?|d|days?)?\s*(?:-|–|to)\s*(\d+)(?:\s*years?)?", text)
    if match:
        low = 0 if match[2] else int(match[1])
        return low <= years <= int(match[3])
    match = re.fullmatch(r"(?:above|over|more than|>)\s*(\d+)(?:\s*years?)?", text)
    if match:
        return years > int(match[1])
    match = re.fullmatch(r"(?:up ?to|upto|below|<=)\s*(\d+)(?:\s*years?)?", text)
    if match:
        return years <= int(match[1])
    return text.isdigit() and int(text) == years


def choose(axis, options, card, person, profile, zones):
    """The one printed option for this axis, or None when it is not exact."""
    if axis == "sum_insured":
        picks = [o for o in options if amount(o) == profile.sum_insured]
    elif axis == "age":
        picks = [o for o in options if band(o, person.age)]
    elif axis == "composition":
        picks = [
            o
            for o in options
            # One adult: printed as 1A, or as the one-person "Individual" plan type.
            if re.fullmatch(
                r"1\s*a(?:dult)?(?:\s*\+\s*0\s*c(?:hild)?)?|individual", o.casefold().strip()
            )
        ]
    elif axis == "zone":
        zone = zone_for(zones, profile.city) if zones else None
        picks = [o for o in options if zone and o.casefold() == zone.casefold()]
    elif axis == "term":
        picks = [o for o in options if re.fullmatch(r"1\s*(?:year|yr)s?", o.casefold().strip())]
    elif axis == "tax_basis":
        picks = [o for o in options if re.search(r"exclud", o, re.I)]
    elif axis == "variant":
        picks = [o for o in options if o.casefold() == card["variant"].casefold()]
    elif axis == "coverage_basis":
        picks = [o for o in options if re.search(r"individual", o, re.I)]
    else:
        picks = options if len(options) == 1 else []
    return picks[0] if len(picks) == 1 else None


def plan_price(card, profile, root=None):
    """One plan's printed premium for a one-adult profile, or the reason it is absent."""
    chart = load_chart(card, root)
    if chart is None:
        return {"status": "source_unavailable"}
    status = chart.get("status") or ("parsed" if chart["prices"] else "invalid_chart")
    if status != "parsed":
        return {"status": status}
    prices, cells = load_prices(chart)
    person = profile.people[0]
    printed_zones = {p.axes["zone"].casefold() for p in prices if "zone" in p.axes}
    # Only a complete printed list (every zone the chart prices) may place a
    # city; a truncated quote could send a named town to a "Rest of" zone.
    complete = [
        (parsed, citation)
        for parsed, citation in zone_lists(card)
        if {z.casefold() for z in parsed} == printed_zones
    ]
    placed = {zone_for(parsed, profile.city) for parsed, _ in complete}
    zones, zone_citation = {}, None
    if len(placed) == 1 and None not in placed:
        zones, zone_citation = complete[0]
    # Fix the member/basis axes first so later options come from matching rows only.
    order = ["composition", "coverage_basis", "variant", "term", "tax_basis", "sum_insured", "zone"]
    axes = sorted(
        chart["required_axes"], key=lambda a: order.index(a) if a in order else len(order)
    )
    selected, unmatched, candidates = {}, [], prices
    for axis in axes:
        options = sorted({p.axes[axis] for p in candidates})
        pick = choose(axis, options, card, person, profile, zones)
        if pick is None:
            unmatched.append(axis)
            continue
        selected[axis] = pick
        candidates = [p for p in candidates if p.axes[axis] == pick]
    if unmatched:
        return {"status": "no_exact_combination", "unmatched_axes": unmatched}
    result = lookup(
        prices=prices,
        cells=cells,
        required_axes=set(chart["required_axes"]),
        selected=selected,
        published=True,
    )
    if result.status != "available":
        return {"status": result.status}
    return {
        "status": "available",
        "amount_printed": result.amount_printed,
        "amount": int(re.sub(r"\D", "", result.amount_printed)),
        "axes": selected,
        # Chart cells open from the premium chart; the zone list from the card.
        "citations": [c.model_dump(mode="json") for c in result.citations],
        "zone_citations": [zone_citation] if "zone" in selected and zone_citation else [],
    }


def label(card):
    name = card["name"]
    if not name.casefold().startswith(card["insurer"].casefold()):
        name = f"{card['insurer']} {name}"
    if card["variant"] != "Default" and card["variant"] not in card["name"]:
        name += f" ({card['variant']})"
    return name


def compare(state, cards, count=None, root=None):
    """The comparison record and its plain-language summary."""
    profile = state.profile
    people = profile.people
    if (
        len(people) != 1
        or people[0].age is None
        or people[0].age_unit != "years"
        or people[0].age < 18
    ):
        return None, (
            "I can look up printed premiums for one adult so far. For more people the price "
            "depends on how each insurer combines ages and members, which I won’t guess."
        )
    remaining = remaining_ids(state.fit_groups)
    open_cards = sorted(
        (c for c in cards if c["plan_id"] in remaining),
        key=lambda c: (c["insurer"].casefold(), c["name"].casefold(), c["variant"].casefold()),
    )
    rows, missing = [], []
    for card in open_cards:
        found = plan_price(card, profile, root)
        if found["status"] == "available":
            rows.append({"plan_id": card["plan_id"], "name": label(card), **found})
        else:
            status = "zone" if found.get("unmatched_axes") == ["zone"] else found["status"]
            missing.append(
                {
                    "plan_id": card["plan_id"],
                    "name": label(card),
                    "status": status,
                    "reason": REASONS.get(status, REASONS["no_exact_combination"]),
                }
            )
    rows.sort(key=lambda r: (r["amount"], r["name"].casefold()))
    shown = rows[:count] if count else rows
    basis = (
        f"one adult aged {people[0].age} in {profile.city}, "
        f"{rupees(profile.sum_insured)} sum insured, 1-year term, excluding tax"
    )
    record = {
        "basis": basis,
        "requested_count": count,
        "rows": shown,
        "more_priced": len(rows) - len(shown),
        "not_found": missing,
        "note": "Printed premiums only; not a recommendation or a quotation.",
    }
    if shown:
        parts = []
        for r in shown:
            text = f"{r['name']} ₹{r['amount']:,}"
            if "zone" in r["axes"]:
                text += f" ({r['axes']['zone']})"
            if profile.annual_budget:
                text += (
                    ", within your budget"
                    if r["amount"] <= profile.annual_budget
                    else ", above your budget"
                )
            parts.append(text)
        lead = f"Printed annual premiums for {basis}, lowest first: " + "; ".join(parts) + "."
        if count and len(shown) < count:
            lead += f" Only {plural(len(rows), 'plan')} of the {len(open_cards)} open to you {'has' if len(rows) == 1 else 'have'} a printed premium I could match."
        elif record["more_priced"]:
            lead += f" {plural(record['more_priced'], 'more plan')} also {'has' if record['more_priced'] == 1 else 'have'} a printed premium."
        lead += " This is the printed premium only, not a recommendation; the insurer’s quote decides the final amount."
    else:
        lead = (
            f"I couldn’t find a printed annual premium for {basis} in any of the "
            f"{plural(len(open_cards), 'plan')} open to you."
        )
    groups = {}
    for m in missing:
        groups.setdefault(m["reason"], []).append(m["name"])
    if groups and shown:
        lead += f" No printed premium for the other {len(missing)}:"
    for reason, names in groups.items():
        lead += f" {reason[0].upper() + reason[1:]} — " + "; ".join(names) + "."
    if "zone" in groups and not place(profile.city)[1]:
        lead += " Telling me your state too (for example “Kota, Rajasthan”) may let me place it."
    return record, lead


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def rupees(value):
    if value >= 10_000_000:
        return f"₹{value / 10_000_000:g} crore"
    return f"₹{value / 100_000:g} lakh"
