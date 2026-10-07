"""Replays of customer turns that went wrong in a real demo conversation."""

from types import SimpleNamespace

from apps.adviser_v2.demo.chat_rules import fit_groups
from apps.adviser_v2.demo.chat_services import suggestions, turn_blocks
from apps.adviser_v2.demo.conversation import interpret, next_question, summary, transition
from apps.adviser_v2.demo.conversation_contracts import ChatState, ProposedChanges, Requirement
from apps.adviser_v2.tests.test_demo_contracts import citation
from apps.adviser_v2.tests.test_guided_conversation import NoCalls, cards, complete, with_rule


class Returns:
    """A relay stub returning fixed proposed changes."""

    def __init__(self, **value):
        self.value = value

    def call(self, **kwargs):
        return SimpleNamespace(value=ProposedChanges(**self.value).model_dump(), model="test")


def asked(state, field, source):
    state.fit_groups = fit_groups(source, state.profile)
    setattr(state.profile, field, None)
    state = next_question(state, source, relay=NoCalls())
    assert state.pending.field == field
    return state


def say(state, text, source, relay=None):
    changes, _ = interpret(text, state, source, relay or NoCalls())
    return transition(state, changes, source, relay=relay or NoCalls())


def test_asking_for_sum_insured_options_keeps_the_question_open():
    source = cards()
    for c in source:
        c["executable_rules"] = [
            {
                "field": "sum_insured",
                "choices": [500000, 1000000],
                "citations": [citation().model_dump()],
            }
        ]
    state = asked(complete(), "sum_insured", source)
    state = say(state, "what are the options?", source)
    assert state.pending.field == "sum_insured" and "₹5 lakh, ₹10 lakh" in state.message
    assert "didn’t quite catch" not in state.message
    assert suggestions(state)[:3] == ["5 lakh", "10 lakh", "25 lakh"]


def test_show_me_whats_open_lists_plans_instead_of_reasking_the_budget():
    source = cards(7)
    state = asked(complete(), "annual_budget", source)
    state = say(state, "show me whats open to me", source)
    assert "didn’t quite catch" not in state.message
    assert len(state.shown_plans) == 5 and "7 plans are open to you" in state.message
    assert "annual_budget" in state.skipped


def test_show_all_insurers_lists_plans():
    source = cards(3)
    state = complete()
    state.answered = []
    state.fit_groups = fit_groups(source, state.profile)
    state = next_question(state, source, relay=NoCalls())
    state = say(state, "Show all insurers", source)
    assert len(state.shown_plans) == 3 and state.pending.template != "needs"


def test_matters_most_is_a_confirmed_must_have_without_a_strength_question():
    source = cards(3)
    state = complete()
    state.answered = ["options_shown"]
    state.fit_groups = fit_groups(source, state.profile)
    state = next_question(state, source, relay=NoCalls())
    assert state.pending.template == "needs"
    # The model may leave the strength open; "matters most" decides it.
    opd = Returns(
        requirements=[
            Requirement(field="opd", original_text="OPD matter most", strength="unclassified")
        ]
    )
    state = say(state, "OPD matter most", source, opd)
    assert [(r.field, r.strength) for r in state.profile.requirements] == [("opd", "must_have")]
    assert state.pending.template != "strength"
    assert state.message.startswith("Noted: outpatient cover is a must-have.")
    assert "Outpatient cover — must-have" in state.understanding


def test_a_vague_limit_is_clarified_not_stored_as_an_uncheckable_must_have():
    source = cards(3)
    state = complete()
    state.answered = ["options_shown", "needs"]
    state.fit_groups = fit_groups(source, state.profile)
    state = next_question(state, source, relay=NoCalls())
    vague = Returns(
        requirements=[
            Requirement(field="limits", original_text="limit do matter", strength="must_have")
        ]
    )
    state = say(state, "limit do matter", source, vague)
    assert state.profile.requirements == [] and state.pending.template == "which_limit"
    assert "room rent, co-pay" in state.message
    # Every plan stays open: a need that can't be checked never filters.
    assert len(state.fit_groups["fits"]) == 3


def test_an_uncheckable_must_have_never_makes_every_plan_unconfirmed():
    source = cards(3)
    state = complete()
    state.profile.requirements = [
        Requirement(field="unsupported:abc", original_text="good claim ratio", strength="must_have")
    ]
    groups = fit_groups(source, state.profile)
    assert len(groups["fits"]) == 3 and not groups["unresolved"]


def test_top_three_is_sorted_by_the_customers_needs_and_honours_the_count():
    source = cards(7)
    for i, c in enumerate(source):
        c["name"] = f"Secure {i}"  # "plan" in the request names no plan
    for i in (1, 3):
        with_rule(source[i], "opd", "covered")
    state = complete()
    state.profile.requirements = [
        Requirement(field="opd", original_text="OPD", strength="must_have")
    ]
    state.answered = ["options_shown", "needs"]
    state.fit_groups = fit_groups(source, state.profile)
    state = next_question(state, source, relay=NoCalls())
    state = say(state, "what is the best plan for me,suggest top 3 plans for me", source)
    assert len(state.shown_plans) == 3 and set(state.shown_plans[:2]) == {"1", "3"}
    assert "here are the first 3" in state.message and "I don’t pick" not in state.message
    assert "isn’t a ranking" in state.message and "best" not in state.message.casefold()
    block = turn_blocks(state, [], source)[0]
    assert block["needs"] == [{"field": "opd", "label": "Outpatient cover"}]
    assert [r["needs"][0]["status"] for r in block["plans"]][:2] == ["fits", "fits"]


