import uuid

import pytest

from apps.adviser_v2.demo.chat_rules import fit_groups
from apps.adviser_v2.demo.chat_services import commit_turn, history, start, turn_blocks
from apps.adviser_v2.demo.conversation import next_question
from apps.adviser_v2.demo.conversation_contracts import ChatState
from apps.adviser_v2.demo.services import decrypted
from apps.adviser_v2.models import DemoConversation
from apps.adviser_v2.tests.test_demo_services import demo  # noqa: F401
from apps.adviser_v2.tests.test_guided_conversation import NoCalls, cards, complete
from apps.adviser_v2.tests.test_guided_services import Reply


def turn(user, identity, revision, text, **changes):
    return commit_turn(
        user,
        identity,
        request_id=uuid.uuid4(),
        revision=revision,
        text=text,
        relay=Reply(**changes),
        dispatch=False,
    )


@pytest.mark.django_db(transaction=True)
def test_history_lists_owned_started_chats_newest_first_with_encrypted_titles(
    v2_user,
    demo,  # noqa: F811
    django_user_model,
):
    other = django_user_model.objects.create(email="other-history@example.invalid", is_active=True)
    empty = start(v2_user)
    first = start(v2_user)
    second = start(v2_user)
    start(other)
    turn(v2_user, first["id"], 0, "We live in Pune and need maternity cover", city="Pune")
    turn(v2_user, second["id"], 0, "Two adults in Mumbai", city="Mumbai")
    before = DemoConversation.objects.get(pk=first["id"]).updated_at
    turn(v2_user, first["id"], 1, "Budget is thirty thousand", annual_budget=30000)
    row = DemoConversation.objects.get(pk=first["id"])
    assert row.updated_at > before
    assert b"Pune" not in bytes(row.title_ciphertext)
    listed = history(v2_user)
    assert [c["id"] for c in listed] == [first["id"], second["id"]]
    assert listed[0]["title"] == "We live in Pune and need maternity cover"
    assert empty["id"] not in {c["id"] for c in listed}
    assert history(other) == []


@pytest.mark.django_db(transaction=True)
def test_history_endpoint_is_owner_scoped(client, v2_user, demo):  # noqa: F811
    data = start(v2_user)
    turn(v2_user, data["id"], 0, "Pune", city="Pune")
    assert client.get("/api/v2/demo/conversations/").status_code in {401, 403}
    client.force_login(v2_user)
    response = client.get("/api/v2/demo/conversations/")
    assert response.status_code == 200
    assert [c["title"] for c in response.json()] == ["Pune"]


@pytest.mark.django_db(transaction=True)
def test_assistant_messages_carry_question_and_price_blocks_once(v2_user, demo):  # noqa: F811
    data = start(v2_user)
    response = turn(
        v2_user,
        data["id"],
        0,
        "What is covered?",
        policy_question="What is covered?",
        selected_plans=[r.plan_key for r in demo[2][:2]],
    )
    reply = response["state"]["transcript"][-1]
    assert reply["blocks"] == [
        {"type": "question", "question_id": response["state"]["question_id"]}
    ]
    state = ChatState.model_validate(
        decrypted(DemoConversation.objects.get(pk=data["id"]).state_ciphertext, data["id"])
    )
    state.price = {"status": "found", "amount_printed": "12,000", "citations": []}
    state.price_plan = "plan"
    prior = state.model_copy(deep=True)
    assert [b["type"] for b in turn_blocks(state, ChatState(), [])] == ["question", "price"]
    # Unchanged state from the previous turn draws nothing again.
    assert turn_blocks(state, prior, []) == []


def test_shortlist_block_includes_unconfirmed_remaining_plans_without_reasons():
    source = cards(3)
    state = complete()
    state.fit_groups = fit_groups(source, state.profile)
    state.fit_groups["unresolved"].append(state.fit_groups["fits"].pop())
    state.fit_groups["unresolved"][-1]["status"] = "unresolved"
    state = next_question(state, source, relay=NoCalls())
    assert state.stop_reason == "two_or_three_remain"
    [block] = turn_blocks(state, ChatState(), source)
    assert block["type"] == "shortlist"
    assert len(block["plans"]) == 3
    assert sorted(p["confirmed"] for p in block["plans"]) == [False, True, True]
    assert all("explanation" not in p for p in block["plans"])
