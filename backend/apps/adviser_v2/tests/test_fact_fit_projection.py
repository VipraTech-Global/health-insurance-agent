from apps.adviser_v2.demo.chat_rules import requirement_result
from apps.adviser_v2.demo.conversation_contracts import ChatPerson, IncompleteProfile, Requirement
from apps.adviser_v2.demo.fact_fit_projection import optional_unit
from apps.adviser_v2.demo.fact_projection import project
from apps.adviser_v2.demo.fact_rule_contracts import FactRule
from apps.adviser_v2.demo.typed_matching import hard_limits
from apps.adviser_v2.tests.test_fact_rules_v3 import statement


def test_purchase_geography_never_comes_from_treatment_territory():
    assert not project(
        "geography",
        [statement("All treatment under this policy must be taken in India.")],
        "Default",
    )
    rules = project(
        "geography",
        [
            statement(
                "Premium Payment Zones: For premium computation based on the residential address. Zone A Mumbai; Zone B Rest of India."
            )
        ],
        "Default",
    )
    assert rules and FactRule.model_validate(rules[0]).value == "india"
    card = {"variant": "Default", "executable_rules": rules}
    old = [{"field": "geography", "status": "unresolved", "citations": []}]
    checked = hard_limits(card, IncompleteProfile(city="Pune"), old)
    assert checked[0]["status"] == "fits" and checked[0]["citations"]
    assert hard_limits(card, IncompleteProfile(city="Paris"), old)[0]["status"] == "unresolved"
    assert not project(
        "geography",
        [statement("This policy is available only in Delhi. Treatment is covered across India.")],
        "Default",
    )


def test_basis_uses_own_typed_field_and_accepts_operative_options_heading():
    rules = project(
        "coverage_basis", [statement("Coverage Options Individual/Family floater")], "Default"
    )
    assert rules[0]["value"] == "individual|floater"
    card = {"variant": "Default", "executable_rules": rules}
    result = hard_limits(card, IncompleteProfile(coverage_basis="floater"), [])
    assert result[0]["field"] == "coverage_basis" and result[0]["status"] == "fits"


def test_positive_base_maternity_with_waiting_and_excluded_complication():
    s = statement(
        "Maternity Cover. We will cover for Maternity Expenses subject to a waiting period of 3 years of continuous coverage. We will not cover ectopic pregnancy under this benefit."
    )
    rules = project("maternity", [s], "Default")
    assert len(rules) == 1 and rules[0]["value"] == "covered"
    assert rules[0]["waiting_months"] == [36]
    result = requirement_result(
        {"variant": "Default", "executable_rules": rules},
        Requirement(
            field="maternity", original_text="Maternity is a must-have", strength="must_have"
        ),
    )
    assert result["status"] == "fits" and "36 months" in result["explanation"]


def test_delivery_wording_can_establish_base_maternity():
    rules = project(
        "maternity",
        [
            statement(
                "Delivery Expenses: Expenses for a Delivery including Delivery by Caesarean section, subject to a maximum of 2 deliveries in the entire life time of the Insured Person, are payable."
            )
        ],
        "Default",
    )
    assert rules[0]["value"] == "covered"


def test_outpatient_exclusion_is_contrary_but_temporary_wait_is_not():
    assert (
        project(
            "opd", [statement("Specific Exclusions: Outpatient treatment expenses.")], "Default"
        )[0]["value"]
        == "not_covered"
    )
    assert not project(
        "opd",
        [
            statement(
                "Outpatient treatment is not covered until expiry of the waiting period of 12 months."
            )
        ],
        "Default",
    )


def test_optional_context_and_choice_menus_do_not_establish_base():
    s = statement("Room Modifier: option to modify eligibility to any room category.")
    assert optional_unit(s, "room_limit")
    s = statement("Co-Payment 0%, 10%, 20%, 30%, 40%, 50%")
    assert optional_unit(s, "copay")
    s = statement("Any room category is covered.")
    s["conditions"] = [
        statement("This Optional Cover is available across all Sum Insured options.")
    ]
    assert optional_unit(s, "room_limit")


def test_elite_room_exception_is_not_unrestricted_room():
    rules = project(
        "room_limit", [statement("Room entitlement: Any Room except Deluxe/Suite.")], "Elite"
    )
    assert rules[0]["value"] == "any_room_except_deluxe_suite"
    result = requirement_result(
        {"variant": "Elite", "executable_rules": rules},
        Requirement(
            field="room_limit", original_text="Suite", value="room:suite", strength="must_have"
        ),
    )
    assert result["status"] == "doesnt_fit"


