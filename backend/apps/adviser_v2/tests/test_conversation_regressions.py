"""Replays of customer turns that went wrong in a real demo conversation."""

from types import SimpleNamespace

from apps.adviser_v2.demo.chat_rules import fit_groups, requirement_result, topic_verdict
from apps.adviser_v2.demo.chat_services import suggestions, turn_blocks
from apps.adviser_v2.demo.conversation import interpret, next_question, summary, transition
from apps.adviser_v2.demo.conversation_contracts import (
    ChatPerson,
    ChatState,
    ProposedChanges,
    Requirement,
)
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


def with_wait(c, months, conditions=()):
    c.setdefault("executable_rules", []).append(
        {
            "field": "ped_waiting",
            "kind": "maximum",
            "value": months,
            "unit": "months",
            "conditions": list(conditions),
            "condition_mode": "quoted",
            "citations": [citation(f"Pre-existing diseases after {months} months.").model_dump()],
        }
    )
    return c


DIABETIC = "I am diabetic and i want it to be covered too"


def diabetic(person_id=None):
    # As in the live run: health details captured, the need filed as "other".
    return Returns(
        health_details="Diabetes",
        requirements=[
            Requirement(
                field="other", original_text=DIABETIC, strength="must_have", person_id=person_id
            )
        ],
    )


def test_an_illness_to_cover_is_answered_with_pre_existing_waits():
    state, source = listed(7)
    with_wait(source[2], 36, ["declared at the time of application and accepted by Insurer"])
    with_wait(source[5], 24)
    with_wait(source[0], 36)
    state = say(state, DIABETIC, source, diabetic())
    needs = state.profile.requirements
    assert [(r.field, r.value) for r in needs] == [("ped_waiting", "shown")]
    assert "can’t check" not in state.message and "waiting period" in state.message
    assert "declare it when you apply" in state.message
    assert "waiting period: 24 months for Insurer 2 5 and 36 months for" in state.message
    assert "doesn’t mean they exclude it" in state.message
    assert state.pending.template == "batch" and state.shown_plans[0] == "5"
    assert set(state.shown_plans[1:3]) == {"0", "2"}
    # Shown for information: nothing is filtered and no must-have is noted.
    assert len(state.fit_groups["fits"]) + len(state.fit_groups["unresolved"]) == 7
    assert "Noted:" not in state.message
    assert "Sorted by what you told me: shortest pre-existing illness wait first" in state.message
    assert not any("diabetic" in line.casefold() for line in state.understanding)
    assert "Pre-existing illness cover — wanted" in state.understanding
    block = turn_blocks(state, ChatState(), source)[0]
    assert block["needs"] == [
        {"field": "ped_waiting", "label": "Pre-existing illness covered after"}
    ]
    assert block["plans"][0]["needs"][0]["detail"] == "24 months"
    assert suggestions(state) == ["Show more", "Compare premiums"]


def test_a_relatives_illness_is_attached_to_that_relative():
    state, source = listed(3)
    state.profile.people.append(ChatPerson(id="father", relationship="parent", age=62))
    state = say(state, "my father is diabetic, want it covered", source, diabetic("father"))
    assert [(r.field, r.person_id) for r in state.profile.requirements] == [
        ("ped_waiting", "father")
    ]


def test_a_shown_wait_never_conflicts_with_a_plan():
    source = cards(2)
    with_wait(source[0], 48)
    need = Requirement(field="ped_waiting", original_text="x", strength="must_have", value="shown")
    assert requirement_result(source[0], need)["status"] == "fits"
    assert requirement_result(source[1], need)["status"] == "unresolved"


def split(source, field, value, yes=3):
    for i, c in enumerate(source):
        with_rule(c, field, value if i < yes else "not_covered")
    return source


def narrowing(*fields):
    source = cards(7)
    for field in fields:
        split(source, field, "covered")
    state = complete()
    state.answered = ["options_shown", "needs"]
    state.fit_groups = fit_groups(source, state.profile)
    return next_question(state, source), source


def reply(state, text, source):
    """A customer reply read without the model; fixed questions follow."""
    changes, model = interpret(text, state, source, NoCalls())
    assert model is None
    return transition(state, changes, source)


