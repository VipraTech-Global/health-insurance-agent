"""Neutral, complete fit evaluation using documented entry limits only."""

from .contracts import FitReason, FitResult, PlanCard, Profile


def evaluate(card: PlanCard, profile: Profile) -> FitResult:
    hard: list[FitReason] = []

    def add(field, status, explanation, citations=()):
        hard.append(FitReason(field=field, status=status, explanation=explanation, citations=list(citations)))

    if card.plan_type == "unresolved" or profile.plan_type == "unresolved":
        add("plan_type", "unresolved", "Plan type has not been established.")
    elif card.plan_type != profile.plan_type:
        add("plan_type", "doesnt_fit", "This plan is a different type from the requested cover.")
    else:
        add("plan_type", "fits", "Plan type matches.")
    for person in profile.people:
        rules = [r for r in card.entry_ages if r.relationship == person.relationship]
        if person.age_days is None or len(rules) != 1:
            add("entry_age:" + person.id, "unresolved", "Entry-age evidence or this person's age is missing.")
            continue
        rule = rules[0]
        if rule.minimum_days is None or (rule.maximum_days is None and not rule.maximum_unbounded):
            add("entry_age:" + person.id, "unresolved", "The full entry-age range is not established.", rule.citations)
        elif person.age_days < rule.minimum_days or (rule.maximum_days is not None and person.age_days > rule.maximum_days):
            add("entry_age:" + person.id, "doesnt_fit", "This person's age falls outside the documented entry range.", rule.citations)
        else:
            add("entry_age:" + person.id, "fits", "This person's age is within the documented entry range; underwriting still applies.", rule.citations)
    family = card.family_rule
    if family is None:
        add("family", "unresolved", "Permitted family composition has not been established.")
    else:
        children = [p for p in profile.people if p.relationship == "child"]
        adults = len(profile.people) - len(children)
        invalid = (any(p.relationship not in family.allowed_relationships for p in profile.people)
                   or adults > family.maximum_adults or len(children) > family.maximum_children
                   or (family.children_must_be_dependent and any(p.dependent is False for p in children)))
        if invalid:
            add("family", "doesnt_fit", "The requested family composition exceeds a documented restriction.", family.citations)
        elif family.children_must_be_dependent and any(p.dependent is None for p in children):
            add("family", "unresolved", "Dependent-child status is needed.", family.citations)
        else:
            add("family", "fits", "The family composition matches the documented limits.", family.citations)
    si = card.sum_insured
    if profile.sum_insured is None or si.state == "not_stated" or not si.numbers or not si.citations:
        add("sum_insured", "unresolved", "Sum-insured evidence or the requested amount is missing.")
    elif si.variant is not None and si.variant != card.variant:
        add("sum_insured", "unresolved", "The sum-insured evidence is for a different variant.")
    elif si.conditions:
        add("sum_insured", "unresolved", "The stated sum-insured choice has conditions requiring a document check.", si.citations)
    elif profile.sum_insured not in si.numbers and not si.exhaustive:
        add("sum_insured", "unresolved", "The complete list of sum-insured choices is not established.", si.citations)
    else:
        fits = profile.sum_insured in si.numbers
        add("sum_insured", "fits" if fits else "doesnt_fit",
            "The requested amount is listed." if fits else "The requested amount is not among the documented choices.", si.citations)
    geography = card.geography
    # A premium zone alone is not a treatment territory or an eligibility restriction.
    if geography.state == "not_stated" or not geography.citations:
        add("geography", "unresolved", "Purchase geography limits have not been established.")
    elif not profile.city:
        add("geography", "unresolved", "City is needed to check applicable geography.", geography.citations)
    elif geography.conditions or (geography.variant is not None and geography.variant != card.variant):
        add("geography", "unresolved", "Geographic conditions or variant applicability need checking.", geography.citations)
    elif "all_india" in geography.labels or profile.city.casefold() in {s.casefold() for s in geography.labels}:
        add("geography", "fits", "The stated purchase geography includes this location.", geography.citations)
    elif geography.exhaustive:
        add("geography", "doesnt_fit", "The location is outside the documented purchase geography.", geography.citations)
    else:
        add("geography", "unresolved", "The complete purchase geography is not established.", geography.citations)
    if card.status != "ready":
        add("documents", "unresolved", "The applicable document bundle or facts card is incomplete.")
    other = []
    for need in profile.needs:
        field = getattr(card, need, None)
        other.append(FitReason(field=need, status="unresolved",
            explanation="See the quoted benefit and its conditions in chat." if field and field.citations else "Not stated; ask in chat.",
            citations=field.citations if field else []))
    if profile.typed_needs:
        other.append(FitReason(field="typed_needs", status="unresolved",
            explanation="Can't check this automatically; ask in chat.", citations=[]))
    status = "doesnt_fit" if any(r.status == "doesnt_fit" for r in hard) else (
        "unresolved" if any(r.status == "unresolved" for r in hard) else "fits")
    return FitResult(plan_id=card.plan_id, index_version=card.index_version, status=status,
                     hard_limits=hard, other_needs=other)


def all_fits(cards: list[PlanCard], profile: Profile) -> list[FitResult]:
    return [evaluate(c, profile) for c in sorted(cards, key=lambda c: (c.insurer.casefold(), c.name.casefold(), c.variant.casefold(), c.plan_id))]


def validate_selection(cards: list[PlanCard], identifiers: list[str]) -> list[PlanCard]:
    if not 2 <= len(identifiers) <= 5 or len(set(identifiers)) != len(identifiers):
        raise ValueError("Select two to five distinct plans.")
    by_id = {c.plan_id: c for c in cards}
    if any(key not in by_id for key in identifiers):
        raise ValueError("A selected plan is outside this release.")
    selected = [by_id[key] for key in identifiers]
    if len({c.plan_type for c in selected}) != 1 or selected[0].plan_type == "unresolved":
        raise ValueError("Select plans of the same established plan type.")
    return selected