def test_onwards_entry_does_not_mean_lifetime_renewal():
    rules = project("entry_age", [statement("Entry Age: Adults: 18 years onwards.")], "Default")
    assert rules and rules[0]["maximum_unbounded"]
    assert not project("entry_age", [statement("Adult renewal age: 18 years onwards.")], "Default")


def test_nationwide_geography_and_basis_do_not_erase_missing_family():
    rules = project(
        "geography",
        [statement("Indian nationals residing in India are eligible for this policy.")],
        "Default",
    )
    rules += project(
        "coverage_basis",
        [statement("Type of Policy: Individual Sum Insured and Floater Sum Insured.")],
        "Default",
    )
    result = hard_limits(
        {"variant": "Default", "executable_rules": rules},
        IncompleteProfile(
            city="Pune",
            coverage_basis="floater",
            people=[ChatPerson(id="self", relationship="self", age=35)],
        ),
        [{"field": "family", "status": "fits", "citations": []}],
    )
    assert next(r for r in result if r["field"] == "family")["status"] == "unresolved"


def test_inline_sum_insured_choices_preserve_unlimited_and_reject_booster():
    rules = project(
        "sum_insured",
        [
            statement(
                "Sum Insured Options are: 5 Lacs10 Lacs, Unlimited\nThe Sum Insured opted by you is mentioned in the Policy Schedule."
            )
        ],
        "Default",
    )
    assert rules[0]["choices"] == [500000, 1000000]
    assert rules[0]["unlimited_choice"]
    assert not project(
        "sum_insured",
        [statement("Booster+ worked example: Sum Insured Options:\n5 lakh, 10 lakh, 50 lakh")],
        "Default",
    )


def test_separate_named_minimum_and_maximum_age_sentences():
    raw = "The minimum entry age for adult is 18 years and for dependent child is 91 days. The maximum entry age limit for adults in this product is 99 years. The maximum entry age allowed for dependent child is 30 years."
    rules = project("entry_age", [statement(raw)], "Default")
    assert any(
        r["relationship"] == "adult" and r["minimum"] == 18 and r["maximum"] == 99 for r in rules
    )


def test_family_relation_check_is_applicable_to_the_requested_combination():
    s = statement(
        "Floater Policy: Relationships covered: Self, spouse and up to 3 dependent children, up to 2 parents and up to 2 parents-in-law."
    )
    rules = project("family", [s], "Default")
    assert rules and FactRule.model_validate(rules[0])
    profile = IncompleteProfile(
        coverage_basis="floater",
        people=[
            ChatPerson(id="self", relationship="self", age=35),
            ChatPerson(id="spouse", relationship="spouse", age=33),
            ChatPerson(id="child", relationship="child", age=8, dependent=True),
        ],
    )
    result = hard_limits({"variant": "Default", "executable_rules": rules}, profile, [])
    assert next(r for r in result if r["field"] == "family")["status"] == "fits"
    profile.people.extend(
        [
            ChatPerson(id="child2", relationship="child", age=6, dependent=True),
            ChatPerson(id="child3", relationship="child", age=4, dependent=True),
            ChatPerson(id="child4", relationship="child", age=2, dependent=True),
        ]
    )
    result = hard_limits({"variant": "Default", "executable_rules": rules}, profile, [])
    assert next(r for r in result if r["field"] == "family")["status"] == "doesnt_fit"


def test_lifelong_entry_table_separates_adults_children_and_exit_age():
    rules = project(
        "entry_age",
        [
            statement(
                "Entry Age – Minimum Adult: 18 years\nChild: 90 days\nEntry Age – Maximum Adult: Lifelong\nChild: 24 years (last birthday)\nExit Age Adult: Lifelong\nChild: 25 years"
            )
        ],
        "Default",
    )
    adult = next(r for r in rules if r["relationship"] == "adult")
    child = next(r for r in rules if r["relationship"] == "child")
    assert adult["minimum"] == 18 and adult["maximum_unbounded"]
    assert child["minimum"] == 90 and child["maximum"] == 24


def test_explicit_nationwide_pricing_scheme_requires_all_numbered_zones():
    prefix = "Zonal pricing. For calculating premium, the country has been divided into the following 3 zones: "
    assert not project("geography", [statement(prefix + "Zone 1: Delhi. Zone 2: Pune.")], "Default")
    assert project(
        "geography",
        [statement(prefix + "Zone 1: Delhi. Zone 2: Pune. Zone 3: all other states.")],
        "Default",
    )


