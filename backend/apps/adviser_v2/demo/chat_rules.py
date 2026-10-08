"""Neutral chat evaluation and deterministic insurer-independent question choice."""

import re
from itertools import combinations

from .contracts import PersonInput, PlanCard, Profile
from .conversation_contracts import FIELD_TOPICS, FIELDS, TOPIC_FIELDS, TOPIC_KEYS, Requirement
from .matching import evaluate
from .typed_matching import guard_applies, hard_limits


def source_rule(card, field, person_id=None, profile=None):
    rules = [
        r
        for r in card.get("executable_rules", [])
        if r["field"] == field
        and r.get("citations")
        and (not r.get("conditions") or r.get("condition_mode") == "quoted")
        and r.get("scope", "base") == "base"
        and guard_applies(r, profile, person_id)
        and r.get("variant") in (None, card["variant"])
        and r.get("person_id") in (None, person_id)
    ]
    if len(rules) == 1:
        return rules[0]
    if (
        rules
        and all(r["kind"] == "coverage" for r in rules)
        and len({r["value"] for r in rules}) == 1
    ):
        # Multiple base clauses may state the same covered/excluded outcome.
        # Preserve every condition and waiting period rather than discarding a
        # passing unit or using the first quotation as the whole benefit.
        return {
            **rules[0],
            "citations": [c for r in rules for c in r["citations"]],
            "conditions": list(dict.fromkeys(c for r in rules for c in r.get("conditions", []))),
            "waiting_months": sorted({m for r in rules for m in r.get("waiting_months", [])}),
            "limits_rupees": sorted({m for r in rules for m in r.get("limits_rupees", [])}),
        }
    return None


def waiting_months(card, need, profile=None):
    """The printed waiting period for a need shown for information, if one is cited."""
    rule = source_rule(card, need.field, need.person_id, profile)
    if rule and rule["kind"] == "maximum" and rule.get("unit") == "months":
        return int(float(rule["value"]))
    return None


def cited(rule):
    """A cited rule's quotes as one statement, shown the way the engine's answers are."""
    quotes = list(dict.fromkeys(c["quote"] for c in rule["citations"]))
    quotes = [q for q in quotes if not any(q != other and q in other for other in quotes)]
    return {
        "heading": "Policy excerpt",
        "text": quotes[0],
        "excerpts": quotes,
        "coverage_scope": "base",
        "conditions": [],
        "restrictions": [],
        "citations": rule["citations"],
    }


def topic_verdict(card, topic, banked, profile=None):
    """One answer per plan and topic, used by every table and count in a reply.

    Decided in requirement_result's order: a cited base rule, then the engine's stored
    answer (banked) when it puts the topic in the base cover, then an add-on the card
    shows is sold, then the stored answer. When the card decides, its own quoted
    statements come with the group; otherwise they are None."""
    field = TOPIC_FIELDS.get(topic)
    rule = source_rule(card, field, None, profile) if field else None
    if rule and rule["kind"] == "coverage" and rule["value"] not in {"covered", "not_covered"}:
        rule = None
    if rule and rule["kind"] == "bonus" and float(rule["value"]) <= 0:
        rule = None
    sold = ((card.get("optional_covers") or {}).get(field) or {}) if field else {}
    added = [{**s, "coverage_scope": "optional, extra premium"} for s in sold.get("statements", [])]
    excluded = bool(rule) and rule["kind"] == "coverage" and rule["value"] == "not_covered"
    if rule and not excluded:
        return "base", [cited(rule)]
    if added and (excluded or banked != "base"):
        return "addon", added
    if added:
        # The base cover has part of it: the add-on that extends it is shown beside the
        # engine's answer, and never makes the plan add-on only.
        return "base", added
    if rule and banked != "addon":
        return "excluded", [cited(rule)]
    return banked, None