def test_a_bare_no_to_a_narrowing_question_stores_nothing():
    state, source = narrowing("opd")
    assert state.pending.template == "narrow" and state.pending.field == "opd"
    changes, model = interpret("No", state, source, NoCalls())
    assert changes.affirmative is False and not changes.requirements and model is None
    state = transition(state, changes, source)
    assert not state.profile.requirements and state.declined_narrowing == 1
    assert state.pending.field != "opd" and "didn’t quite catch" not in state.message


def test_two_declined_narrowing_questions_show_the_plans():
    state, source = narrowing("opd", "ayush", "restoration")
    state = reply(state, "no", source)
    assert state.pending.template == "narrow"
    state = reply(state, "not needed", source)
    assert not state.profile.requirements and len(state.shown_plans) == 5
    assert "Those questions didn’t narrow the list, so here are the plans." in state.message


def test_maternity_is_never_offered_to_one_adult_but_is_to_a_couple():
    state, _ = narrowing("maternity")
    assert state.pending.field != "maternity"
    source = split(cards(7), "maternity", "covered")
    state = complete()
    state.answered = ["options_shown", "needs"]
    state.answered.append("coverage_basis")
    state.profile.people.append(ChatPerson(id="spouse", relationship="spouse", age=33))
    state.fit_groups = fit_groups(source, state.profile)
    state = next_question(state, source)
    assert state.pending.field == "maternity"


def test_narrowing_questions_use_plain_words():
    source = cards(7)
    for i, c in enumerate(source):
        c.setdefault("executable_rules", []).append(
            {
                "field": "room_limit",
                "kind": "room",
                "value": "single_private" if i < 3 else "twin_sharing",
                "citations": [citation().model_dump()],
            }
        )
    state = complete()
    state.answered = ["options_shown", "needs"]
    state.fit_groups = fit_groups(source, state.profile)
    state = next_question(state, source)
    assert state.pending.template == "narrow" and "a single private room" in state.message
    for raw in ("actuals", "remaining", "single_private", "conditions conditions"):
        assert raw not in state.message


def needs_answered():
    state = complete()
    state.answered = ["options_shown", "needs"]
    state.skipped = []
    return state


def test_a_shared_illness_is_answered_with_each_plans_pre_existing_wait():
    source = cards(7)
    with_wait(source[1], 24)
    with_wait(source[3], 36, ["declared at the time of application and accepted by Insurer"])
    state = asked(needs_answered(), "health_details", source)
    state = say(state, "i have high blood pressure", source, Returns(health_details="hypertension"))
    assert [(r.field, r.value) for r in state.profile.requirements] == [("ped_waiting", "shown")]
    assert "waiting period: 24 months for" in state.message
    assert "declare it when you apply" in state.message
    assert "hypertension" not in state.message.casefold()
    # Answered already: never offered back as a narrowing question.
    assert "ped_waiting" in state.narrowing_asked and len(state.shown_plans) == 5


def test_no_health_conditions_is_recorded_without_a_need():
    source = cards(3)
    state = asked(needs_answered(), "health_details", source)
    state = say(state, "no health conditions", source, Returns(health_details="none"))
    assert not state.profile.requirements and "health_details" in state.answered


def test_a_must_have_never_excludes_a_plan_that_sells_it_as_an_add_on():
    source = cards(3)
    with_rule(source[0], "opd", "covered")
    with_rule(source[1], "opd", "not_covered")
    with_rule(source[2], "opd", "not_covered")
    source[1]["optional_covers"] = {
        "opd": {"status": "optional, extra premium", "statements": [citation().model_dump()]}
    }
    state = complete()
    state.profile.requirements = [
        Requirement(field="opd", original_text="OPD", strength="must_have")
    ]
    groups = fit_groups(source, state.profile)
    assert [r["plan_id"] for r in groups["doesnt_fit"]] == ["2"]
    need = state.profile.requirements[0]
    assert requirement_result(source[1], need)["status"] == "addon"


