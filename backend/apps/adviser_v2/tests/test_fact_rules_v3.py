from dataclasses import replace

import pytest

from apps.adviser_v2.demo.card_assembly import PacketLabels, assemble
from apps.adviser_v2.demo.card_clauses import clause_bounds
from apps.adviser_v2.demo.contracts import DraftQuote, DraftUnit, Statement
from apps.adviser_v2.demo.fact_rules_v6 import clauses, project, scope
from apps.adviser_v2.tests.test_demo_contracts import citation, packet


def statement(raw):
    return Statement(text=raw, citations=[citation(raw)]).model_dump()


@pytest.mark.parametrize(
    ("field", "raw"),
    [
        (
            "maternity",
            "Parenthood add-on: Maternity expenses are covered on payment of additional premium.",
        ),
        ("opd", "Optima Wellbeing add-on: Outpatient consultations are covered."),
        ("maternity", "Fetal Flourish rider: Delivery expenses are payable."),
    ],
)
def test_riders_are_separate_and_never_base(field, raw):
    s = statement(raw)
    assert scope(s, field, {"sections": []}) == "optional, extra premium"
    base, optional, _ = clauses({"answer": {"statements": [s]}}, field, {"sections": []})
    assert not base and len(optional) == 1
    assert optional[0]["citations"] == s["citations"]
    assert optional[0]["text"] == raw
    assert optional[0]["conditions"] == s["conditions"]


def test_health_check_vouchers_do_not_establish_opd():
    s = statement("OPD health-check vouchers are available for preventive health checks.")
    assert scope(s, "opd", {"sections": []}) == "not_opd"
    assert clauses({"answer": {"statements": [s]}}, "opd", {"sections": []})[0] == []


@pytest.mark.parametrize(
    ("field", "raw", "kind", "value"),
    [
        (
            "ped_waiting",
            "Pre-existing Diseases: Expenses shall be excluded until the expiry of 36 months of continuous coverage.",
            "maximum",
            "36",
        ),
        (
            "specified_waiting",
            "Specified Disease waiting period of 24 months applies.",
            "maximum",
            "24",
        ),
        ("renewal_age", "This policy offers lifetime renewal.", "renewal", "lifetime"),
        (
            "coverage_basis",
            "The policy is available on individual and family floater basis.",
            "basis",
            "individual|floater",
        ),
        (
            "copay",
            "Co-payment of 10% applies for Insured Persons whose age at entry is 61 years and above.",
            "maximum",
            "10",
        ),
        ("room_limit", "Room rent is limited to a single private room.", "room", "single_private"),
        ("deductible", "The deductible is Rs. 50,000 per policy year.", "maximum", "50000"),
        ("maternity", "Maternity is not covered.", "coverage", "not_covered"),
        ("maternity", "Maternity expenses are payable up to Rs. 50,000.", "coverage", "covered"),
    ],
)
def test_numbers_and_keywords_come_from_the_cited_clause(field, raw, kind, value):
    rules = project(field, [statement(raw)], "Default")
    assert any(r["kind"] == kind and r["value"] == value for r in rules)
    assert all(r["printed"] in raw and r["citations"][0]["quote"] == raw for r in rules)


def test_age_choices_family_bonus_and_conditional_copay():
    age = project(
        "entry_age", [statement("Adults aged 18 years to 65 years are eligible.")], "Default"
    )[0]
    assert (age["minimum"], age["maximum"], age["minimum_unit"], age["maximum_unit"]) == (
        18,
        65,
        "years",
        "years",
    )
    choices = project(
        "sum_insured",
        [statement("Sum Insured Options: Rs.5,00,000/-, Rs.10,00,000/- and Rs.25,00,000/-.")],
        "Default",
    )[0]
    assert choices["choices"] == [500000, 1000000, 2500000]
    family = project(
        "family",
        [
            statement(
                "A family floater can cover a maximum of 2 adults and 3 dependent children: self, spouse and children."
            )
        ],
        "Default",
    )[0]
    assert (
        family["maximum_adults"] == 2
        and family["maximum_children"] == 3
        and family["dependent_children"]
    )
    bonus = project(
        "no_claim_bonus",
        [statement("No claim bonus increases by 20% each year up to a maximum of 100%.")],
        "Default",
    )[0]
    assert bonus["value"] == "20" and bonus["cap_percent"] == "100"
    copay = project(
        "copay",
        [
            statement(
                "Co-payment of 10% applies for Insured Persons whose age at entry is 61 years and above."
            )
        ],
        "Default",
    )[0]
    assert copay["guards"][0]["value"] == 61