def requirement_result(card, need, profile=None):
    rule = source_rule(card, need.field, need.person_id, profile)
    status, quotes = "unresolved", []
    if rule:
        quotes = rule["citations"]
        if need.value == "shown":
            # Shown for information: a stated wait answers it; nothing conflicts.
            status = "fits" if waiting_months(card, need, profile) is not None else "unresolved"
        elif rule["kind"] == "coverage" and need.value == "covered":
            status = {"covered": "fits", "not_covered": "doesnt_fit"}.get(
                rule["value"], "unresolved"
            )
        elif rule["kind"] == "bonus" and need.value == "covered":
            status = "fits" if float(rule["value"]) > 0 else "unresolved"
        elif rule["kind"] == "room" and need.value.startswith("room:"):
            requested = need.value.split(":", 1)[1]
            category = rule["value"]
            order = {
                "shared": 0,
                "twin_sharing": 1,
                "single_standard": 2,
                "single_private": 3,
                "suite": 4,
            }
            if category == requested or category == "any_room":
                status = "fits"
            elif category in order and requested in order and order[category] < order[requested]:
                status = "doesnt_fit"
            elif category in {"any_room_except_suite", "any_room_except_deluxe_suite"}:
                if requested == "suite" or (
                    category == "any_room_except_deluxe_suite" and requested == "deluxe"
                ):
                    status = "doesnt_fit"
                elif requested in {"shared", "twin_sharing", "single_standard", "single_private"}:
                    status = "fits"
        elif rule["kind"] == "bonus" and re.fullmatch(
            r"bonus_at_least:\d+(?:\.\d+)?:percent", need.value
        ):
            requested = float(need.value.split(":")[1])
            status = "fits" if float(rule["value"]) >= requested else "doesnt_fit"
        elif rule["kind"] == "maximum" and re.fullmatch(
            r"at_most:\d+(?:\.\d+)?:[a-z_]+", need.value
        ):
            _, requested, unit = need.value.split(":")
            if unit == rule.get("unit"):
                status = "fits" if float(rule["value"]) <= float(requested) else "doesnt_fit"
    detail = None
    if need.value == "covered" and status in {"doesnt_fit", "unresolved"}:
        topic = FIELD_TOPICS.get(need.field, need.field)
        banked = (card.get("bank_groups") or {}).get(topic) if topic in TOPIC_KEYS else None
        if status == "unresolved" and banked == "base":
            # No cited rule: the engine's validated answer puts it in the base cover.
            status = "fits"
        elif (card.get("optional_covers") or {}).get(need.field) or banked == "addon":
            # Sold as an optional add-on: the customer can buy it, so it never rules the
            # plan out.
            status, detail = "addon", "Add-on (extra premium)"
        elif status == "unresolved" and banked == "excluded":
            # Only a cited rule rules a plan out, since an uncited conflict never excludes.
            status = "doesnt_fit"
    elif need.value == "shown" and status == "unresolved":
        banked = (card.get("bank_groups") or {}).get(FIELD_TOPICS.get(need.field, need.field))
        detail = "See wording" if banked == "base" else None
    common = {f["field"]: f["value"] for f in card.get("common_needs", [])}
    field = card.get(need.field) or common.get(need.field, {})
    quotes = quotes or field.get("citations", [])
    labels = {
        "fits": "Covered for this documented check.",
        "doesnt_fit": "The document states a conflicting limit or exclusion.",
        "unresolved": "Cannot establish this requirement and its applicable conditions from the evidence.",
        "addon": "Available as an optional add-on for an extra premium.",
    }
    waiting = rule.get("waiting_months", []) if rule else []
    if waiting and status == "fits":
        labels["fits"] += (
            " Printed waiting period: "
            + ", ".join(str(v) + " months" for v in waiting)
            + ". Quoted conditions and limits apply."
        )
    return {
        "field": need.field,
        "status": status,
        # Only a cited executable rule can rule a plan out; the stored answers label it.
        "ruled": bool(rule),
        "strength": need.strength,
        "coverage_status": {
            "fits": "covered",
            "doesnt_fit": "not covered",
            "unresolved": "can’t tell",
            "addon": "optional add-on",
        }[status],
        "explanation": need.original_text + " — " + labels[status],
        "citations": quotes,
        **({"detail": detail} if detail else {}),
    }


def single_type(cards):
    """The one cover type every plan in the catalogue has, if there is one."""
    types = {c["plan_type"] for c in cards}
    return next(iter(types)) if len(types) == 1 and "unresolved" not in types else None