def test_optional_exception_does_not_turn_base_exclusion_into_base_cover():
    s = statement(
        "WHAT WE WILL NOT PAY (EXCLUSIONS UNDER THE POLICY)\nOut Patient treatment, except optional cover BeFit opted."
    )
    assert project("opd", [s], "Default")[0]["value"] == "not_covered"
    assert not optional_unit(s, "opd")


def test_general_entry_age_does_not_use_proposer_age_as_minimum():
    rules = project(
        "entry_age",
        [
            statement(
                "Entry age: This Policy can be offered to an individual with minimum age of 6 years (Proposer needs to be 18 years and above). Maximum entry age is up to 125 years."
            )
        ],
        "Default",
    )
    assert len(rules) == 1 and rules[0]["minimum"] == 6 and rules[0]["maximum"] == 125


def test_sum_choices_multiple_units_support_only_explicit_values():
    rules = project(
        "sum_insured",
        [statement("Sum Insured (SI) – on annual basis (in Rs.)\n5L/ 7L/ 10L/ 15L/ 1 Cr")],
        "Default",
    )
    assert rules[0]["choices"] == [500000, 700000, 1000000, 1500000, 10000000]
    card = {"variant": "Default", "executable_rules": rules}
    result = hard_limits(card, IncompleteProfile(sum_insured=1000000), [])
    assert result[0]["status"] == "fits"
    result = hard_limits(card, IncompleteProfile(sum_insured=600000), [])
    assert result[0]["status"] == "unresolved"


def test_multiple_positive_base_clauses_retain_waits_and_contrary_stays_unknown():
    rules = project(
        "maternity",
        [
            statement("Maternity is covered after a waiting period of 24 months."),
            statement("Maternity is covered subject to a limit of Rs. 50000."),
        ],
        "Default",
    )
    need = Requirement(field="maternity", original_text="Maternity", strength="must_have")
    card = {"variant": "Default", "executable_rules": rules}
    result = requirement_result(card, need)
    assert result["status"] == "fits" and "24 months" in result["explanation"]
    card["executable_rules"] += project(
        "maternity", [statement("Maternity is not covered.")], "Default"
    )
    assert requirement_result(card, need)["status"] == "unresolved"


def test_conditional_penalty_is_not_unconditional_base_copay():
    rules = project(
        "copay",
        [
            statement(
                "In event of failure to intimate within 7 days an additional cumulative co-payment of 10% will be levied."
            )
        ],
        "Black",
    )
    assert rules and all(r["restricted_scope"] for r in rules)


def test_selected_cell_under_optional_heading_remains_optional():
    from apps.adviser_v2.demo.fact_fit_projection import optional_table

    s = statement("10%")
    s["table"] = {"region_id": "t", "value_cell_id": "v"}
    b = {
        "tables": [
            {
                "id": "t",
                "cells": {
                    "h": {"row": 2, "text": "Optional Benefits"},
                    "v": {"row": 3, "text": "10%"},
                },
            }
        ]
    }
    assert optional_table(s, b)


def test_child_entry_bound_allows_parenthetical_definition_without_changing_numbers():
    rules = project(
        "entry_age",
        [
            statement(
                "The minimum entry age for a dependent child (i.e. natural or legally adopted) is 91 days and maximum entry age is 25 years."
            )
        ],
        "Default",
    )
    assert len(rules) == 1 and rules[0]["minimum"] == 91 and rules[0]["maximum"] == 25


def test_primary_spouse_pair_constraint_does_not_guess_parent_relationships():
    s = statement(
        "Family Floater: maximum 2 adults and 4 children; self, spouse, children and parents. The relationship between the Insureds will always have to be Primary Insured and their Spouse."
    )
    rules = project("family", [s], "Default")
    assert rules[0]["primary_spouse_pair_only"]
    profile = IncompleteProfile(
        coverage_basis="floater",
        people=[
            ChatPerson(id="p1", relationship="parent", age=60),
            ChatPerson(id="p2", relationship="parent", age=58),
        ],
    )
    result = hard_limits({"variant": "Default", "executable_rules": rules}, profile, [])
    assert next(r for r in result if r["field"] == "family")["status"] == "unresolved"


