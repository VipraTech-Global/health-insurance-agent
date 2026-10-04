"""Execute cited bounded rules against incomplete customer details."""

import re


def eligible_rules(card, field):
    return [
        r
        for r in card.get("executable_rules", [])
        if r["field"] == field
        and r.get("citations")
        and r.get("scope", "base") == "base"
        and r.get("supported", True)
        and not r.get("restricted_scope")
        and r.get("variant") in (None, card["variant"])
    ]


def guard_applies(rule, profile, person_id=None):
    if rule.get("restricted_scope"):
        return False
    if not rule.get("guards"):
        return True
    if profile is None:
        return False
    people = [p for p in profile.people if person_id is None or p.id == person_id]
    for guard in rule["guards"]:
        if guard["field"] != "entry_age" or guard["unit"] != "years" or guard["operator"] != "gte":
            return False
        if not any(
            p.age is not None and p.age_unit == "years" and p.age >= guard["value"] for p in people
        ):
            return False
    return True


def age_result(person, rule):
    if person.age is None:
        return "unresolved"

    # Compare completed years or months without approximating a month as days.
    def interval(value, unit):
        if unit == "years":
            return value * 12, (value + 1) * 12, "months"
        if unit == "months":
            return value, value + 1, "months"
        return value, value + 1, "days"

    lower, upper, dimension = interval(person.age, person.age_unit)
    minimum, _, low_dimension = interval(rule["minimum"], rule["minimum_unit"])
    if dimension != low_dimension:
        # A known whole-year age safely clears a short infant-day minimum; do
        # not invent exact day counts near a calendar boundary.
        if dimension == "months" and low_dimension == "days" and lower >= 12 and minimum <= 365:
            minimum = 0
        else:
            return "unresolved"
    if upper <= minimum:
        return "doesnt_fit"
    if lower < minimum:
        return "unresolved"
    if rule.get("maximum_unbounded"):
        return "fits"
    _, maximum, high_dimension = interval(rule["maximum"], rule["maximum_unit"])
    if high_dimension != dimension:
        return "unresolved"
    if lower >= maximum:
        return "doesnt_fit"
    return "fits" if upper <= maximum else "unresolved"


