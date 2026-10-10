"""Building the answer bank: stored chat answers fill only the pairs the bank lacks, and
the answers whose stored drafts the current code reads differently are found offline."""

import json
from io import StringIO
from types import SimpleNamespace

import pytest
from django.core.management import call_command

from apps.adviser_v2.demo.answer_bank import TOPIC_QUESTIONS, remember
from apps.adviser_v2.demo.answer_replay import changed_pairs
from apps.adviser_v2.demo.answers import answer_plan
from apps.adviser_v2.demo.evidence import Packet, digest
from apps.adviser_v2.demo.services import decrypted, encrypted
from apps.adviser_v2.management.commands import build_answer_bank
from apps.adviser_v2.models import DemoPlanAnswer, DemoPlanIndex, DemoQuestion, DemoTopicAnswer
from apps.adviser_v2.tests.test_demo_assembly import source
from apps.adviser_v2.tests.test_demo_contracts import card
from apps.adviser_v2.tests.test_demo_services import demo  # noqa: F401
from apps.adviser_v2.tests.test_topic_answers import engine_result, says

pytestmark = pytest.mark.django_db(transaction=True)
AIR = "Air ambulance expenses are covered up to the sum insured."


def live(release, session, index, result):
    """A finished chat answer to the canonical air ambulance question."""
    question = DemoQuestion(
        session=session, release=release, profile_revision=0, erasure_generation=0
    )
    question.input_ciphertext = encrypted(
        {"question": TOPIC_QUESTIONS["air_ambulance"]}, question.id
    )
    question.save()
    answer = DemoPlanAnswer(question=question, index=index, state="completed")
    answer.result_ciphertext = encrypted(result, answer.id)
    answer.save()


def bank_text(index):
    row = DemoTopicAnswer.objects.get(index=index, topic="air_ambulance")
    return decrypted(row.result_ciphertext, row.id)["answer"]["statements"][0]["text"]


def test_stored_chat_answers_fill_only_the_pairs_the_bank_lacks(demo):  # noqa: F811
    release, session, rows = demo
    assert remember(
        rows[0], "air_ambulance", "P", engine_result(rows[0].plan_key, says("Covered by air."))
    )
    live(release, session, rows[0], engine_result(rows[0].plan_key, says("An older answer.")))
    live(release, session, rows[1], engine_result(rows[1].plan_key, says("Covered if opted.")))
    imported = build_answer_bank.Command().import_stored(release, {r.id: r for r in rows})
    assert imported == 1
    assert bank_text(rows[0]) == "Covered by air."
    assert bank_text(rows[1]) == "Covered if opted."


def plan_index(release, tmp_path, name):
    """A plan index whose bundle holds one air ambulance passage."""
    bundle = {
        "policy_version_id": "plan",
        "name": name,
        "variant": "Default",
        "sections": [source(AIR).payload()],
        "documents": [],
        "navigation": [],
    }
    key = digest(bundle)
    path = tmp_path / f"{key}.json"
    path.write_text(json.dumps({**bundle, "index_id": key}))
    plan_card = card(name)
    index = DemoPlanIndex.objects.create(
        id=key,
        plan_key=plan_card.plan_id,
        insurer=plan_card.insurer,
        name=name,
        plan_type=plan_card.plan_type,
        bundle_path=str(path),
        card=plan_card.model_dump(),
    )
    release.indexes.add(index)
    return index, {**bundle, "index_id": key}


@pytest.fixture
def replayed(demo, tmp_path, monkeypatch):  # noqa: F811
    """Two banked engine answers with the same drafts: one as the current code gives it,
    one as an older checker left it, with every drafted unit rejected."""
    release = demo[0]
    packet = Packet("plan", (source(AIR),), (), 100)
    monkeypatch.setattr(
        "apps.adviser_v2.demo.answers.search",
        lambda **kw: SimpleNamespace(packet=packet, model="test-model", call_ids=[]),
    )
    draft = {
        "schema_version": 3,
        "status": "answered",
        "units": [{"coverage_scope": "base", "benefit": [{"passage": "P1", "quote": AIR}]}],
    }
    relay = SimpleNamespace(
        call=lambda **kw: SimpleNamespace(value=draft, model="test-model", call_ids=[])
    )
    indexes = []
    for name in ("Alpha Cover", "Beta Cover"):
        index, bundle = plan_index(release, tmp_path, name)
        result = answer_plan(bundle, TOPIC_QUESTIONS["air_ambulance"], method="P", relay=relay)
        assert result["status"] == "answered"
        if name == "Beta Cover":
            result = {**result, "status": "not_found", "answer": None}
        assert remember(index, "air_ambulance", "P", result)
        indexes.append(index)
    return release, indexes


def test_a_stored_answer_whose_drafts_now_read_differently_is_found(replayed):
    release, (same, stale) = replayed
    assert changed_pairs([same, stale], ["air_ambulance"], "P") == [
        (stale, "air_ambulance", "not_found", "base")
    ]


def test_a_dry_refresh_lists_the_changed_answers_without_asking_again(replayed, monkeypatch):
    def asked(*args, **kwargs):
        raise AssertionError("A dry run asks the engine nothing.")

    monkeypatch.setattr(build_answer_bank, "answer_plan", asked)
    out = StringIO()
    call_command(
        "build_answer_bank",
        "--topics",
        "air_ambulance",
        "--refresh-changed",
        "--dry-run",
        stdout=out,
    )
    assert "1 stored answers read differently" in out.getvalue()
    assert "Beta Cover (Default) · air_ambulance: not_found → base" in out.getvalue()
