"""Customer questions and needs answered from the engine's stored topic answers."""

import uuid

import pytest

from apps.adviser_v2.demo import answer_bank, chat_services, services
from apps.adviser_v2.demo.answer_bank import TOPIC_QUESTIONS, remember
from apps.adviser_v2.demo.answer_retrieval import EXPANSION_VERSION
from apps.adviser_v2.demo.answer_scope import SCOPE_VERSION
from apps.adviser_v2.demo.answers import DRAFT_VERSION
from apps.adviser_v2.demo.chat_rules import requirement_result
from apps.adviser_v2.demo.chat_services import commit_turn, start
from apps.adviser_v2.demo.conversation_contracts import TOPIC_KEYS, Requirement
from apps.adviser_v2.demo.services import decrypted
from apps.adviser_v2.demo.validation import VALIDATOR_VERSION
from apps.adviser_v2.models import DemoQuestion, DemoTopicAnswer
from apps.adviser_v2.tests.test_demo_contracts import citation
from apps.adviser_v2.tests.test_demo_services import demo  # noqa: F401
from apps.adviser_v2.tests.test_guided_services import Reply

pytestmark = pytest.mark.django_db(transaction=True)

HELICOPTER = "which one provides helicoptor transport"


def engine_result(plan_id, *statements, method="P"):
    return {
        "schema_version": 3,
        "draft_contract": DRAFT_VERSION,
        "scope_contract": SCOPE_VERSION,
        "retrieval_contract": EXPANSION_VERSION,
        "validator": VALIDATOR_VERSION,
        "plan_id": plan_id,
        "status": "answered" if statements else "not_found",
        "answer": {"plan_id": plan_id, "status": "answered", "statements": list(statements)}
        if statements
        else None,
        "models": ["test-model"],
        "method": method,
        "total_ms": 1000,
    }


def says(text, scope="base"):
    return {"text": text, "coverage_scope": scope}


def bank(rows):
    """Air ambulance answers for four of the five plans; the last has none stored."""
    rows = rows[:4]
    answers = [
        (rows[0], [says("Air ambulance by helicopter or aeroplane is covered up to the SI.")]),
        (rows[1], [says("Air ambulance cover, if opted.", "optional, extra premium")]),
        (rows[2], []),
        (rows[3], [says("Air ambulance expenses are payable up to Rs 2.5 lakh.")]),
    ]
    for row, statements in answers:
        assert remember(row, "air_ambulance", "P", engine_result(row.plan_key, *statements))


def ask(user, identity, revision, text, relay=None, dispatch=False):
    return commit_turn(
        user,
        identity,
        request_id=uuid.uuid4(),
        revision=revision,
        text=text,
        relay=relay,
        dispatch=dispatch,
    )


def helicopter_relay():
    return Reply(
        policy_question="Which plans provide helicopter transport?", policy_topic="air_ambulance"
    )


def test_topics_match_the_engine_question_set():
    assert set(TOPIC_KEYS) == set(answer_bank.TOPICS)


def test_a_misspelt_benefit_question_is_answered_now_from_stored_answers(v2_user, demo):  # noqa: F811
    _, _, rows = demo
    bank(rows)
    data = start(v2_user)
    response = ask(v2_user, data["id"], 0, HELICOPTER, helicopter_relay())
    state = response["state"]
    q = DemoQuestion.objects.get(pk=state["question_id"])
    # Stored under the engine's own question: the customer's words never reach the bank.
    assert decrypted(q.input_ciphertext, q.id)["question"] == TOPIC_QUESTIONS["air_ambulance"]
    assert not q.profile_bound and q.answers.count() == 5
    filled = q.answers.exclude(result_ciphertext=None)
    assert filled.count() == 4 and q.answers.get(index=rows[4]).state == "queued"
    assert q.state == "queued"  # only the plan without a stored answer is read live
    message = state["message"]
    assert "kept your question" not in message
    assert message.startswith("I’ve read this as a question about air ambulance cover.")
    assert (
        "Of the 5 plans open to you, 2 include air ambulance cover in the base cover, "
        "1 offers it only as an optional add-on (extra premium) and 1 doesn’t mention it."
    ) in message
    assert "Only the wording of" in message and "mentions “helicopter” by name" in message
    assert "still reading the documents of 1 plan" in message
    assert state["pending"]["field"] == "people"  # the interview resumes where it was
    assert state["topic_groups"] == {
        rows[0].plan_key: "base",
        rows[3].plan_key: "base",
        rows[1].plan_key: "addon",
        rows[2].plan_key: "not_found",
    }


