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
            coverage_basis="floater",
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
    # The open options are shown before the first "what matters" question.
    assert state.stage == "requirements" and state.pending.template == "strength"
    assert state.message.startswith("Based on your details")
    state = transition(state, ProposedChanges(affirmative=True), cards(), relay=NoCalls())
    assert state.pending.field == "health_details"
    assert state.profile.requirements[0].strength == "must_have"
    state = transition(state, ProposedChanges(skip=True), cards(), relay=NoCalls())
    assert state.stage == "narrowing" and state.stop_reason == "two_or_three_remain"


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
    source = cards()
    source[0]["plan_type"] = "top_up"
    state = complete()
    state.profile.plan_type = "unresolved"
    state.answered = []
    state = next_question(state, source)
    assert state.pending.field == "plan_type"
    state = transition(state, ProposedChanges(no_preference=True), source)
    assert state.pending.field != "cover_need" and state.profile.plan_type == "unresolved"
    assert state.profile.any_type
    assert not [
        r
        for group in state.fit_groups.values()
        for result in group
        for r in result["hard_limits"]
        if r["field"] == "plan_type"
    ]
    state = transition(state, ProposedChanges(stop=True), source)
    assert state.stage == "stopped" and state.pending is None and "?" not in state.message
    assert next_question(state, source).question_count == state.question_count


def test_single_type_catalogue_asks_no_cover_type_and_type_is_no_limit():
    state = complete()
    state.profile.plan_type = "unresolved"
    state.answered = []
    state.fit_groups = fit_groups(cards(), state.profile)
    state = next_question(state, cards())
    assert state.pending.field == "needs" and len(state.fit_groups["fits"]) == 5


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
    # More than five plans remain: the question is held, never a request to pick.
    assert state.pending.field == "people" and state.policy_question == "Is OPD covered?"
    assert state.policy_deferred and "kept your question" in state.message
    assert not state.profile.requirements and state.interrupted.field == "people"
    state = transition(state, ProposedChanges(selected_plans=["0", "1"]), cards(6))
    assert state.pending.field == "people" and not state.policy_deferred
    assert state.selected_plans == ["0", "1"]


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
    source = cards(6)
    for i, c in enumerate(source):
        for field in ("opd", "maternity"):
            if i < 4:
                with_rule(c, field, "covered" if i % 2 else "not_covered")
    state = complete()
    state.fit_groups = fit_groups(source, state.profile)
    first = differentiator(source, state.fit_groups, set())
    assert first["field"] == "maternity" and first["known"] == 4 and first["remaining"] == 6
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
        (5, "two_or_three_remain"),
        (6, "no_supported_question"),
    ],
)
def test_stop_conditions_and_counts(n, stop):
    state = complete()
    state.fit_groups = fit_groups(cards(n), state.profile)
    state = next_question(state, cards(n), relay=NoCalls())
    assert state.stop_reason == stop and state.message.count("?") == 1
    if 2 <= n <= 5:
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


def test_policy_narrow_first_retains_question_and_multiple_unsupported_needs():
    state = next_question(ChatState(), cards(6))
    state = transition(state, ProposedChanges(policy_question="What is covered?"), cards(6))
    state = transition(state, ProposedChanges(narrow_first=True), cards(6))
    assert state.policy_question == "What is covered?" and state.policy_deferred
    assert state.pending.field == "people"
    state = transition(
        state,
        ProposedChanges(
            requirements=[
                Requirement(
                    field="other", original_text="Nutrition consultation", strength="must_have"
                ),
                Requirement(field="other", original_text="Gym membership", strength="nice_to_have"),
            ]
        ),
        cards(6),
    )
    assert len(state.profile.requirements) == 2
    assert len({r.field for r in state.profile.requirements}) == 2


def test_partial_card_does_not_make_an_independently_complete_profile_unresolved():
    source = cards(1)
    source[0]["status"] = "partial"
    assert len(fit_groups(source, complete().profile)["fits"]) == 1


def test_question_labels_cannot_turn_one_field_into_a_compound_request():
    state = ChatState(
        profile=IncompleteProfile(people=[ChatPerson(id="age and city?", relationship="child")])
    )
    state = next_question(state, cards())
    assert state.pending.text == "What is the age of your child?"
    assert state.pending.person_id == "age and city?"
    state.pending = None
    state = next_question(state, cards(), ambiguity="age and city?")
    assert state.pending.text == "Could you clarify that detail?"


def test_explicit_person_removal_is_a_chat_correction_and_skip_does_not_remove():
    state = complete()
    state.profile.people.append(ChatPerson(id="parent", relationship="parent", age=72))
    unchanged = transition(state, ProposedChanges(removed_people=["parent"]), cards())
    assert len(unchanged.profile.people) == 2
    corrected = transition(
        state, ProposedChanges(removed_people=["parent"], correction=True), cards()
    )
    assert [p.id for p in corrected.profile.people] == ["me"]