def family_status(rules, profile):
    old = [{"field": "family", "status": "unresolved", "citations": []}]
    result = hard_limits({"variant": "Default", "executable_rules": rules}, profile, old)
    return next(r for r in result if r["field"] == "family")


def test_floater_limits_confirm_but_never_exclude_without_a_stated_basis():
    rules = project(
        "family",
        [statement("Floater Policy: Self, spouse and up to 3 dependent children.")],
        "Default",
    )
    family = [
        ChatPerson(id="self", relationship="self", age=35),
        ChatPerson(id="spouse", relationship="spouse", age=33),
        ChatPerson(id="child", relationship="child", age=8, dependent=True),
    ]
    assert family_status(rules, IncompleteProfile(people=family))["status"] == "fits"
    large = family + [
        ChatPerson(id=f"c{i}", relationship="child", age=i, dependent=True) for i in (2, 4, 6)
    ]
    unknown = family_status(rules, IncompleteProfile(people=large))
    assert unknown["status"] == "unresolved" and "separate cover" in unknown["explanation"]
    floater = IncompleteProfile(people=large, coverage_basis="floater")
    assert family_status(rules, floater)["status"] == "doesnt_fit"
    individual = IncompleteProfile(people=family, coverage_basis="individual")
    assert family_status(rules, individual)["status"] == "unresolved"
    assert family_status(rules, individual)["citations"] == []


def test_number_words_bound_to_children_set_the_printed_limit():
    raw = "Floater basis: a family consisting of Self, Spouse, dependent children not exceeding three, dependent Parents and Parents-in-law."
    rules = project("family", [statement(raw)], "Default")
    assert rules and rules[0]["maximum_children"] == 3
    assert "not exceeding three" in rules[0]["printed"]
    rules = project(
        "family",
        [statement("Floater basis: Self and Spouse; children up to three years old.")],
        "Default",
    )
    assert all(r["maximum_children"] is None for r in rules)


def test_grounding_rejects_a_number_word_not_in_the_quote():
    from apps.adviser_v2.demo.fact_rule_grounding import grounded

    raw = "Floater basis: Self, Spouse, dependent children not exceeding three."
    rule = project("family", [statement(raw)], "Default")[0]
    assert grounded(rule)
    assert not grounded({**rule, "maximum_children": 4})


def test_city_answer_to_the_india_question_establishes_residence():
    rules = project(
        "geography",
        [
            statement(
                "Premium Payment Zones: For premium computation based on the residential address. Zone A Mumbai; Zone B Rest of India."
            )
        ],
        "Default",
    )
    card = {"variant": "Default", "executable_rules": rules}
    old = [{"field": "geography", "status": "unresolved", "citations": []}]
    assert hard_limits(card, IncompleteProfile(city="Kota"), old)[0]["status"] == "unresolved"
    resident = IncompleteProfile(city="Kota", resides_in_india=True)
    assert hard_limits(card, resident, old)[0]["status"] == "fits"


def test_single_sum_insured_family_list_names_the_proposer_as_self():
    raw = (
        "Yes. You can cover the entire family under a Single Sum Insured. The members of the family who\n"
        "could be covered under the Policy are:\na) Proposer\nb) Proposer’s Spouse\n"
        "c) Proposer’s Dependent Children\nd) Proposer’s Parents"
    )
    rules = project("family", [statement(raw)], "Default")
    assert rules and {"self", "spouse", "child", "parent"} <= set(rules[0]["relationships"])
    assert rules[0]["maximum_children"] is None and rules[0]["coverage_basis"] == "floater"
    two = [
        ChatPerson(id="self", relationship="self", age=29),
        ChatPerson(id="spouse", relationship="spouse", age=28),
    ]
    assert family_status(rules, IncompleteProfile(people=two))["status"] == "fits"
    kids = two + [
        ChatPerson(id=f"c{i}", relationship="child", age=i, dependent=True) for i in (3, 5)
    ]
    assert family_status(rules, IncompleteProfile(people=kids))["status"] == "unresolved"
    assert not project(
        "family",
        [
            statement(
                "The family under a Single Sum Insured: a) Proposer’s Spouse b) Proposer’s Children"
            )
        ],
        "Default",
    )


def test_premium_zones_with_rest_of_india_cover_the_country():
    raw = "Premium will be charged based on the classification of the zones namely\nZon\ne 1\nMaharashtraand Gujarat\nZon\ne 2\nRest Of India"
    rules = project("geography", [statement(raw)], "Default")
    assert rules and rules[0]["value"] == "india"
