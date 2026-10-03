from apps.adviser_v2.demo.fact_governing import operative_basis, variant_proven
from apps.adviser_v2.demo.fact_projection import clauses, project
from apps.adviser_v2.demo.fact_rule_grounding import grounded
from apps.adviser_v2.tests.test_demo_contracts import packet
from apps.adviser_v2.tests.test_fact_rules_v3 import statement


def test_actual_room_clause_overrides_incidental_room_example():
    s = statement(
        "Room rent limit shall be 'At Actuals' unless otherwise specified. An example refers to a single private room."
    )
    rules = project("room_limit", [s], "Default")
    assert len(rules) == 1 and rules[0]["value"] == "actuals"
    assert not grounded({**rules[0], "value": "twin_sharing"})


def test_ped_duration_in_following_condition_is_not_specified_wait():
    s = statement(
        "Specified disease waiting period: Expenses excluded until expiry of 24 months of continuous coverage. For Pre-Existing Diseases a waiting period of 36 months applies."
    )
    assert [r["value"] for r in project("specified_waiting", [s], "Default")] == ["24"]


def test_any_numbered_maternity_exclusion_is_negative():
    s = statement(
        "Maternity expenses (Code Excl 17): Treatment expenses traceable to childbirth are excluded, except ectopic pregnancy."
    )
    assert project("maternity", [s], "Default")[0]["value"] == "not_covered"


def test_illustration_does_not_establish_basis():
    assert not operative_basis(
        statement("Benefit illustration: policy basis Individual; Sum insured 5 lakh.")
    )
    assert operative_basis(
        statement("This policy is available on individual and family floater basis.")
    )
    rules = project(
        "coverage_basis",
        [statement("This policy is available on individual and family floater basis.")],
        "Default",
    )
    assert rules[0]["value"] == "individual|floater"
    assert rules[0]["exhaustive"]
    assert not grounded({**rules[0], "value": "individual|floater|unknown"})


def test_partial_list_cannot_exclude_unlisted_amount():
    s = statement("Sum Insured Options:\n• Rs. 5,00,000/-")
    rules = project("sum_insured", [s], "Default")
    assert rules and not rules[0]["exhaustive"]


def test_shared_benefit_needs_selected_variant_column():
    s = statement("D.I.12 Outpatient treatment expenses are covered.")
    bundle = {"variant": "Protect", "variants": ["Protect", "Advantage"], "sections": []}
    assert not variant_proven(s, bundle)
    result = {"answer": {"statements": [s]}}
    assert not clauses(result, "opd", bundle)[0]
    assert "selected-variant" in result["projection_omissions"][0]


def test_age_value_cannot_borrow_unit_or_person_from_another_row():
    rules = project(
        "entry_age", [statement("Adults aged 18 years to 65 years are eligible.")], "Default"
    )
    assert len(rules) == 1 and rules[0]["relationship"] == "adult"
    assert not grounded({**rules[0], "maximum": 66})
    assert not grounded({**rules[0], "minimum_unit": "months"})


def test_eligibility_quote_drops_previous_dispute_and_ecs_heading():
    raw = "1.25. ECS\nNo additional charges will be levied.\n1.26. Dispute Resolution Clause\nDisputes determined by Courts.\n1.27. Eligibility\nThe minimum entry age for an adult is 18 years and there is no limit on maximum entry age.\n1.28. Other condition\nSomething else."
    bundle = {"sections": [packet(raw).sections[0].payload()]}
    s = statement(raw)
    kept = clauses({"answer": {"statements": [s]}}, "entry_age", bundle)[0]
    assert len(kept) == 1
    quote = kept[0]["citations"][0]["quote"]
    assert (
        quote.startswith("1.27. Eligibility")
        and "Dispute" not in quote
        and "Something else" not in quote
    )
    assert project("entry_age", kept, "Default")[0]["maximum_unbounded"]


def test_failed_rule_never_falls_back_to_legacy_exclusion():
    from apps.adviser_v2.demo.conversation_contracts import IncompleteProfile
    from apps.adviser_v2.demo.typed_matching import hard_limits

    old = [
        {
            "field": "family",
            "status": "doesnt_fit",
            "explanation": "Legacy",
            "citations": [{"quote": "old"}],
        }
    ]
    result = hard_limits({"variant": "Default", "executable_rules": []}, IncompleteProfile(), old)
    assert result[0]["status"] == "unresolved" and not result[0]["citations"]


def test_single_basis_and_incomplete_sum_list_do_not_exclude():
    from apps.adviser_v2.demo.conversation_contracts import IncompleteProfile
    from apps.adviser_v2.demo.typed_matching import hard_limits

    rules = project(
        "coverage_basis", [statement("This policy is available on individual basis.")], "Default"
    )
    rules += project("sum_insured", [statement("Sum Insured Options:\nRs. 5,00,000/-")], "Default")
    card = {"variant": "Default", "executable_rules": rules}
    p = IncompleteProfile(coverage_basis="floater", sum_insured=1000000)
    assert {r["status"] for r in hard_limits(card, p, [])} == {"unresolved"}


def test_all_bullets_are_preserved_but_unproven_list_end_is_not_exhaustive():
    s = statement("Sum Insured Options:\n• Rs. 5,00,000/-\n• Rs. 10,00,000/-\n• Rs. 3,00,00,000/-")
    rules = project("sum_insured", [s], "Default")
    assert rules[0]["choices"] == [500000, 1000000, 30000000]
    assert not rules[0]["exhaustive"]