def test_missing_evidence_never_becomes_not_covered_or_executable():
    assert (
        project(
            "ped_waiting", [statement("Waiting period details are in your schedule.")], "Default"
        )
        == []
    )
    assert (
        project(
            "opd",
            [
                statement(
                    "Outpatient cover excludes cosmetic consultations but covers other treatment."
                )
            ],
            "Default",
        )
        == []
    )
    assert clauses({"status": "not_found"}, "opd", {"sections": []}) == ([], [], [])


def test_governing_heading_prevents_previous_benefit_and_header_contamination():
    raw = "Note: Only restored cover is available.\n14. Outpatient Treatment:\nOutpatient consultations are covered. Only at network hospitals.\n15. Maternity:\nMaternity is excluded."
    start = raw.index("Outpatient consultations")
    a, b = clause_bounds(raw, start, start + len("Outpatient consultations are covered."))
    assert "restored" not in raw[a:b] and "Maternity" not in raw[a:b]
    assert "Only at network hospitals." in raw[a:b]
    raw = "STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS\n14. Outpatient Treatment:\nOutpatient consultations are covered."
    p = packet(raw)
    segment = replace(p.sections[0].segments[0], document_start=0, document_end=len(raw))
    p = replace(p, sections=(replace(p.sections[0], segments=(segment,)),))
    s, _ = assemble(
        DraftUnit(
            benefit=[DraftQuote(passage="P1", quote="Outpatient consultations are covered.")]
        ),
        PacketLabels(p),
        p,
        list(p.sections),
    )
    assert "POLICY WORDINGS" not in s.text and "Outpatient consultations are covered." in s.text


def test_projection_rejects_riders_without_relying_on_the_caller():
    assert (
        project("maternity", [statement("Optional maternity cover pays Rs. 50,000.")], "Default")
        == []
    )


def test_bonus_cap_is_not_misread_as_annual_increment():
    assert (
        project("no_claim_bonus", [statement("The maximum no claim bonus is 100%.")], "Default")
        == []
    )
    rule = project(
        "no_claim_bonus",
        [statement("Maximum 100% no claim bonus; increases by 20% per claim-free year.")],
        "Default",
    )[0]
    assert rule["value"] == "20" and rule["cap_percent"] == "100"


def test_temporary_exclusion_does_not_establish_permanent_noncoverage():
    assert (
        project(
            "maternity",
            [statement("Maternity is not covered until 24 months have elapsed.")],
            "Default",
        )
        == []
    )
    assert (
        project(
            "coverage_basis",
            [statement("Individual cover is not available under this policy.")],
            "Default",
        )
        == []
    )


def test_sum_insured_range_and_conditional_choices_are_not_exhaustive():
    assert (
        project(
            "sum_insured",
            [statement("Sum insured options from Rs. 5 lakh to Rs. 50 lakh.")],
            "Default",
        )
        == []
    )
    rule = project(
        "sum_insured",
        [statement("Sum insured options: Rs. 5 lakh and Rs. 10 lakh, only for age 18 to 60.")],
        "Default",
    )[0]
    assert rule["restricted_scope"] and not rule["exhaustive"]


def test_same_value_with_different_conditions_is_not_collapsed():
    rules = project(
        "maternity",
        [
            statement("Maternity expenses covered up to Rs. 20,000."),
            statement("Maternity expenses covered up to Rs. 50,000."),
        ],
        "Default",
    )
    assert len(rules) == 2