def test_cover_type_detail_does_not_answer_needs_and_registry_alias_is_supported():
    from apps.adviser_v2.demo.conversation import merge

    state = complete()
    state.answered = []
    question(state, "cover_need")
    merge(
        state,
        ProposedChanges(
            plan_type="medical_indemnity",
            coverage_basis="floater",
            requirements=[
                Requirement(
                    field="hospital_expenses",
                    original_text="Hospital expenses",
                    strength="must_have",
                )
            ],
        ),
    )
    assert not state.profile.requirements and "needs" not in state.answered
    state.pending = None
    next_question(state, cards(), relay=NoCalls())
    assert state.pending.field == "needs"
    merge(
        state,
        ProposedChanges(
            requirements=[
                Requirement(
                    field="maternity coverage",
                    original_text="Maternity cover is a must-have",
                    strength="must_have",
                )
            ]
        ),
    )
    assert state.profile.requirements[0].field == "maternity"


def test_model_cannot_promote_matters_to_must_have_without_customer_strength():
    class Interpreter:
        def call(self, **kwargs):
            assert "needs_registry" in kwargs["messages"][0]["content"]
            return SimpleNamespace(
                model="gpt-5.6-luna",
                value=ProposedChanges(
                    requirements=[
                        Requirement(
                            field="maternity",
                            original_text="Maternity cover is a must-have.",
                            strength="must_have",
                        )
                    ]
                ).model_dump(),
            )

    changes, _ = interpret(
        "Maternity cover matters to me.", complete(), cards(), relay=Interpreter()
    )
    assert changes.requirements[0].strength == "unclassified"
    changes, _ = interpret(
        "Maternity cover is a must-have.", complete(), cards(), relay=Interpreter()
    )
    assert changes.requirements[0].strength == "must_have"
    changes, _ = interpret(
        "Maternity cover is a nice-to-have.", complete(), cards(), relay=Interpreter()
    )
    assert changes.requirements[0].strength == "nice_to_have"


def test_volunteered_health_skip_does_not_skip_pending_family_or_repeat_health():
    class Reply:
        def call(self, **kwargs):
            return SimpleNamespace(
                value=ProposedChanges(skip=True).model_dump(), model="gpt-5.6-luna"
            )

    state = next_question(ChatState(), cards(), relay=NoCalls())
    changes, _ = interpret(
        "Cover me. I prefer to skip the optional health details.", state, cards(), relay=Reply()
    )
    assert changes.skip_health_details and not changes.skip
    state = transition(state, changes, cards(), relay=NoCalls())
    assert "health_details" in state.skipped
    assert "people" not in state.skipped
    assert state.pending.field == "people"


@pytest.mark.parametrize("reply", ["I have health details", "Do not skip health details"])
def test_health_skip_requires_affirmative_customer_words(reply):
    class Reply:
        def call(self, **kwargs):
            return SimpleNamespace(
                value=ProposedChanges(skip_health_details=True).model_dump(), model="gpt-5.6-luna"
            )

    changes, _ = interpret(reply, ChatState(), cards(), relay=Reply())
    assert not changes.skip_health_details


def test_unsure_budget_is_skipped_without_ai_and_never_asked_again():
    state = complete()
    state.profile.annual_budget = None
    state = next_question(state, cards())
    assert state.pending.field == "annual_budget"
    text = "i dont know about that, can you tell me what can i get here?"
    changes, model = interpret(text, state, cards(), NoCalls())
    assert changes.skip and model is None and not changes.policy_question
    state = transition(state, changes, cards(), relay=NoCalls())
    assert "annual_budget" in state.skipped and state.pending.field != "annual_budget"
    assert "plans" in state.message and "Which plans would you like" not in state.message


def test_unsure_budget_with_an_amount_is_left_to_interpretation():
    class Amount:
        def call(self, **kwargs):
            return SimpleNamespace(value={"annual_budget": 20000}, model="test")

    state = complete()
    state.profile.annual_budget = None
    state = next_question(state, cards())
    changes, _ = interpret("not sure, maybe 20k", state, cards(), Amount())
    assert changes.annual_budget == 20000 and not changes.skip


def test_options_summary_never_claims_fit_when_nothing_is_confirmed():
    source = cards(6)
    state = complete()
    state.answered = []
    state.fit_groups = {
        "fits": [],
        "unresolved": [
            {
                "plan_id": c["plan_id"],
                "hard_limits": [
                    {"field": "family", "status": "unresolved", "citations": []},
                    {"field": "geography", "status": "unresolved", "citations": []},
                ],
            }
            for c in source
        ],
        "doesnt_fit": [],
    }
    from apps.adviser_v2.demo.conversation import options_summary

    text = options_summary(state, source)
    assert "6 plans are open to you" in text and "None is ruled out" in text
    assert "who can be covered together" in text and "match every" not in text
    assert text.index("Insurer 1") < text.index("Insurer 6")