def test_rate_and_limit_of_these_plans_stays_on_the_shown_plans():
    source = cards(7)
    state = complete()
    state.profile.sum_insured = None
    state.skipped = ["sum_insured", "health_details"]
    for c in source[:3]:
        with_rule(c, "opd", "covered")
    state.answered = ["options_shown", "needs"]
    state.fit_groups = fit_groups(source, state.profile)
    state.plans_requested = True
    state.list_count = 3
    state = next_question(state, source, relay=NoCalls())
    shown = list(state.last_shown or state.shown_plans)
    state.last_shown = shown
    assert len(shown) == 3
    state = say(state, "can you also share the annual rate and limit of these plans", source)
    assert state.pending.field == "price_sum_insured"
    state = transition(state, ProposedChanges(sum_insured=500000), source, relay=NoCalls())
    assert "any of these 3 plans" in state.message and "see more" not in state.message
    assert state.pending.template == "limit_question"


def test_summary_reads_plainly():
    state = complete()
    state.profile.sum_insured = 1000000
    state.profile.health_details = "none"
    state.profile.requirements = [
        Requirement(field="opd", original_text="OPD", strength="must_have"),
        Requirement(field="copay", original_text="co-pay", strength="unclassified"),
    ]
    lines = summary(state.profile)
    assert "Sum insured: ₹10 lakh" in lines and "Outpatient cover — must-have" in lines
    assert not any("unclassified" in line or "1000000" in line for line in lines)
    assert not any("encrypted" in line for line in lines)


def test_older_states_without_new_fields_still_load():
    state = ChatState.model_validate({"insurer_filter": "x", "suggestion_asked": True})
    assert state.last_shown == [] and state.listed_for is None


def listed(n=7, **profile):
    source = cards(n)
    state = complete()
    for k, v in profile.items():
        setattr(state.profile, k, v)
    state.answered = ["options_shown", "needs"]
    state.fit_groups = fit_groups(source, state.profile)
    state.plans_requested = True
    return next_question(state, source, relay=NoCalls()), source


def test_not_knowing_the_budget_after_a_list_is_not_a_price_request():
    state, source = listed(annual_budget=None)
    changes, model = interpret("i don't know the annual premium budget", state, source, NoCalls())
    assert changes.budget_unsure and not changes.compare_prices and model is None
    state = transition(state, changes, source, relay=NoCalls())
    assert state.message.startswith("No problem: I’ll leave the budget open.")
    assert "didn’t quite catch" not in state.message and "annual_budget" in state.skipped


def test_a_bare_must_have_restates_the_latest_need_and_never_adds_others():
    source = cards(3)
    state = complete()
    state.profile.requirements = [
        Requirement(field="opd", original_text="OPD matter most", strength="must_have")
    ]
    state.answered = ["options_shown"]
    state.skipped = []
    state.fit_groups = fit_groups(source, state.profile)
    state = next_question(state, source, relay=NoCalls())
    assert state.pending.field == "health_details"
    state = say(state, "must have", source)
    assert [(r.field, r.strength) for r in state.profile.requirements] == [("opd", "must_have")]
    assert state.message.startswith("Got it: outpatient cover stays a must-have.")
    assert "didn’t quite catch" not in state.message


def test_a_vague_limit_is_clarified_without_the_model_at_any_point():
    state, source = listed(3)
    state = say(state, "limit do matter", source)
    assert state.pending.template == "which_limit" and not state.profile.requirements


def test_a_skipped_amount_skips_one_comparison_not_every_later_one():
    state, source = listed(sum_insured=None)
    state = say(state, "compare premiums", source)
    assert state.pending.field == "price_sum_insured"
    state = say(state, "not sure", source)
    assert "I need a sum insured" in state.message
    state = say(state, "what are the annual rates of these plans", source)
    assert state.pending.field == "price_sum_insured"


def test_many_must_haves_are_acknowledged_once_and_sorted_by_count():
    source = cards(7)
    state = complete()
    state.answered = ["options_shown"]
    state.fit_groups = fit_groups(source, state.profile)
    state = next_question(state, source, relay=NoCalls())
    many = Returns(
        requirements=[
            Requirement(field=f, original_text=f, strength="must_have")
            for f in ("opd", "maternity", "copay")
        ]
    )
    state = say(state, "opd, maternity and co-pay are essential", source, many)
    assert state.message.count("Noted:") == 1
    assert "outpatient cover, maternity cover and co-pay are must-haves" in state.message
