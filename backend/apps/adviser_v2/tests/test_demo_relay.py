"""Section 15 acceptance against an isolated keyspace in the slice Redis."""

import json
import multiprocessing
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
import redis

from apps.adviser_v2.demo.relay import (
    LUNA,
    SONNET,
    InvalidOutput,
    ModelChanged,
    Relay,
    RelayUnavailable,
    SharedRelayState,
    quota_error,
    retry_after,
)

SCHEMA = {
    "type": "object",
    "properties": {"ok": {"type": "boolean"}},
    "additionalProperties": False,
    "required": ["ok"],
}


@pytest.fixture
def state(settings):
    if settings.REDIS_URL != "redis://127.0.0.1:6401/0":
        pytest.skip("Run through scripts/star_slice.sh test for isolated Redis acceptance.")
    client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    client.ping()
    value = SharedRelayState(client, prefix="coverguide:test:relay:" + uuid.uuid4().hex)
    yield value
    keys = list(client.scan_iter(value.prefix + ":*"))
    if keys:
        client.delete(*keys)


def reply(model, text='{"ok":true}', *, status=200, error=None):
    body = {
        "model": model,
        "status": "completed",
        "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}],
        "usage": {"input_tokens": 4, "output_tokens": 3},
    }
    return httpx.Response(
        status,
        json=error or body,
        request=httpx.Request("POST", "http://127.0.0.1:8317/v1/responses"),
    )


def invoke(relay, **kwargs):
    return relay.call(
        instructions="Return ok.",
        messages=[{"role": "user", "content": "check"}],
        schema=SCHEMA,
        stage="test",
        **kwargs,
    )


def limited():
    return {"error": {"type": "usage_limit_reached", "message": "Weekly usage limit reached"}}


def test_quota_switch_and_sonnet_json_repair_are_independent(state, tmp_path):
    calls = []

    def post(url, *, json, **kwargs):
        calls.append(json)
        if len(calls) == 1:
            return reply(LUNA, status=429, error=limited())
        if len(calls) == 2:
            return reply(SONNET, "ok=true")
        return reply(SONNET)

    result = invoke(Relay(state, "test", tmp_path, post=post))
    assert result.value == {"ok": True} and result.model == SONNET
    assert [c["model"] for c in calls] == [LUNA, SONNET, SONNET]
    assert all(isinstance(c["input"], list) for c in calls)
    assert all('"required": ["ok"]' in c["instructions"] for c in calls)
    assert SharedRelayState(state.redis, prefix=state.prefix).model() == SONNET
    records = [
        json.loads(line) for line in (tmp_path / "relay-calls.jsonl").read_text().splitlines()
    ]
    assert records[0]["status"] == "usage_limit"
    assert all(
        set(("queue_ms", "model_ms", "total_ms", "observed_model")) <= r.keys() for r in records
    )


def test_transient_429_never_switches(state, tmp_path, monkeypatch):
    calls = []

    def post(url, *, json, **kwargs):
        calls.append(json["model"])
        if len(calls) == 1:
            return reply(
                LUNA,
                status=429,
                error={"error": {"code": "rate_limit_exceeded", "message": "Try later"}},
            )
        return reply(LUNA)

    # Clear just this request's persisted retry delay; do not change limiter time.
    original_now = state.now
    monkeypatch.setattr(state, "now", lambda: original_now() + 60 * len(calls))
    invoke(Relay(state, "test", tmp_path, post=post))
    assert calls == [LUNA, LUNA] and state.model() == LUNA


def test_reset_and_both_limited(state, tmp_path, monkeypatch):
    now = state.now()
    state.trip(LUNA, {"error": {**limited()["error"], "resets_at": now + 20}})
    assert state.model() == SONNET
    state.trip(SONNET, limited())
    assert state.model() is None
    with pytest.raises(RelayUnavailable, match="paused"):
        invoke(
            Relay(state, "test", tmp_path, post=lambda *a, **k: pytest.fail("No call while paused"))
        )
    monkeypatch.setattr(state, "now", lambda: now + 21)
    assert state.model() == LUNA


def test_unknown_reset_single_token_probe_restores_luna(state, tmp_path, monkeypatch):
    now = state.now()
    state.trip(LUNA, limited())
    monkeypatch.setattr(state, "now", lambda: now + 1801)
    calls = []

    def post(url, *, json, **kwargs):
        calls.append(json)
        return reply(LUNA)

    invoke(Relay(state, "test", tmp_path, post=post))
    assert calls[0]["max_output_tokens"] == 1
    assert len(calls) == 2 and state.model() == LUNA


def test_model_identity_and_invalid_json_fail_closed(state, tmp_path):
    with pytest.raises(InvalidOutput, match="identity"):
        invoke(Relay(state, "test", tmp_path, post=lambda *a, **k: reply("other-model")))
    calls = []

    def post(*a, **k):
        calls.append(1)
        return reply(LUNA, '{"ok":"wrong type"}')

    with pytest.raises(InvalidOutput, match="after one repair"):
        invoke(Relay(state, "test", tmp_path, post=post))
    assert len(calls) == 2