def test_an_uncited_exclusion_never_rules_a_plan_out():
    source = cards(2)
    source[0]["bank_groups"] = {"air_ambulance": "excluded"}
    need = Requirement(field="air_ambulance", original_text="air ambulance", strength="must_have")
    state = complete()
    state.profile.requirements = [need]
    assert not fit_groups(source, state.profile)["doesnt_fit"]


def test_a_misspelt_benefit_question_routes_without_the_model():
    state, source = listed(7)
    changes, model = interpret("which one provides helicoptor transport", state, source, NoCalls())
    assert changes.policy_topic == "air_ambulance" and model is None
    assert changes.policy_question and not changes.requirements
    state = transition(state, changes, source, relay=NoCalls())
    assert state.policy_topic == "air_ambulance" and len(state.asked_plans) == 7
    assert not state.policy_deferred and "kept your question" not in state.message
    # A personal statement goes to the model, which reads it as a need.
    need = Returns(requirements=[Requirement(field="opd", original_text="OPD")])
    changes, model = interpret("is opd a must for me?", state, source, need)
    assert model == "test" and changes.policy_topic is None


def test_one_verdict_per_plan_follows_the_cards_cited_rules_then_the_stored_answer():
    source = cards(5)
    with_rule(source[0], "opd", "covered")
    with_rule(source[1], "opd", "not_covered")
    with_rule(source[2], "opd", "not_covered")
    sold = {"text": "OPD treatment, if opted.", "conditions": [], "restrictions": []}
    source[2]["optional_covers"] = {"opd": {"status": "optional", "statements": [sold]}}
    with_wait(source[3], 36)
    # A cited rule decides, with its own quote, whatever the stored answer says.
    group, quoted = topic_verdict(source[0], "opd", "not_found")
    assert group == "base" and quoted[0]["text"] == "Cover is 5 lakh for 30 days."
    assert quoted[0]["citations"] and quoted[0]["coverage_scope"] == "base"
    assert topic_verdict(source[1], "opd", "base")[0] == "excluded"
    # A plan that sells it never reads as excluded: the card's add-on, or the stored one.
    group, quoted = topic_verdict(source[2], "opd", None)
    assert group == "addon" and quoted[0]["coverage_scope"] == "optional, extra premium"
    assert topic_verdict(source[1], "opd", "addon") == ("addon", None)
    # An add-on to a benefit the stored answer puts in the base cover leaves it there,
    # and its quotes are shown beside the stored answer.
    source[4]["optional_covers"] = source[2]["optional_covers"]
    decided, quoted = topic_verdict(source[4], "opd", "base")
    assert decided == "base" and quoted
    assert {s["coverage_scope"] for s in quoted} == {"optional, extra premium"}
    source[4]["bank_groups"] = {"opd": "base"}
    need = Requirement(field="opd", value="covered", original_text="OPD", strength="must_have")
    assert requirement_result(source[4], need)["status"] == "fits"
    del source[4]["optional_covers"], source[4]["bank_groups"]
    assert topic_verdict(source[3], "ped", "not_found")[0] == "base"
    # Without a rule or add-on on the card, the stored answer stands unchanged.
    assert topic_verdict(source[4], "opd", "excluded") == ("excluded", None)
    assert topic_verdict(source[4], "air_ambulance", "base") == ("base", None)


def test_no_after_the_plan_list_signs_off_instead_of_asking_again():
    state, source = listed(7)
    assert state.pending.template in {"batch", "batch_end"}
    state = reply(state, "No", source)
    assert state.pending.template == "closing" and not state.shown_plans
    assert "anything else" not in state.message
    # Another "no" is acknowledged briefly, never read as not understood; a new need or
    # "show more" still goes on as usual.
    for text in ("No, that’s all", "I don't want it"):
        state = reply(state, text, source)
        assert state.pending.template == "closing" and not state.shown_plans
        assert state.message == "Alright. I’m here whenever you have a question about these plans."
    state = reply(state, "Show more", source)
    assert state.pending.template != "closing"


def test_no_to_anything_else_after_the_plan_list_never_lists_the_plans_again():
    state, source = listed(3)
    state.pending.template = "exhausted"
    state = reply(state, "No", source)
    assert state.pending.template == "closing" and not state.shown_plans
