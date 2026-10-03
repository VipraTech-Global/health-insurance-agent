import uuid
from types import SimpleNamespace

import pytest
from django.utils import timezone

from apps.adviser_v2.demo.chat_services import StaleTurn, commit_turn, start
from apps.adviser_v2.demo.conversation_contracts import ProposedChanges
from apps.adviser_v2.demo.services import decrypted
from apps.adviser_v2.models import DemoChatTurn, DemoConversation
from apps.adviser_v2.services.erasure import erase_account
from apps.adviser_v2.tests.test_demo_services import demo  # noqa: F401

pytestmark = pytest.mark.django_db(transaction=True)


class Reply:
    def __init__(self, **changes):
        self.changes = changes
        self.calls = 0

    def call(self, **kwargs):
        assert kwargs["stage"] == "chat_interpretation"
        self.calls += 1
        return SimpleNamespace(
            value=ProposedChanges(**self.changes).model_dump(), model="test-luna"
        )


def test_idempotent_encrypted_turns_stale_revision_and_ownership(v2_user, demo, django_user_model):  # noqa: F811
    v2_other_user = django_user_model.objects.create(
        email="other-guided@example.invalid", is_active=True
    )
    data = start(v2_user)
    identity = data["id"]
    key = uuid.uuid4()
    relay = Reply(city="Pune", health_details="synthetic optional detail")
    first = commit_turn(
        v2_user,
        identity,
        request_id=key,
        revision=0,
        text="Pune; synthetic optional detail",
        relay=relay,
        dispatch=False,
    )
    replay = commit_turn(
        v2_user,
        identity,
        request_id=key,
        revision=0,
        text="Pune; synthetic optional detail",
        relay=relay,
        dispatch=False,
    )
    assert first == replay and relay.calls == 1
    assert first["state"]["revision"] == 1 and first["state"]["pending"]["field"] == "people"
    receipt = DemoChatTurn.objects.get(conversation_id=identity)
    assert b"Pune" not in bytes(receipt.input_ciphertext) and b"Pune" not in bytes(
        receipt.output_ciphertext
    )
    convo = DemoConversation.objects.get(pk=identity)
    assert b"synthetic optional detail" not in bytes(convo.state_ciphertext)
    assert (
        decrypted(convo.state_ciphertext, convo.id)["profile"]["health_details"]
        == "synthetic optional detail"
    )
    with pytest.raises(StaleTurn):
        commit_turn(
            v2_user, identity, request_id=uuid.uuid4(), revision=0, text="Change city", relay=relay
        )
    with pytest.raises(StaleTurn):
        commit_turn(v2_user, identity, request_id=key, revision=0, text="Different", relay=relay)
    with pytest.raises(DemoConversation.DoesNotExist):
        commit_turn(
            v2_other_user, identity, request_id=uuid.uuid4(), revision=1, text="Pune", relay=relay
        )


def test_revocation_prevents_receipt_replay_and_erasure_removes_encrypted_turns(v2_user, demo):  # noqa: F811
    data = start(v2_user)
    key = uuid.uuid4()
    commit_turn(v2_user, data["id"], request_id=key, revision=0, text="Skip", dispatch=False)
    demo[2][0].revoked_at = timezone.now()
    demo[2][0].save(update_fields=["revoked_at"])
    with pytest.raises(StaleTurn):
        commit_turn(v2_user, data["id"], request_id=key, revision=0, text="Skip", dispatch=False)
    erase_account(v2_user.id)
    assert not DemoConversation.objects.filter(pk=data["id"]).exists()
    assert not DemoChatTurn.objects.filter(request_id=key).exists()


def test_customer_stop_needs_no_model_and_no_future_question(v2_user, demo):  # noqa: F811
    data = start(v2_user)
    stopped = commit_turn(
        v2_user,
        data["id"],
        request_id=uuid.uuid4(),
        revision=0,
        text="Stop",
        relay=object(),
        dispatch=False,
    )
    assert stopped["state"]["stage"] == "stopped" and stopped["state"]["pending"] is None
    assert stopped["state"]["question_count"] == 1
    with pytest.raises(ValueError):
        commit_turn(
            v2_user,
            data["id"],
            request_id=uuid.uuid4(),
            revision=1,
            text="Continue",
            dispatch=False,
        )


def test_stage1_fixed_question_after_model_interprets_all_supplied_details(v2_user, demo):  # noqa: F811
    data = start(v2_user)
    relay = Reply(
        people=[{"id": "self", "relationship": "self", "age": 35}],
        city="Pune",
        sum_insured=500000,
        annual_budget=30000,
        plan_type="medical_indemnity",
    )
    result = commit_turn(
        v2_user,
        data["id"],
        request_id=uuid.uuid4(),
        revision=0,
        text="All details",
        relay=relay,
        dispatch=False,
    )
    assert result["state"]["pending"]["field"] == "health_details" and relay.calls == 1
    assert result["state"]["turns"][0]["elapsed_ms"] >= 0
