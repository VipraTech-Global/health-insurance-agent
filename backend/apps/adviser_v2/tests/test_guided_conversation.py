from types import SimpleNamespace

import pytest

from apps.adviser_v2.demo.chat_rules import differentiator, fit_groups
from apps.adviser_v2.demo.conversation import interpret, next_question, question, transition
from apps.adviser_v2.demo.conversation_contracts import (
    ChatPerson,
    ChatState,
    IncompleteProfile,
    ProposedChanges,
    Requirement,
)
from apps.adviser_v2.tests.test_demo_contracts import card, citation


def cards(n=5):
    return [card(str(i), insurer=f"Insurer {n - i}").model_dump() for i in range(n)]


def complete():
    return ChatState(
        profile=IncompleteProfile(
            people=[ChatPerson(id="me", relationship="self", age=35)],
            city="Pune",
            sum_insured=500000,
            annual_budget=30000,
            plan_type="medical_indemnity",
        ),
        skipped=["health_details"],
        answered=["needs"],
    )


class NoCalls:
    def call(self, **kwargs):
        raise AssertionError("Fixed question phrasing must not call AI")


def test_multidetail_skips_future_questions_and_fixed_stages_make_no_calls():
    state = next_question(ChatState(), cards(), relay=NoCalls())
    assert state.pending.field == "people"
    assert next_question(state, cards()).question_count == 1
    state = transition(
        state,
        ProposedChanges(
            people=[
                ChatPerson(id="self", relationship="self", age=35),
                ChatPerson(id="spouse", relationship="spouse"),
            ],
            city="Pune",
            sum_insured=500000,
            annual_budget=30000,
            plan_type="medical_indemnity",
            requirements=[Requirement(field="maternity", original_text="Maternity")],
        ),
        cards(),
        relay=NoCalls(),
    )
    assert state.pending.field == "age:spouse"
    state = transition(
        state,
        ProposedChanges(people=[ChatPerson(id="spouse", relationship="spouse", age=33)]),
        cards(),
        relay=NoCalls(),
    )
    assert state.pending.field == "health_details"
    state = transition(state, ProposedChanges(skip=True), cards(), relay=NoCalls())
    assert state.stage == "requirements" and state.pending.template == "strength"
    state = transition(state, ProposedChanges(affirmative=True), cards(), relay=NoCalls())
    assert state.stage == "narrowing" and state.profile.requirements[0].strength == "must_have"
    assert state.stop_reason == "no_supported_question"


def test_ambiguity_preserves_facts_corrections_and_skip_does_not_erase():
    state = next_question(ChatState(), cards())
    state = transition(state, ProposedChanges(city="Pune"), cards())
    state = transition(state, ProposedChanges(city="Mumbai"), cards())
    assert state.profile.city == "Pune" and state.pending.template == "clarify"
    state = transition(state, ProposedChanges(city="Mumbai", correction=True), cards())
    assert state.profile.city == "Mumbai"
    state.profile.people = [ChatPerson(id="self", relationship="self", age=35)]
    state = transition(state, ProposedChanges(skip=True), cards())
    assert state.profile.people[0].age == 35


def test_no_preference_does_not_assign_type_and_customer_stop_has_no_question():
    state = complete()
    state.profile.plan_type = "unresolved"
    state.answered = []
    state = next_question(state, cards())
    state = transition(state, ProposedChanges(no_preference=True), cards())
    assert state.pending.field == "cover_need" and state.profile.plan_type == "unresolved"
    state = transition(state, ProposedChanges(stop=True), cards())
    assert state.stage == "stopped" and state.pending is None and "?" not in state.message
    assert next_question(state, cards()).question_count == state.question_count


def test_policy_question_is_not_requirement_and_retains_stage():
    state = next_question(ChatState(), cards(6))
    state = transition(
        state,
        ProposedChanges(
            policy_question="Is OPD covered?",
            requirements=[Requirement(field="opd", original_text="OPD")],
        ),
        cards(6),
    )
    assert state.pending.template == "select" and state.policy_question == "Is OPD covered?"
    assert not state.profile.requirements and state.interrupted.field == "people"
    state = transition(state, ProposedChanges(selected_plans=["0", "1"]), cards(6))
    assert state.pending.field == "people"


