"""Customer questions and needs answered from the engine's stored topic answers."""

import hashlib
import json
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
from apps.adviser_v2.demo.evidence import digest
from apps.adviser_v2.demo.services import bundle_for, decrypted
from apps.adviser_v2.demo.validation import VALIDATOR_VERSION
from apps.adviser_v2.demo.views import render_anchor
from apps.adviser_v2.models import DemoPlanIndex, DemoQuestion, DemoTopicAnswer
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


# One brochure and one policy wording printed for every ReAssure-style variant. The
# brochure table prints a benefit every variant shares as one cell across the variant
# columns; the table reader files that cell under the first column, Classic.
VARIANTS = ["Classic", "Select", "Elite", "Black"]
BROCHURE = (
    "Benefit Classic Select Elite Black\n"
    "Room Type Twin Sharing Single Room Single Room Suite\n"
    "E-Consultation Unlimited (Only Cashless)\n"
    "C. Air Ambulance • Classic & Select Variant: NA "
    "• Elite & Black Variant: Up to INR 5L per hospitalization\n"
)
WORDING = (
    "4.1 Day Care Treatment\n"
    "Day care treatments are covered up to the Sum Insured.\n"
    "Day care for the Classic variant needs 2 hours of admission.\n"
)
PAGES = {"page-1": BROCHURE, "page-2": WORDING}
AIR = (
    "C. Air Ambulance • Classic & Select Variant: NA "
    "• Elite & Black Variant: Up to INR 5L per hospitalization"
)
TABLE_ROWS = [
    ["Benefit", *VARIANTS],
    ["Room Type", "Twin Sharing", "Single Room", "Single Room", "Suite"],
    ["E-Consultation", "Unlimited (Only Cashless)"],
]


def section_of(plan, page_id):
    # Section IDs derive from each variant's own plan ID.
    return f"{plan}:{page_id}"


@pytest.fixture
def family(tmp_path):
    """Classic and Elite plan indexes of one product over the same documents."""
    pdf = tmp_path / "reassure.pdf"
    pdf.write_bytes(b"%PDF-1.4 shared brochure and wording")
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    indexes = {}
    for variant in ("Classic", "Elite"):
        plan = f"reassure-{variant.lower()}"
        sections, cursor = [], 0
        for n, (page_id, text) in enumerate(PAGES.items(), start=1):
            segment = {
                "page_id": page_id,
                "page": n,
                "start": 0,
                "end": len(text),
                "document_start": cursor,
                "document_end": cursor + len(text),
                "text": text,
            }
            sections.append(
                {
                    "id": section_of(plan, page_id),
                    "plan_id": plan,
                    "document_id": "reassure",
                    "document_sha256": sha,
                    "role": "base_wording",
                    "title_path": [],
                    "segments": [segment],
                }
            )
            cursor += len(text) + 1
        cells = {
            f"t:{r}:{c}": {
                "id": f"t:{r}:{c}",
                "row": r,
                "column": c,
                "text": text,
                "citation": {"section_id": section_of(plan, "page-1"), "page_id": "page-1"},
            }
            for r, row in enumerate(TABLE_ROWS)
            for c, text in enumerate(row)
        }
        bundle = {
            "policy_version_id": plan,
            "name": "ReAssure 3.0",
            "variant": variant,
            "variants": VARIANTS,
            "documents": [{"document_version_id": "reassure", "sha256": sha, "path": str(pdf)}],
            "pages": [
                {
                    "evidence_span_id": page_id,
                    "document_sha256": sha,
                    "passage": text,
                    "ocr_words": [{"start": 0, "end": len(text), "bbox": [0, 0, 1, 1]}],
                }
                for page_id, text in PAGES.items()
            ],
            "sections": sections,
            "tables": [{"id": "t", "cells": cells}],
            "navigation": [],
        }
        key = digest(bundle)
        bundle["index_id"] = key
        path = tmp_path / f"{key}.json"
        path.write_text(json.dumps(bundle))
        indexes[variant] = DemoPlanIndex.objects.create(
            id=key,
            plan_key=plan,
            insurer="Niva Bupa",
            name="ReAssure 3.0",
            uin="NBHHLIP26047V012526",
            variant=variant,
            bundle_path=str(path),
        )
    return sha, indexes


def quoted(index, page_id, *quotes, **extra):
    """A base statement quoting this wording, cited to the plan's own section."""
    return {
        "text": "\n\n".join(quotes),
        "excerpts": list(quotes),
        "coverage_scope": "base",
        "citations": [
            {
                "section_id": section_of(index.plan_key, page_id),
                "page_id": page_id,
                "quote": q,
                "occurrence": 0,
            }
            for q in quotes
        ],
        "conditions": [],
        "restrictions": [],
        **extra,
    }


def answered(sha, index, *statements):
    """A validated engine answer with every quote anchored in the plan's documents."""
    anchors, mapping = [], []
    for statement in statements:
        mapping.append([])
        for c in statement["citations"]:
            start = PAGES[c["page_id"]].index(c["quote"])
            mapping[-1].append(len(anchors))
            anchors.append(
                {
                    "document_id": "reassure",
                    "document_sha256": sha,
                    "page": 1,
                    "page_id": c["page_id"],
                    "section_id": c["section_id"],
                    "start": start,
                    "end": start + len(c["quote"]),
                    "quote": c["quote"],
                    "method": "ocr",
                    "role": "base_wording",
                }
            )
    result = engine_result(index.plan_key, *statements)
    result["validation"] = {
        "anchors": anchors,
        "statement_anchors": mapping,
        "checks": [True] * 6,
        "problems": [],
    }
    return result


