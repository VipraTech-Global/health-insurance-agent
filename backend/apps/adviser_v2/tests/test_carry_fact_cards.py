import hashlib
import json
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.adviser_v2.demo.citations import card_anchor, price_anchor
from apps.adviser_v2.demo.evidence import digest
from apps.adviser_v2.demo.price_compare import load_chart
from apps.adviser_v2.demo.services import bundle_for
from apps.adviser_v2.models import DemoFactCard, DemoPlanIndex, DemoRelease
from apps.adviser_v2.tests.test_demo_contracts import citation, packet
from apps.adviser_v2.tests.test_page_charts import chart

pytestmark = pytest.mark.django_db

ROOM = "Room rent is covered at actuals."
CHART_TEXT = "\n".join(
    [
        ROOM,
        *dict.fromkeys(c["text"] for c in chart()["cells"].values()),
        "Zone 1 Delhi, Mumbai",
        "Zone 7 Rest of Rajasthan, Bihar",
    ]
)


@pytest.fixture
def report(tmp_path, settings, monkeypatch):
    settings.COVERGUIDE_REPORT_ROOT = str(tmp_path)
    isolated = SimpleNamespace(
        DATABASES={"default": {"NAME": "coverguide_star_slice"}},
        COVERGUIDE_REPORT_ROOT=str(tmp_path),
    )
    for command in ("carry_fact_cards", "publish_fact_release"):
        monkeypatch.setattr(f"apps.adviser_v2.management.commands.{command}.settings", isolated)
    return tmp_path / "ten-insurer"


def index(root, text, *, plan="plan", tables=()):
    bundle = {
        "policy_version_id": plan,
        "sections": [{**packet(text).sections[0].payload(), "plan_id": plan}],
        "documents": [],
        "pages": [],
        "navigation": [],
        "tables": list(tables),
    }
    key = digest(bundle)
    path = root / "indexes" / (key + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**bundle, "index_id": key}))
    return DemoPlanIndex.objects.create(
        id=key, plan_key=plan, insurer="Insurer", name=plan, variant="Gold", bundle_path=str(path)
    )


def published_card(root, row, *, priced=False):
    """A card in run "source" pinned to the row, optionally with a validated chart."""
    run = root / "fact-card-runs" / "source"
    value = {
        "plan_id": row.plan_key,
        "index_version": row.id,
        "room_limit": {"citations": [citation(ROOM).model_dump()]},
    }
    if priced:
        raw = json.dumps(chart(row.id)).encode()
        frozen = run / "prices" / (hashlib.sha256(raw).hexdigest() + ".json")
        frozen.parent.mkdir(parents=True, exist_ok=True)
        frozen.write_bytes(raw)
        value.update(pricing_artifact=str(frozen), pricing_sha256=hashlib.sha256(raw).hexdigest())
    identity = digest(value)
    value["card_version"] = identity
    audit = run / "cards" / (identity + ".json")
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(
        json.dumps(
            {
                "card": value,
                "fields": {"room_limit": {"index_version": row.id}},
                "provenance": {"room_limit": {"index": row.id, "source_result": "kept"}},
                "source_card_version": "earlier",
            }
        )
    )
    DemoFactCard.objects.create(id=identity, index=row, card=value, audit_path=str(audit))
    return {"id": identity, "index": row.id, "name": row.name, "variant": row.variant}


def source_run(root, *items):
    run = root / "fact-card-runs" / "source"
    (run / "complete.json").write_text(json.dumps({"cards": list(items), "manifest": {"m": 1}}))


def test_carry_moves_a_card_and_its_chart_to_the_reread_edition_and_publishes(report):
    old = index(report, CHART_TEXT)
    other = index(report, ROOM, plan="other")
    moved_item, kept_item = published_card(report, old, priced=True), published_card(report, other)
    source_run(report, moved_item, kept_item)
    new = index(report, CHART_TEXT, tables=[{"id": "t1", "cells": {}}])

    call_command("carry_fact_cards", source_run="source", run_id="carried", index=[new.id])

    run = report / "fact-card-runs" / "carried"
    complete = json.loads((run / "complete.json").read_text())
    assert complete["cards"][1] == kept_item
    carried = complete["cards"][0]
    assert carried["index"] == new.id and carried["id"] != moved_item["id"]
    row = DemoFactCard.objects.get(pk=carried["id"])
    assert row.index_id == new.id and row.card["index_version"] == new.id
    assert row.card["card_version"] == row.id
    assert card_anchor(row.card, bundle_for(new), citation(ROOM))["quote"] == ROOM
    priced = load_chart(row.card)
    assert priced == {**json.loads(json.dumps(chart())), "index_id": new.id}
    assert price_anchor(priced, bundle_for(new), new.plan_key, citation("6,638"))
    audit = json.loads((run / "cards" / (row.id + ".json")).read_text())
    assert audit["fields"]["room_limit"]["index_version"] == new.id
    assert audit["provenance"]["room_limit"] == {"index": new.id, "source_result": "kept"}
    assert audit["carried_from"] == {
        "card_version": moved_item["id"],
        "index_version": old.id,
        "run_id": "source",
    }
    assert "carried_from" not in row.card
    # The old card and its index stay as they were, for live conversations and rollback.
    assert DemoFactCard.objects.get(pk=moved_item["id"]).card["index_version"] == old.id

    call_command("carry_fact_cards", source_run="source", run_id="carried", index=[new.id])
    assert json.loads((run / "complete.json").read_text()) == complete
    assert DemoFactCard.objects.count() == 3

    DemoRelease.objects.create(method="H", manifest_sha256="a" * 64, bakeoff={}, active=True)
    call_command("publish_fact_release", run_id="carried", inactive=True)
    release = DemoRelease.objects.get(active=False)
    assert set(release.indexes.values_list("id", flat=True)) == {new.id, other.id}


def test_carry_refuses_a_card_whose_quotation_no_longer_opens(report):
    old = index(report, ROOM)
    source_run(report, published_card(report, old))
    changed = index(report, "Room rent is covered up to 1% of the sum insured.")
    with pytest.raises(CommandError, match="no longer opens"):
        call_command("carry_fact_cards", source_run="source", run_id="carried", index=[changed.id])
    assert DemoFactCard.objects.count() == 1


def test_carry_needs_a_source_card_for_the_same_plan_and_variant(report):
    old = index(report, ROOM)
    source_run(report, published_card(report, old))
    stranger = index(report, ROOM, plan="other")
    with pytest.raises(CommandError, match="no other source card"):
        call_command("carry_fact_cards", source_run="source", run_id="carried", index=[stranger.id])
    with pytest.raises(CommandError, match="no other source card"):
        call_command("carry_fact_cards", source_run="source", run_id="carried", index=[old.id])
    with pytest.raises(CommandError, match="Unknown index"):
        call_command("carry_fact_cards", source_run="source", run_id="carried", index=["f" * 64])