def test_table_age_rows_keep_adult_and_child_bounds_separate():
    s = statement("Entry Age\nAdults 18years – 65 years\nChildren 91 days – 25 years")
    assert {
        (r["relationship"], r["minimum"], r["maximum"])
        for r in project("entry_age", [s], "Default")
    } == {("adult", 18, 65), ("child", 91, 25)}


def test_deterministic_list_completion_includes_every_bullet_before_next_heading():
    from dataclasses import replace

    from apps.adviser_v2.demo.fact_list_projection import complete_sum_list

    raw = "Sum Insured Options:\n• Rs. 5,00,000/-\n• Rs. 10,00,000/-\n• Rs. 3,00,00,000/-\nOther Benefits:\nRoom cover."
    pkt = packet(raw)
    segment = replace(
        pkt.sections[0].segments[0], start=0, end=len(raw), document_start=0, document_end=len(raw)
    )
    pkt = replace(pkt, sections=(replace(pkt.sections[0], segments=(segment,)),))
    bundle = {"policy_version_id": "plan", "sections": [pkt.sections[0].payload()]}
    s = statement(raw.split("\n• Rs. 10")[0])
    result = {"packet": pkt.evidence()}
    completed = complete_sum_list(result, bundle, s)
    assert "3,00,00,000" in completed["text"]
    assert completed["complete_options"]
    assert all(result["list_projection_audit"][0]["checks"])


def test_negative_basis_and_contradictory_exhaustive_choices_remain_unresolved():
    assert not operative_basis(statement("This policy is not available on floater basis."))
    rules = project(
        "coverage_basis",
        [
            statement("This policy is available only on individual basis."),
            statement("This policy is available only on floater basis."),
        ],
        "Default",
    )
    assert len(rules) == 2  # Matching requires exactly one consistent rule.


def test_following_numeric_condition_cannot_back_a_different_printed_value():
    s = statement(
        "Specified waiting period is 24 months. Pre-existing waiting period is 36 months."
    )
    rule = project("specified_waiting", [s], "Default")[0]
    assert not grounded({**rule, "value": "36"})


def test_minimum_maximum_table_pairs_only_same_person_row():
    raw = "Entry Age: Minimum Child- 91 days\nDependent children between 91 days and 5 years can be insured only when both parents are getting insured.\nAdult- 18 years\nEntry Age: Maximum Child- 25 years\nAdult- 65 years\nCover Ceasing age There is no maximum cover ceasing age."
    rules = project("entry_age", [statement(raw)], "Default")
    assert {(r["relationship"], r["minimum"], r["maximum"]) for r in rules} == {
        ("adult", 18, 65),
        ("child", 91, 25),
    }
    missing = raw.replace("Adult- 18 years", "")
    assert {r["relationship"] for r in project("entry_age", [statement(missing)], "Default")} == {
        "child"
    }


def test_illustration_column_without_its_title_is_still_not_basis_evidence():
    assert not operative_basis(
        statement(
            "Coverage opted on individual basis. Coverage opted on family ﬂoater basis. Premium (Rs.) Discount (if any)."
        )
    )


def test_selected_variant_header_must_align_with_the_value_cell():
    s = statement("Outpatient Protect Not Available")
    s["table"] = {
        "region_id": "grid",
        "row_label_ids": ["row"],
        "column_label_ids": ["protect"],
        "value_cell_id": "value",
    }
    cells = {
        "row": {"row": 1, "column": 0, "text": "Outpatient"},
        "protect": {"row": 0, "column": 1, "text": "Protect"},
        "value": {"row": 1, "column": 2, "text": "Not Available"},
    }
    bundle = {
        "variant": "Protect",
        "variants": ["Protect", "Advantage"],
        "tables": [{"id": "grid", "cells": cells}],
    }
    assert not variant_proven(s, bundle)
    cells["value"]["column"] = 1
    assert variant_proven(s, bundle)


def test_profile_turn_trace_keeps_each_plan_and_its_deciding_check():
    from apps.adviser_v2.management.commands.run_guided_profiles import turn_groups

    data = {
        "cards": [
            {
                "plan_id": "p",
                "variant": "Gold",
                "insurer": "Insurer",
                "name": "Plan",
                "card_version": "v",
            }
        ],
        "state": {
            "fit_groups": {
                "fits": [],
                "unresolved": [
                    {
                        "plan_id": "p",
                        "hard_limits": [
                            {"field": "age", "status": "fits"},
                            {"field": "family", "status": "unresolved", "citations": []},
                        ],
                        "other_needs": [],
                    }
                ],
                "doesnt_fit": [],
            }
        },
    }
    trace = turn_groups(data)
    assert trace["unresolved"][0]["policy_version_id"] == "p"
    assert trace["unresolved"][0]["variant"] == "Gold"
    assert trace["unresolved"][0]["deciding_checks"] == [
        {"field": "family", "status": "unresolved", "citations": []}
    ]


def test_operative_per_person_and_floater_headers_preserve_both_bases():
    s = statement(
        "Sum Insured on Individual Basis: Limit per person, per Policy Period for each treatment / procedure\nSum Insured on Floater Basis: Limit per Policy Period for each treatment / procedure Rs."
    )
    assert project("coverage_basis", [s], "Default")[0]["value"] == "individual|floater"