def test_room_suite_exception_is_preserved():
    rule = project("room_limit", [statement("Any room except suite is covered.")], "Default")[0]
    assert rule["value"] == "any_room_except_suite"


def test_closed_rule_schema_rejects_impossible_bounds():
    from pydantic import ValidationError

    from apps.adviser_v2.demo.fact_rule_contracts import FactRule

    rule = project(
        "entry_age", [statement("Adults aged 18 years to 65 years are eligible.")], "Default"
    )[0]
    assert FactRule.model_validate(rule).maximum == 65
    with pytest.raises(ValidationError):
        FactRule.model_validate({**rule, "maximum": 400})
    with pytest.raises(ValidationError):
        FactRule.model_validate({**rule, "inferred_fact": True})


def test_typed_age_inclusive_boundaries_preserve_printed_units():
    from apps.adviser_v2.demo.conversation_contracts import ChatPerson
    from apps.adviser_v2.demo.typed_matching import age_result

    rule = project(
        "entry_age", [statement("Adults aged 18 years to 65 years are eligible.")], "Default"
    )[0]
    assert age_result(ChatPerson(id="self", relationship="self", age=18), rule) == "fits"
    assert age_result(ChatPerson(id="self", relationship="self", age=65), rule) == "fits"
    assert age_result(ChatPerson(id="self", relationship="self", age=66), rule) == "doesnt_fit"
    assert age_result(ChatPerson(id="self", relationship="self", age=None), rule) == "unresolved"
    infant = project(
        "entry_age", [statement("Children aged 90 days to 25 years are eligible.")], "Default"
    )[0]
    assert (
        age_result(ChatPerson(id="child", relationship="child", age=89, age_unit="days"), infant)
        == "doesnt_fit"
    )
    assert (
        age_result(ChatPerson(id="child", relationship="child", age=3, age_unit="months"), infant)
        == "unresolved"
    )


def test_conditional_copay_does_not_apply_to_an_unknown_age():
    from apps.adviser_v2.demo.chat_rules import requirement_result
    from apps.adviser_v2.demo.conversation_contracts import (
        ChatPerson,
        IncompleteProfile,
        Requirement,
    )

    rules = project(
        "copay",
        [
            statement(
                "Co-payment of 10% applies for Insured Persons whose age at entry is 61 years and above."
            )
        ],
        "Default",
    )
    card = {"variant": "Default", "executable_rules": rules}
    need = Requirement(
        field="copay", original_text="No co-pay", strength="must_have", value="at_most:0:percent"
    )
    p = IncompleteProfile(people=[ChatPerson(id="self", relationship="self", age=None)])
    assert requirement_result(card, need, p)["status"] == "unresolved"
    p.people[0].age = 61
    assert requirement_result(card, need, p)["status"] == "doesnt_fit"
    p.people[0].age = 60
    assert requirement_result(card, need, p)["status"] == "unresolved"


def test_adjacent_age_ranges_keep_their_person_applicability():
    rules = project(
        "entry_age",
        [
            statement(
                "Adults aged 18 years to 65 years; children aged 90 days to 25 years are eligible."
            )
        ],
        "Default",
    )
    assert [(r["relationship"], r["minimum"], r["maximum"]) for r in rules] == [
        ("adult", 18, 65),
        ("child", 90, 25),
    ]


def test_parents_in_law_do_not_imply_parents_are_allowed():
    rules = project(
        "family",
        [
            statement(
                "The floater covers a maximum of 2 adults and 3 dependent children: self, spouse, parents-in-law and children."
            )
        ],
        "Default",
    )
    assert "parent_in_law" in rules[0]["relationships"]
    assert "parent" not in rules[0]["relationships"]


def test_standard_maternity_exclusion_code_is_not_positive_cover():
    rules = project(
        "maternity",
        [
            statement(
                "Maternity: Code – Excl18. Medical treatment expenses traceable to childbirth except ectopic pregnancy."
            )
        ],
        "Default",
    )
    assert rules[0]["value"] == "not_covered"