def test_unnarrowable_policy_question_is_answered_in_alphabetical_fives():
    source = cards(7)
    state = complete()
    state.fit_groups = fit_groups(source, state.profile)
    state.policy_question = "Is OPD covered?"
    state.policy_deferred = True
    state = next_question(state, source, relay=NoCalls())
    first = state.selected_plans
    assert len(first) == 5 and len(state.batch_queue) == 2 and not state.policy_deferred
    assert "not a ranking" in state.message and "next five" in state.message
    assert {c["insurer"] for c in source if c["plan_id"] in first} == {
        f"Insurer {i}" for i in range(1, 6)
    }
    state.policy_question = None  # submitted by the service
    changes, model = interpret("next five", state, source, NoCalls())
    assert changes.next_batch and model is None
    state = transition(state, changes, source, relay=NoCalls())
    assert len(state.selected_plans) == 2 and not set(state.selected_plans) & set(first)
    assert state.policy_question == "Is OPD covered?" and not state.batch_queue
    assert "last group" in state.message


def test_first_person_reply_means_self_without_ai():
    state = next_question(ChatState(), cards())
    changes, model = interpret("i need the coveer", state, cards(), NoCalls())
    assert model is None and [p.relationship for p in changes.people] == ["self"]
    state = transition(state, changes, cards(), relay=NoCalls())
    assert state.pending.field == "age:self"


class Empty:
    def call(self, **kwargs):
        return SimpleNamespace(value={}, model="test")


@pytest.mark.parametrize("text", ["me and my wife", "me, my wife and our 2 children", "not me"])
def test_family_replies_are_left_to_interpretation(text):
    state = next_question(ChatState(), cards())
    _, model = interpret(text, state, cards(), Empty())
    assert model == "test"


def test_unparsed_reply_is_reasked_with_an_example_not_repeated():
    state = next_question(ChatState(), cards())
    first, count = state.message, state.question_count
    state = transition(state, ProposedChanges(), cards(), relay=NoCalls())
    assert state.pending.field == "people" and state.question_count == count + 1
    assert state.message != first and "I didn’t quite catch that" in state.message
    assert "“just me”" in state.message
    state = transition(
        state,
        ProposedChanges(people=[ChatPerson(id="self", relationship="self")]),
        cards(),
        relay=NoCalls(),
    )
    state = transition(state, ProposedChanges(), cards(), relay=NoCalls())
    assert state.pending.field == "age:self" and "for example “35”" in state.message
    state = transition(
        state, ProposedChanges(people=[ChatPerson(id="self", relationship="self", age=35)]), cards()
    )
    assert state.pending.field == "city" and "catch" not in state.message


class SkipAll:
    def call(self, **kwargs):
        return SimpleNamespace(value=ProposedChanges(skip=True).model_dump(), model="test")


def test_vague_reply_never_skips_who_is_covered():
    state = next_question(ChatState(), cards())
    changes, _ = interpret("hmm", state, cards(), SkipAll())
    assert not changes.skip
    changes, _ = interpret("skip this for now please", state, cards(), SkipAll())
    assert changes.skip


def test_own_age_is_asked_directly():
    state = transition(
        next_question(ChatState(), cards()),
        ProposedChanges(people=[ChatPerson(id="self", relationship="self")]),
        cards(),
    )
    assert state.message == "How old are you?"


def test_basis_is_asked_once_for_a_family_and_parsed_without_ai():
    family = ChatState(
        profile=IncompleteProfile(
            people=[
                ChatPerson(id="self", relationship="self", age=35),
                ChatPerson(id="spouse", relationship="spouse", age=33),
            ],
            city="Pune",
            sum_insured=500000,
            annual_budget=30000,
        )
    )
    state = next_question(family, cards(), relay=NoCalls())
    assert state.pending.field == "coverage_basis" and "family floater" in state.pending.text
    for reply, basis in [
        ("One shared cover", "floater"),
        ("family floater please", "floater"),
        ("separate cover for each", "individual"),
    ]:
        changes, _ = interpret(reply, state, cards(), relay=NoCalls())
        assert changes.coverage_basis == basis
    changes, _ = interpret("not sure", state, cards(), relay=NoCalls())
    assert changes.skip
    after = transition(state, changes, cards(), relay=NoCalls())
    assert after.pending.field != "coverage_basis" and after.profile.coverage_basis is None
    alone = complete()
    alone.profile.plan_type = "unresolved"
    assert next_question(alone, cards(), relay=NoCalls()).pending.field != "coverage_basis"


def test_only_the_india_city_answer_establishes_residence():
    state = next_question(
        ChatState(
            profile=IncompleteProfile(people=[ChatPerson(id="me", relationship="self", age=35)])
        ),
        cards(),
        relay=NoCalls(),
    )
    assert (
        state.pending.field == "city"
        and state.pending.text == "Which city in India do you live in?"
    )
    assert transition(state, ProposedChanges(city="Kota"), cards()).profile.resides_in_india
    abroad = transition(state, ProposedChanges(city="Dubai", outside_india=True), cards())
    assert not abroad.profile.resides_in_india
    assert not transition(
        state, ProposedChanges(city="Austin, Texas"), cards()
    ).profile.resides_in_india
    volunteered = transition(
        next_question(ChatState(), cards()),
        ProposedChanges(people=[ChatPerson(id="me", relationship="self")], city="Kota"),
        cards(),
    )
    assert volunteered.profile.city == "Kota" and not volunteered.profile.resides_in_india