def merged_cell(index):
    return quoted(
        index,
        "page-1",
        "E-Consultation",
        "Classic",
        "Unlimited (Only Cashless)",
        table={
            "region_id": "t",
            "value_cell_id": "t:2:1",
            "row_label_ids": ["t:2:0"],
            "column_label_ids": ["t:0:1"],
        },
    )


def test_a_variant_line_gives_a_sibling_variant_its_own_entry(family):
    sha, plans = family
    classic, elite = plans["Classic"], plans["Elite"]
    remember(classic, "air_ambulance", "P", answered(sha, classic, quoted(classic, "page-1", AIR)))
    groups = answer_bank.bank_groups([classic.id, elite.id], "P")
    assert groups[classic.id]["air_ambulance"] == "excluded"
    assert groups[elite.id]["air_ambulance"] == "base"
    # The answer building the bank reads each plan's own answers only.
    assert answer_bank.lookup([elite], "air_ambulance", "P") == {}
    shown = answer_bank.lookup([elite], "air_ambulance", "P", siblings=True)[elite.id]
    assert shown["shared_from"] == {"index": classic.id, "variant": "Classic"}
    assert shown["plan_id"] == shown["answer"]["plan_id"] == elite.plan_key
    assert shown["index_version"] == elite.id
    # Every quote opens in the Elite plan's own copy of the documents.
    bundle = bundle_for(elite)
    for anchor in shown["validation"]["anchors"]:
        assert anchor["section_id"] == section_of(elite.plan_key, "page-1")
        assert render_anchor(elite.id, anchor, bundle).data["quote"] == AIR
    (statement,) = answer_bank.statements(shown)
    assert statement["citations"][0]["section_id"] == section_of(elite.plan_key, "page-1")


def test_a_benefit_cell_printed_across_every_variant_is_each_variants_own(family):
    sha, plans = family
    classic, elite = plans["Classic"], plans["Elite"]
    remember(classic, "opd", "P", answered(sha, classic, merged_cell(classic)))
    assert answer_bank.bank_groups([elite.id], "P")[elite.id]["opd"] == "base"
    shown = answer_bank.lookup([elite], "opd", "P", siblings=True)[elite.id]
    (statement,) = answer_bank.statements(shown)
    # The Classic column label is not Elite's wording, so it is neither shown nor linked.
    assert statement["excerpts"] == ["E-Consultation", "Unlimited (Only Cashless)"]
    assert statement["text"] == "E-Consultation\n\nUnlimited (Only Cashless)"
    assert statement["table"]["column_label_ids"] == ["t:0:3"]
    assert statement["scope_variant"] == "Elite"
    anchors = shown["validation"]["anchors"]
    assert [a["quote"] for a in anchors] == ["E-Consultation", "Unlimited (Only Cashless)"]
    assert shown["validation"]["statement_anchors"] == [[0, 1]]
    bundle = bundle_for(elite)
    assert [render_anchor(elite.id, a, bundle).data["quote"] for a in anchors] == [
        "E-Consultation",
        "Unlimited (Only Cashless)",
    ]


def test_a_cell_in_a_row_with_other_variants_values_stays_with_its_variant(family):
    sha, plans = family
    classic, elite = plans["Classic"], plans["Elite"]
    room = quoted(
        classic,
        "page-1",
        "Room Type",
        "Classic",
        "Twin Sharing",
        table={
            "region_id": "t",
            "value_cell_id": "t:1:1",
            "row_label_ids": ["t:1:0"],
            "column_label_ids": ["t:0:1"],
        },
    )
    remember(classic, "room_rent", "P", answered(sha, classic, room))
    assert answer_bank.lookup([elite], "room_rent", "P", siblings=True) == {}
    assert "room_rent" not in answer_bank.bank_groups([elite.id], "P").get(elite.id, {})


def test_wording_naming_another_variant_is_not_borrowed(family):
    sha, plans = family
    classic, elite = plans["Classic"], plans["Elite"]
    general = quoted(classic, "page-2", "Day care treatments are covered up to the Sum Insured.")
    own = quoted(classic, "page-2", "Day care for the Classic variant needs 2 hours of admission.")
    remember(classic, "day_care", "P", answered(sha, classic, own, general))
    shown = answer_bank.lookup([elite], "day_care", "P", siblings=True)[elite.id]
    # Only the wording every variant shares carries over, linked to its own quote.
    (statement,) = answer_bank.statements(shown)
    assert statement["text"] == "Day care treatments are covered up to the Sum Insured."
    assert [a["quote"] for a in shown["validation"]["anchors"]] == [statement["text"]]
    assert shown["validation"]["statement_anchors"] == [[0]]
    remember(classic, "day_care", "P", answered(sha, classic, own))
    assert answer_bank.lookup([elite], "day_care", "P", siblings=True) == {}


def test_an_exclusion_code_heading_further_down_a_list_is_an_exclusion():
    wording = (
        "This includes: a. Any type of contraception, sterilization b. Assisted Reproduction "
        "services including artificial insemination and advanced reproductive technologies "
        "such as IVF, ZIFT, GIFT, ICSI c. Gestational Surrogacy d. Reversal of sterilization. "
        "Maternity Expenses (Code-Excl18) a. Medical treatment expenses traceable to childbirth."
    )
    assert wording.index("Code-Excl18") > 200
    assert answer_bank.group(engine_result("plan", says(wording)), "maternity") == "excluded"