def with_rule(c, field, value):
    c.setdefault("executable_rules", []).append(
        {"field": field, "kind": "coverage", "value": value, "citations": [citation().model_dump()]}
    )
    return c


def test_unknown_never_excludes_nice_never_excludes_must_needs_cited_conflict():
    source = cards(3)
    with_rule(source[0], "opd", "covered")
    with_rule(source[1], "opd", "not_covered")
    state = complete()
    state.profile.requirements = [
        Requirement(field="opd", original_text="OPD", strength="nice_to_have")
    ]
    groups = fit_groups(source, state.profile)
    assert not groups["doesnt_fit"]
    state.profile.requirements[0].strength = "must_have"
    groups = fit_groups(source, state.profile)
    assert [r["plan_id"] for r in groups["doesnt_fit"]] == ["1"]
    assert [r["plan_id"] for r in groups["unresolved"]] == ["2"]
    assert [r["plan_id"] for r in groups["fits"]] == ["0"]


def test_question_selection_is_insurer_independent_and_skip_suppresses():
    source = cards()
    for i, c in enumerate(source):
        for field in ("opd", "maternity"):
            if i < 4:
                with_rule(c, field, "covered" if i % 2 else "not_covered")
    state = complete()
    state.fit_groups = fit_groups(source, state.profile)
    first = differentiator(source, state.fit_groups, set())
    assert first["field"] == "maternity" and first["known"] == 4 and first["remaining"] == 5
    for c in source:
        c["insurer"] = "changed"
    assert differentiator(list(reversed(source)), state.fit_groups, set()) == first
    state = next_question(state, source)
    assert state.pending.field == "maternity" and "uncertain evidence will remain" in state.message
    state = transition(state, ProposedChanges(skip=True), source)
    assert state.pending.field == "opd" and not state.profile.requirements


def test_compound_question_gets_one_rewrite_then_fixed_template():
    class Bad:
        calls = 0

        def call(self, **kwargs):
            self.calls += 1
            return SimpleNamespace(
                value={"intent_id": "wrong", "question": "What are your age and city?"},
                model="test",
            )

    relay = Bad()
    state = complete()
    state.stage = "narrowing"
    question(state, "narrow", "opd", relay=relay)
    assert (
        relay.calls == 2 and state.pending.text == "Should I treat outpatient cover as a must-have?"
    )
    assert state.question_count == 1


@pytest.mark.parametrize(
    ("n", "stop"),
    [
        (0, "none_remain"),
        (1, "one_remains"),
        (2, "two_or_three_remain"),
        (3, "two_or_three_remain"),
        (5, "no_supported_question"),
    ],
)
def test_stop_conditions_and_counts(n, stop):
    state = complete()
    state.fit_groups = fit_groups(cards(n), state.profile)
    state = next_question(state, cards(n), relay=NoCalls())
    assert state.stop_reason == stop and state.message.count("?") == 1
    if n in (2, 3):
        assert len(state.selected_plans) == n


def test_restoration_retains_conflict_and_mixed_selection_requires_decision():
    source = cards(3)
    state = complete()
    state.profile.people[0].age = 70
    state = transition(state, ProposedChanges(restored_plans=["0"]), source)
    assert len(state.fit_groups["doesnt_fit"]) == 3 and state.restored_plans == ["0"]
    source[1]["plan_type"] = "top_up"
    state = transition(state, ProposedChanges(selected_plans=["0", "1"]), source)
    assert state.pending.template == "mixed"


def test_chips_submit_exact_visible_text_without_ai():
    source = cards()
    state = ChatState()
    changes, model = interpret("Compare Insurer 5 — 0 (Default)", state, source, NoCalls())
    assert changes.selected_plans == ["0"] and model is None
    changes, _ = interpret("Stop", state, source, NoCalls())
    assert changes.stop