def fit_groups(cards, profile):
    groups = {"fits": [], "unresolved": [], "doesnt_fit": []}
    # Cover type is no limit when the customer has no preference or every plan
    # in the catalogue is the same type; a stated type is still checked.
    any_type = profile.plan_type == "unresolved" and (
        getattr(profile, "any_type", False) or single_type(cards) is not None
    )
    for card in sorted(
        cards,
        key=lambda c: (
            c["insurer"].casefold(),
            c["name"].casefold(),
            c["variant"].casefold(),
            c["plan_id"],
        ),
    ):
        # Legacy projections remain supported; missing checks, rather than an
        # overall partial-card flag, determine uncertainty.
        old = {k: v for k, v in card.items() if k in PlanCard.model_fields}
        old["schema_version"] = 1
        validated = PlanCard.model_validate(old)
        if validated.status != "documents_unavailable":
            validated = validated.model_copy(update={"status": "ready"})
        if profile.people:
            p = Profile(
                people=[
                    PersonInput(
                        id=p.id,
                        relationship=p.relationship,
                        age_days=(
                            p.age * 365
                            if p.age_unit == "years"
                            else p.age
                            if p.age_unit == "days"
                            else None
                        )
                        if p.age is not None
                        else None,
                        dependent=p.dependent,
                    )
                    for p in profile.people
                ],
                city=profile.city,
                sum_insured=profile.sum_insured,
                annual_budget=profile.annual_budget,
                zone=None,
                plan_type=profile.plan_type,
            )
            result = evaluate(validated, p).model_dump()
        else:
            result = {
                "plan_id": card["plan_id"],
                "index_version": card["index_version"],
                "status": "unresolved",
                "hard_limits": [
                    {
                        "field": "people",
                        "status": "unresolved",
                        "explanation": "Who needs cover is not established.",
                        "citations": [],
                    }
                ],
                "other_needs": [],
            }
        if card.get("card_version"):
            type_rule = source_rule(card, "plan_type")
            for reason in result["hard_limits"]:
                if reason["field"] == "plan_type":
                    if type_rule:
                        reason["citations"] = type_rule["citations"]
                    else:
                        reason.update(
                            status="unresolved",
                            explanation="Product type needs cited executable evidence.",
                            citations=[],
                        )
            if profile.coverage_basis:
                rule = source_rule(card, "coverage_basis")
                supported = rule and profile.coverage_basis in rule["value"].split("|")
                result["hard_limits"].append(
                    {
                        "field": "coverage_basis",
                        "status": ("fits" if supported else "doesnt_fit") if rule else "unresolved",
                        "explanation": "Coverage-basis check against the printed choices."
                        if rule
                        else "Coverage basis is not established.",
                        "citations": rule["citations"] if rule else [],
                    }
                )
        if card.get("card_schema_version", 0) >= 3:
            result["hard_limits"] = hard_limits(card, profile, result["hard_limits"])
        if any_type:
            result["hard_limits"] = [r for r in result["hard_limits"] if r["field"] != "plan_type"]
        for need in profile.requirements:
            reason = requirement_result(card, need, profile)
            result["other_needs"].append(reason)
            # Only a need with cited executable rules filters plans; the rest label them.
            if need.strength == "must_have" and need.field in FIELDS and need.value != "shown":
                result["hard_limits"].append(reason)
        # Never exclude from unsupported metadata or an uncited conflict.
        for reason in result["hard_limits"]:
            if reason["status"] == "doesnt_fit" and (
                not reason["citations"] or reason.get("ruled") is False
            ):
                reason.update(
                    status="unresolved", explanation="A cited conflict has not been established."
                )
        result["status"] = (
            "doesnt_fit"
            if any(r["status"] == "doesnt_fit" for r in result["hard_limits"])
            else "unresolved"
            if any(r["status"] == "unresolved" for r in result["hard_limits"])
            else "fits"
        )
        groups[result["status"]].append(result)
    return groups


def remaining_ids(groups):
    return {r["plan_id"] for key in ("fits", "unresolved") for r in groups[key]}


def differentiator(cards, groups, suppressed, profile=None):
    remaining = remaining_ids(groups)
    candidates = []
    for order, field in enumerate(FIELDS):
        if field in suppressed:
            continue
        values = []
        for card in cards:
            if card["plan_id"] not in remaining:
                continue
            rule = source_rule(card, field, profile=profile)
            if rule and rule["kind"] in {"coverage", "maximum", "bonus", "room"}:
                values.append((card, rule))
        if len({(r["kind"], r.get("unit")) for _, r in values}) > 1:
            continue
        score = sum(
            (a[1]["value"], a[1].get("unit")) != (b[1]["value"], b[1].get("unit"))
            for a, b in combinations(values, 2)
        )
        if score:
            candidates.append((score, -order, field, values))
    # Most informative first; a question that would rule out no plan narrows nothing.
    for _, _, field, values in sorted(candidates, key=lambda c: (c[0], c[1]), reverse=True):
        found = proposal(values)
        if found is None:
            continue
        proposed, count = found
        need = Requirement(field=field, original_text=field, strength="must_have", value=proposed)
        if not any(
            (result := requirement_result(card, need, profile))["status"] == "doesnt_fit"
            and result["citations"]
            for card, _ in values
        ):
            continue
        return {
            "field": field,
            "value": proposed,
            "count": count,
            "remaining": len(remaining),
            "known": len(values),
            "source_indexes": sorted({c["index_version"] for c, _ in values}),
            "quotes": [q for _, r in values for q in r["citations"]],
            "conditions": list(
                dict.fromkeys(c for _, r in values for c in r.get("conditions", []))
            ),
        }
    return None


def proposal(values):
    """The must-have a narrowing question proposes, and how many plans meet it."""
    rule = values[0][1]
    if all(r["kind"] == "coverage" for _, r in values):
        return "covered", sum(r["value"] == "covered" for _, r in values)
    if all(r["kind"] == "maximum" and r.get("unit") == rule.get("unit") for _, r in values):
        minimum = min(float(r["value"]) for _, r in values)
        return f"at_most:{minimum:g}:{rule['unit']}", sum(
            float(r["value"]) <= minimum for _, r in values
        )
    if all(r["kind"] == "room" for _, r in values):
        category = sorted(r["value"] for _, r in values)[0]
        return "room:" + category, sum(r["value"] == category for _, r in values)
    if all(r["kind"] == "bonus" for _, r in values):
        amount = max(float(r["value"]) for _, r in values)
        return f"bonus_at_least:{amount:g}:percent", sum(
            float(r["value"]) >= amount for _, r in values
        )
    return None
