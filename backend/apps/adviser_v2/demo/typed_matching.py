"""Execute cited bounded rules against incomplete customer details."""


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

    def record(field, status, explanation, rules):
        reasons[field] = {
            "field": field,
            "status": status,
            "explanation": explanation,
            "citations": [q for r in rules for q in r["citations"]],
        }

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
    if len(rules) == 1 and profile.plan_type != "unresolved":
        record(
            "plan_type",
            "fits" if rules[0]["value"] == profile.plan_type else "doesnt_fit",
            "Requested product type checked against the cited description.",
            rules,
        )
    rules = eligible_rules(card, "coverage_basis")
    if profile.coverage_basis:
        status = (
            ("fits" if profile.coverage_basis in rules[0]["value"].split("|") else "doesnt_fit")
            if len(rules) == 1
            else "unresolved"
        )
        record(
            "coverage_basis",
            status,
            "Individual/floater basis is separate from product type.",
            rules,
        )
    rules = eligible_rules(card, "sum_insured")
    if len(rules) == 1 and profile.sum_insured is not None:
        rule = rules[0]
        status = (
            "fits"
            if profile.sum_insured in rule["choices"]
            else "doesnt_fit"
            if rule.get("exhaustive")
            else "unresolved"
        )
        record(
            "sum_insured",
            status,
            "Requested sum insured checked against the printed selectable choices.",
            rules,
        )
    rules = eligible_rules(card, "family")
    if len(rules) == 1 and (
        not rules[0].get("coverage_basis") or rules[0]["coverage_basis"] == profile.coverage_basis
    ):
        rule = rules[0]
        children = [p for p in profile.people if p.relationship == "child"]
        invalid = (
            any(p.relationship not in rule["relationships"] for p in profile.people)
            or len(children) > rule["maximum_children"]
            or len(profile.people) - len(children) > rule["maximum_adults"]
        )
        invalid |= bool(
            rule.get("dependent_children") and any(p.dependent is False for p in children)
        )
        incomplete = bool(
            rule.get("dependent_children") and any(p.dependent is None for p in children)
        )
        status = "doesnt_fit" if invalid else "unresolved" if incomplete else "fits"
        record(
            "family",
            status,
            "Family composition checked against cited adult, child and relationship limits.",
            rules,
        )
    return list(reasons.values())