def test_a_fully_stored_answer_completes_without_running_the_engine(
    v2_user,
    demo,  # noqa: F811
    monkeypatch,
):
    _, _, rows = demo
    bank(rows)
    remember(rows[4], "air_ambulance", "P", engine_result(rows[4].plan_key))
    dispatched = []
    from apps.adviser_v2.demo import tasks

    monkeypatch.setattr(
        tasks.demo_question, "apply_async", lambda *a, **k: dispatched.append((a, k))
    )
    data = start(v2_user)
    response = ask(v2_user, data["id"], 0, HELICOPTER, helicopter_relay(), dispatch=True)
    q = DemoQuestion.objects.get(pk=response["state"]["question_id"])
    assert q.state == "completed" and q.completed_at and not dispatched
    assert "still reading" not in response["state"]["message"]
    payload = services.question_payload(q)
    assert payload["topic"] == "air_ambulance"
    assert sorted(p["group"] for p in payload["plans"]) == [
        "addon",
        "base",
        "base",
        "not_found",
        "not_found",
    ]
    # The composer is free at once, with follow-ups to the answer.
    assert chat_services.suggestions(chat_services.ChatState(**response["state"]))[:2] == [
        "Show the plans with it in the base cover",
        "Ask exactly my question",
    ]
    response = ask(v2_user, data["id"], 1, "Show the plans with it in the base cover")
    # Listed once the customer has said who is covered, which eligibility needs.
    state = response["state"]
    assert state["plans_requested"] and state["pending"]["field"] == "people"
    assert set(state["list_only"]) == {rows[0].plan_key, rows[3].plan_key}


def test_asking_exactly_runs_the_customers_words_for_the_answered_plans(
    v2_user,
    demo,  # noqa: F811
    monkeypatch,
):
    _, _, rows = demo
    bank(rows)
    remember(rows[4], "air_ambulance", "P", engine_result(rows[4].plan_key))
    data = start(v2_user)
    first = ask(v2_user, data["id"], 0, HELICOPTER, helicopter_relay())
    response = ask(v2_user, data["id"], 1, "Ask exactly my question")
    q = DemoQuestion.objects.get(pk=response["state"]["question_id"])
    assert q.pk != first["state"]["question_id"] and q.state == "queued"
    text = decrypted(q.input_ciphertext, q.id)["question"]
    assert text == "Which plans provide helicopter transport?"
    # Every plan with a stored answer, the ones whose documents cover it first; five at most.
    assert {a.index.plan_key for a in q.answers.select_related("index")} == {
        r.plan_key for r in rows
    }
    assert "I’m reading the documents of" in response["state"]["message"]
    # A free-form question's answers are never kept for other customers.
    before = DemoTopicAnswer.objects.count()
    monkeypatch.setattr(
        services,
        "answer_plan",
        lambda bundle, question, **kw: engine_result(
            bundle["policy_version_id"], says("Helicopter transfer is covered.")
        ),
    )
    services.run_question(q.id)
    assert DemoTopicAnswer.objects.count() == before
    q.refresh_from_db()
    assert q.state == "completed"


def test_a_live_topic_answer_is_kept_for_the_next_customer(v2_user, demo, monkeypatch):  # noqa: F811
    _, _, rows = demo
    bank(rows)
    data = start(v2_user)
    response = ask(v2_user, data["id"], 0, HELICOPTER, helicopter_relay())
    monkeypatch.setattr(
        services,
        "answer_plan",
        lambda bundle, question, **kw: engine_result(
            bundle["policy_version_id"], says("Air ambulance is covered.")
        ),
    )
    services.run_question(response["state"]["question_id"])
    kept = DemoTopicAnswer.objects.get(index=rows[4], topic="air_ambulance")
    result = decrypted(kept.result_ciphertext, kept.id)
    assert kept.status == "answered" and "helicopt" not in str(result).casefold()


def test_a_stated_need_shows_the_stored_evidence_before_the_strength_question(v2_user, demo):  # noqa: F811
    _, _, rows = demo
    statements = {
        0: [says("OPD consultations are covered up to Rs 5,000.")],
        1: [says("Outpatient treatment, if opted.", "optional, extra premium")],
        2: [],
    }
    for i, found in statements.items():
        remember(rows[i], "opd", "P", engine_result(rows[i].plan_key, *found))
    data = start(v2_user)
    relay = Reply(requirements=[Requirement(field="opd", original_text="OPD")])
    response = ask(v2_user, data["id"], 0, "OPD", relay)
    state = response["state"]
    q = DemoQuestion.objects.get(pk=state["question_id"])
    # Only the plans with a stored answer: the reply never waits on the engine.
    assert q.state == "completed" and q.answers.count() == 3
    assert (
        "Outpatient (OPD) cover: of the 3 plans open to you, 1 includes it in the base cover, "
        "1 offers it only as an optional add-on (extra premium) and 1 doesn’t mention it."
    ) in state["message"]
    assert state["message"].endswith(state["pending"]["text"])


def test_a_variant_table_is_read_for_the_plans_own_variant():
    table = says(
        "Air Ambulance Cover • Classic & Select Variant: NA "
        "• Elite Variant: Covered up to Sum Insured. B. Road Ambulance: covered."
    )
    result = engine_result("plan", table)
    assert answer_bank.group(result, "air_ambulance", "Select") == "excluded"
    assert answer_bank.group(result, "air_ambulance", "Elite") == "base"
    # A plan without a variant line, or a table it isn't named in, reads as before.
    assert answer_bank.group(result, "air_ambulance", "Default") == "base"
    assert answer_bank.group(result, "air_ambulance") == "base"