def hard_limits(card, profile, existing):
    reasons = {r["field"]: r for r in existing}
    # Immutable typed cards must not fall back to superseded legacy projections.
    # A quoted field with no executable rule cannot supply an exclusion.
    for field in ("family", "sum_insured", "plan_type", "coverage_basis", "geography"):
        if field == "sum_insured" and profile.sum_insured is None:
            # No requested amount: there is nothing to check, so it is no gap.
            reasons.pop(field, None)
        elif field in reasons:
            reasons[field] = {
                "field": field,
                "status": "unresolved",
                "explanation": "Applicable executable evidence has not been established.",
                "citations": [],
            }

    def record(field, status, explanation, rules):
        reasons[field] = {
            "field": field,
            "status": status,
            "explanation": explanation,
            "citations": [q for r in rules for q in r["citations"]],
        }

    rules = eligible_rules(card, "geography")
    if rules and profile.city:
        # Explicit Indian location labels; never assume that any arbitrary city
        # is Indian just because the insurer offers an India-wide product.
        city = profile.city.casefold().strip()
        indian_city = city in {
            "pune",
            "mumbai",
            "delhi",
            "new delhi",
            "bengaluru",
            "bangalore",
            "chennai",
            "kolkata",
            "hyderabad",
            "ahmedabad",
            "surat",
            "nashik",
            "jaipur",
            "lucknow",
            "kochi",
            "ernakulam",
            "thiruvananthapuram",
        } or bool(re.search(r"[, ]india$", city))
        # Or the customer answered "Which city in India do you live in?".
        indian_city = indian_city or getattr(profile, "resides_in_india", False)
        if all(r["value"] == "india" for r in rules) and indian_city:
            record(
                "geography",
                "fits",
                "The cited purchase/residential geography covers India; premium zones do not restrict sale in this Indian city.",
                rules,
            )
    for person in profile.people:
        rules = [
            r
            for r in eligible_rules(card, "entry_age")
            if r["kind"] == "age"
            and (
                r.get("relationship") == "child"
                if person.relationship == "child"
                else r.get("relationship") in {"adult", "person", person.relationship}
            )
        ]
        values = {age_result(person, r) for r in rules}
        status = next(iter(values)) if len(values) == 1 else "unresolved"
        record(
            "entry_age:" + person.id,
            status,
            "Entry age checked against the printed inclusive range; other conditions remain quoted.",
            rules,
        )
    rules = eligible_rules(card, "plan_type")
    if rules and len({r["value"] for r in rules}) == 1 and profile.plan_type != "unresolved":
        record(
            "plan_type",
            "fits" if rules[0]["value"] == profile.plan_type else "doesnt_fit",
            "Requested product type checked against the cited description.",
            rules,
        )
    rules = eligible_rules(card, "coverage_basis")
    if profile.coverage_basis:
        status = (
            (
                "fits"
                if profile.coverage_basis in rules[0]["value"].split("|")
                else "doesnt_fit"
                if rules[0].get("exhaustive")
                else "unresolved"
            )
            if len(rules) == 1
            else "unresolved"
        )
        record(
            "coverage_basis",
            status,
            "Requested coverage basis checked against the cited coverage_basis rule."
            if rules
            else "No applicable executable coverage_basis rule has been established.",
            rules,
        )
    rules = eligible_rules(card, "sum_insured")
    if rules and profile.sum_insured is not None:
        supported = any(profile.sum_insured in r["choices"] for r in rules)
        contradicted = any(
            r.get("exhaustive") and profile.sum_insured not in r["choices"] for r in rules
        )
        status = (
            "unresolved"
            if supported and contradicted
            else "fits"
            if supported
            else "doesnt_fit"
            if contradicted
            else "unresolved"
        )
        record(
            "sum_insured",
            status,
            "Requested sum insured checked against the printed selectable choices.",
            rules,
        )
    rules = [
        r
        for r in eligible_rules(card, "family")
        if not r.get("coverage_basis")
        or r["coverage_basis"] == profile.coverage_basis
        or (r["coverage_basis"] == "floater" and profile.coverage_basis is None)
    ]
    # With no stated basis a floater limit can confirm the family fits one shared
    # cover, but cannot exclude a family that may buy separate cover instead.
    provisional = profile.coverage_basis is None and any(
        r.get("coverage_basis") == "floater" for r in rules
    )
    if rules:
        outcomes = set()
        for rule in rules:
            children = [p for p in profile.people if p.relationship == "child"]
            invalid = (
                (
                    rule.get("maximum_children") is not None
                    and len(children) > rule["maximum_children"]
                )
                or (
                    rule.get("maximum_adults") is not None
                    and len(profile.people) - len(children) > rule["maximum_adults"]
                )
                or (
                    rule.get("maximum_members") is not None
                    and len(profile.people) > rule["maximum_members"]
                )
            )
            invalid |= bool(
                rule.get("dependent_children") and any(p.dependent is False for p in children)
            )
            unknown_relationship = any(
                p.relationship not in rule["relationships"] for p in profile.people
            )
            invalid |= unknown_relationship and bool(rule.get("exhaustive"))
            incomplete = (unknown_relationship and not rule.get("exhaustive")) or bool(
                rule.get("dependent_children") and any(p.dependent is None for p in children)
            )
            if rule.get("primary_spouse_pair_only"):
                adult_roles = sorted(
                    p.relationship for p in profile.people if p.relationship != "child"
                )
                if adult_roles not in (["self"], ["self", "spouse"]):
                    # Parent relationships are relative to the customer, not
                    # necessarily the primary insured. Do not infer their pairing.
                    incomplete = True
            if rule.get("maximum_children") is None and len(children) > 1:
                incomplete = True
            if rule.get("maximum_adults") is None and rule.get("maximum_members") is None:
                # A named Self/Spouse combination is bounded by those singular
                # roles; extended family needs its own printed multiplicity.
                for relation in {
                    p.relationship for p in profile.people if p.relationship != "child"
                }:
                    count = sum(p.relationship == relation for p in profile.people)
                    limit = (
                        1
                        if relation in {"self", "spouse"}
                        else rule.get("relationship_limits", {}).get(relation)
                    )
                    if limit is None:
                        incomplete = True
                    elif count > limit:
                        invalid = True
            outcomes.add("doesnt_fit" if invalid else "unresolved" if incomplete else "fits")
        status = next(iter(outcomes)) if len(outcomes) == 1 else "unresolved"
        explanation = "Family composition checked against every applicable cited combination; conflicting outcomes remain unresolved."
        if provisional and status == "doesnt_fit":
            status = "unresolved"
            explanation = "This family exceeds the cited family-floater limits; separate cover for each person has not been checked."
        record("family", status, explanation, rules)
    return list(reasons.values())
