from types import SimpleNamespace

from apps.adviser_v2.demo.contracts import PersonInput, Profile
from apps.adviser_v2.demo.needs import normalize


def profile(text="OPD cover for me"):
    return Profile(
        people=[PersonInput(id="me", relationship="self", age_days=35 * 365)],
        sum_insured=None,
        city=None,
        zone=None,
        plan_type="medical_indemnity",
        typed_needs=text,
    )


class FakeRelay:
    def __init__(self, values):
        self.values, self.calls = values, 0

    def call(self, **kwargs):
        self.calls += 1
        assert kwargs["stage"] == "needs_mapping"
        return SimpleNamespace(
            value={"schema_version": 1, "needs": self.values}, model="gpt-5.6-luna"
        )


def test_map_once_for_unchanged_input_and_preserve_person_and_text():
    relay = FakeRelay(
        [{"original_text": "OPD cover for me", "person_id": "me", "field": "opd", "mapped": True}]
    )
    first = normalize(profile(), relay=relay)
    second = normalize(profile(), first.model_dump(), relay=relay)
    assert relay.calls == 1 and second == first
    assert second.normalized_needs[0].person_id == "me"
    normalize(profile("OPD cover for me, overseas cover too"), first.model_dump(), relay=relay)
    assert relay.calls == 2


def test_unmapped_text_and_invalid_person_remain_visible():
    relay = FakeRelay([{"original_text": "OPD", "person_id": "me", "field": "opd", "mapped": True}])
    normalized = normalize(profile(), relay=relay)
    assert any(not n.mapped for n in normalized.normalized_needs)
    relay.values[0]["person_id"] = "stranger"
    normalized = normalize(profile(), relay=relay)
    assert len(normalized.normalized_needs) == 1 and not normalized.normalized_needs[0].mapped
    assert normalized.normalized_needs[0].original_text == profile().typed_needs