def test_the_table_the_counts_and_the_plan_list_give_one_answer_per_plan(v2_user, demo):  # noqa: F811
    _, _, rows = demo
    opd = {
        0: [says("OPD consultations are covered up to Rs 5,000.")],
        1: [says("Outpatient treatment, if opted.", "optional, extra premium")],
        2: [],
    }
    for i, found in opd.items():
        remember(rows[i], "opd", "P", engine_result(rows[i].plan_key, *found))
    # The stored answer missed an add-on that the plan's fact card quotes.
    quote = "Outpatient cover is available on payment of additional premium."
    sold = {
        "heading": "OPD cover",
        "text": quote,
        "excerpts": [quote],
        "conditions": [],
        "restrictions": [],
        "citations": [citation(quote).model_dump()],
    }
    # And a plan whose base cover has some of it also sells an add-on extending it.
    for row in (rows[2], rows[0]):
        row.card = {
            **row.card,
            "optional_covers": {"opd": {"status": "optional", "statements": [sold]}},
        }
        row.save(update_fields=["card"])
    data = start(v2_user)
    relay = Reply(requirements=[Requirement(field="opd", original_text="OPD")])
    state = ask(v2_user, data["id"], 0, "OPD", relay)["state"]
    assert (
        "Outpatient (OPD) cover: of the 3 plans open to you, 1 includes it in the base cover "
        "and 2 offer it only as an optional add-on (extra premium)."
    ) in state["message"]
    assert state["topic_groups"][rows[2].plan_key] == "addon"
    q = DemoQuestion.objects.get(pk=state["question_id"])
    stored = decrypted(q.input_ciphertext, q.id)
    assert stored["question"] == TOPIC_QUESTIONS["opd"] and set(stored["verdicts"]) == {
        rows[0].plan_key,
        rows[2].plan_key,
    }
    plans = {p["plan_id"]: p for p in services.question_payload(q)["plans"]}
    assert plans[rows[2].plan_key]["group"] == "addon"
    shown = plans[rows[2].plan_key]["card_statements"]
    assert shown[0]["text"] == quote and shown[0]["citations"][0]["quote"] == quote
    assert shown[0]["coverage_scope"] == "optional, extra premium"
    # The base cover's wording stays, with the add-on that extends it beside it.
    base = plans[rows[0].plan_key]
    assert base["group"] == "base" and base["result"]["answer"]["statements"]
    assert base["card_statements"][0]["coverage_scope"] == "optional, extra premium"
    # Plans the stored answer already places show only its wording.
    assert (
        plans[rows[1].plan_key]["group"] == "addon"
        and not plans[rows[1].plan_key]["card_statements"]
    )
    # The plan list reads the same card the same way.
    need = Requirement(field="opd", value="covered", original_text="OPD", strength="must_have")
    rows[2].refresh_from_db()
    assert requirement_result(rows[2].card, need)["status"] == "addon"


def test_a_long_card_quote_is_shown_from_its_clause_on_the_topic():
    rooms = "Room rent is covered up to a single private room. " * 8
    gyms = "Gym membership is offered. " * 20
    quote = rooms + "4.30. Wellconsult+ Opt for complete wellness and Out-patient benefits. " + gyms
    noise = "• Lock the Clock Benefit will be impacted, if a claim is paid under this benefit."
    found = [
        {"text": quote, "excerpts": [quote, noise], "conditions": [], "restrictions": []},
        {"text": quote, "excerpts": [quote], "conditions": [], "restrictions": []},
    ]
    shown = answer_bank.card_quotes(found, "opd")
    # One statement, one excerpt: the clause on outpatient cover, cut verbatim.
    assert len(shown) == 1 and len(shown[0]["excerpts"]) == 1
    excerpt = shown[0]["excerpts"][0]
    assert excerpt.startswith("… Wellconsult+ Opt for complete wellness") and excerpt.endswith(" …")
    assert excerpt.removeprefix("… ").removesuffix(" …") in " ".join(quote.split())
    assert len(excerpt) < 400 and shown[0]["text"] == quote
    # A table of add-ons has no full stops: the excerpt starts at the add-on's own row.
    table = (
        "Co-Payment 0%, 10%, 20%, 30%, 40%, 50% Annual Aggregate Deductible INR 10,000; "
        "INR 20,000; INR 30,000; INR 50,000; INR 1,00,000; INR 2,00,000; INR 3,00,000; "
        "INR 4,00,000; INR 5,00,000 Claim Safeguard+ All Non-payable items will be covered "
        "(as per list I, II, III, IV) Wellconsult+(6) Choose up to 5X of total premium for "
        "OPD coverage like: Consultation, Diagnostics, Pharmacy, Gym Memberships and many more."
    )
    row = {"text": table, "conditions": [], "restrictions": []}
    (excerpt,) = answer_bank.card_quotes([row], "opd")[0]["excerpts"]
    assert excerpt.startswith("… Wellconsult+(6) Choose up to 5X of total premium for OPD")