def test_renewal_field_never_executes_neighboring_entry_age_ranges():
    rules = project(
        "renewal_age",
        [statement("Adults aged 18 years to 65 years; Renewal age – Lifetime.")],
        "Default",
    )
    assert {r["kind"] for r in rules} == {"renewal"}


def test_incidental_optional_conditions_do_not_reclassify_base_clause():
    s = statement("This policy offers lifetime renewal.")
    s["conditions"] = [
        {
            "text": "A policyholder may also choose an optional cover.",
            "citations": [
                citation("A policyholder may also choose an optional cover.").model_dump()
            ],
        }
    ]
    assert scope(s, "renewal_age", {"sections": []}) == "base"


def test_rider_scope_is_kept_before_trimming_a_maternity_exclusion():
    raw = "Fetal Flourish rider: Delivery expenses are excluded.\nMaternity: Code Excl18\nMedical treatment expenses traceable to childbirth."
    s = statement(raw)
    base, optional, _ = clauses({"answer": {"statements": [s]}}, "maternity", {"sections": []})
    assert not base and optional[0]["citations"] == s["citations"]


def test_repeated_identical_waiting_rules_keep_both_sources_once():
    rules = project(
        "ped_waiting",
        [
            statement("Pre-existing disease waiting period of 36 months applies."),
            statement(
                "Pre-existing diseases are excluded until the expiry of 36 months of continuous coverage."
            ),
        ],
        "Default",
    )
    assert len(rules) == 1 and rules[0]["value"] == "36" and len(rules[0]["citations"]) == 2


def test_trimmed_field_row_keeps_exact_offsets_with_leading_whitespace():
    from apps.adviser_v2.demo.fact_projection import clauses
    from apps.adviser_v2.demo.quotations import locate

    raw = "  Introductory information.\nPolicy Renewal age – Lifetime\nOther information."
    s = statement(raw)
    bundle = {
        "sections": [
            {"id": "s", "role": "policy_wording", "segments": [{"page_id": "p", "text": raw}]}
        ]
    }
    base, _, _ = clauses({"answer": {"statements": [s]}}, "renewal_age", bundle)
    cite = base[0]["citations"][0]
    assert cite["quote"] == "Policy Renewal age – Lifetime"
    start, end = locate(raw, cite["quote"], cite["occurrence"])
    assert raw[start:end] == cite["quote"]


def test_selectable_sum_list_does_not_include_neighboring_age_or_benefit_limits():
    from apps.adviser_v2.demo.fact_projection import project

    raw = "Dependent children aged 3 months to 30 years.\nWhat are the Sum Insured options available under the policy?\n5 Lakh,7.5 Lakh,10 Lakh,1 Cr,2 Cr\n➢ What type of plans are available?"
    r = project("sum_insured", [statement(raw)], "Default")[0]
    assert r["choices"] == [500000, 750000, 1000000, 10000000, 20000000]
    assert (
        project(
            "sum_insured",
            [
                statement(
                    "Preventive health check: Base Sum Insured 5 lakh; limit of cover Rs. 1500."
                )
            ],
            "Default",
        )
        == []
    )


def test_person_bounds_never_cross_bullets_or_following_child_sentence():
    from apps.adviser_v2.demo.fact_projection import project

    raw = "Eligibility: ▪ The minimum entry age for an adult is 18 years and there is no limit on maximum entry age. ▪ The minimum entry age for a dependent child is 91 days and maximum entry age is 25 years."
    rules = project("entry_age", [statement(raw)], "Default")
    assert {(r["relationship"], r["minimum"], r["maximum"]) for r in rules} == {
        ("adult", 18, None),
        ("child", 91, 25),
    }
    raw = "This insurance is available to persons between the age of 18 years and 65 years. Children from 3 months up to 25 years can be covered provided both parents are covered."
    rules = project("entry_age", [statement(raw)], "Default")
    assert len(rules) == 1 and rules[0]["relationship"] == "person"
    raw = "Children between ages of 91 days to 5 years can be insured only under a floater. Maximum age for dependent children is 30 years."
    assert not project("entry_age", [statement(raw)], "Default")