def test_pinned_pair_cannot_cross_switch(state, tmp_path):
    with pytest.raises(ModelChanged):
        invoke(
            Relay(
                state,
                "test",
                tmp_path,
                post=lambda *a, **k: reply(LUNA, status=429, error=limited()),
            ),
            expected_model=LUNA,
        )
    assert state.model() == SONNET


def _process_slot(url, prefix, priority, delay, gated=False):
    state = SharedRelayState(redis.Redis.from_url(url, decode_responses=True), prefix=prefix)
    if gated:
        state.redis.incr(state.key("test-ready"))
        deadline = time.monotonic() + 30
        while not state.redis.get(state.key("test-start")):
            if time.monotonic() > deadline:
                raise TimeoutError("The parent did not open the test start barrier.")
            time.sleep(0.01)
    with state.slot(priority, deadline=time.monotonic() + 15):
        count = state.redis.incr(state.key("test-inflight"))
        state.redis.rpush(state.key("test-counts"), count)
        model = state.model()
        if gated:
            deadline = time.monotonic() + 15
            while int(state.redis.hget(state.key("metrics"), "peak") or 0) < 6:
                if time.monotonic() > deadline:
                    raise TimeoutError("Six processes could not acquire shared slots.")
                time.sleep(0.01)
        time.sleep(delay)
        state.redis.decr(state.key("test-inflight"))
    return model


def test_cross_process_cap_holds_across_shared_switch(state):
    context = multiprocessing.get_context("spawn")
    with context.Pool(8) as pool:
        jobs = [
            pool.apply_async(
                _process_slot, ("redis://127.0.0.1:6401/0", state.prefix, "live", 0.18, True)
            )
            for _ in range(16)
        ]
        deadline = time.monotonic() + 30
        while int(state.redis.get(state.key("test-ready")) or 0) < 8:
            assert time.monotonic() < deadline, "Spawned processes did not reach the barrier."
            time.sleep(0.01)
        state.trip(LUNA, limited())
        state.redis.set(state.key("test-start"), "1")
        models = [job.get(timeout=20) for job in jobs]
    assert set(models) == {SONNET}
    assert max(map(int, state.redis.lrange(state.key("test-counts"), 0, -1))) <= 6
    assert int(state.redis.hget(state.key("metrics"), "peak")) == 6


def test_background_reserves_two_live_slots(state):
    def background():
        with state.slot("background", deadline=time.monotonic() + 5):
            time.sleep(0.3)

    with ThreadPoolExecutor(max_workers=7) as executor:
        jobs = [executor.submit(background) for _ in range(6)]
        deadline = time.monotonic() + 3
        while state.redis.zcard(state.key("background")) < 4 and time.monotonic() < deadline:
            time.sleep(0.01)
        assert state.redis.zcard(state.key("background")) == 4
        with state.slot("live", deadline=deadline) as queued:
            assert queued < 0.2
        for job in jobs:
            job.result()


@pytest.mark.parametrize(
    "body,expected",
    [
        ({"error": {"message": "429 Too many requests"}}, False),
        ({"error": {"code": "insufficient_quota", "message": "Buy more credits"}}, False),
        ({"error": {"message": "Usage limit reached", "resets_in_seconds": 60}}, True),
        ({"error": {"type": "usage_limit_reached"}}, True),
        ({"error": {"code": "other_code", "type": "usage_limit_reached"}}, True),
        ({"error": {"code": "usage_limit_reached", "type": "other_type"}}, True),
        ({"output": "weekly limit reached"}, False),
    ],
)
def test_quota_classification(body, expected):
    assert quota_error(body, now=100)[0] is expected


def test_retry_after():
    assert retry_after("9", now=0) == 9
    assert retry_after("Thu, 01 Jan 1970 00:01:00 GMT", now=10) == 50
    assert retry_after("invalid", now=0) == 0


def test_unrecognised_429_warns_after_thirty_minutes_without_switch(state, monkeypatch, caplog):
    now = state.now()
    state.observe_429(LUNA)
    monkeypatch.setattr(state, "now", lambda: now + 1799)
    state.observe_429(LUNA)
    assert not caplog.records
    monkeypatch.setattr(state, "now", lambda: now + 1801)
    state.observe_429(LUNA)
    state.observe_429(LUNA)
    assert len(caplog.records) == 1
    assert "LUNA RELAY STALLED" in caplog.text
    assert state.redis.xlen(state.key("warnings")) == 1
    assert state.model() == LUNA
    state.clear_429(LUNA)
    assert state.redis.get(state.key("luna-429-since")) is None


def test_nested_pageindex_json_uses_one_json_repair(state, tmp_path):
    calls = []

    def post(*args, **kwargs):
        calls.append(kwargs["json"])
        value = {"response": '{"valid": true}' if len(calls) == 2 else '{"valid":'}
        return reply(LUNA, json.dumps(value))

    schema = {
        "type": "object",
        "properties": {"response": {"type": "string"}},
        "required": ["response"],
        "additionalProperties": False,
    }
    value = Relay(state, "test", tmp_path, post=post).call(
        instructions="Return nested JSON.",
        messages=[{"role": "user", "content": "Task"}],
        schema=schema,
        stage="pageindex_internal",
        value_validator=lambda result: json.loads(result["response"]),
    )
    assert len(calls) == 2 and json.loads(value.value["response"]) == {"valid": True}
