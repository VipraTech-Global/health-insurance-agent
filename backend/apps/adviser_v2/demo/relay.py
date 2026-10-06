"""One subscription relay, cross-process admission and explicit quota failover.

No prompt/response bodies are logged. The exact quota error is retained in Redis for
the operator. JSON/schema repair is independent of downstream evidence correction.
"""

from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import logging
import os
import random
import re
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import httpx
import jsonschema
import redis

LUNA = "gpt-5.6-luna"
SONNET = "claude-sonnet-5"
MODELS = (LUNA, SONNET)
ENDPOINT = "http://127.0.0.1:8317/v1/responses"
PROBE_INTERVAL = 1800
ADAPTER_VERSION = "subscription-responses/1"
LOG = logging.getLogger(__name__)
AUDIT_CONTEXT = contextvars.ContextVar("demo_relay_audit", default=None)


class RelayUnavailable(RuntimeError):
    """A transient operational failure, never evidence that a benefit is absent."""


class ModelChanged(RelayUnavailable):
    """A pinned bake-off pair must be rerun, without bypassing shared routing."""


class InvalidOutput(ValueError):
    """The allowed local JSON repair failed."""


@dataclass(frozen=True)
class RelayResult:
    value: dict[str, Any]
    model: str
    call_ids: tuple[str, ...]
    usage: dict[str, Any]


def quota_error(body: object, *, now: float) -> tuple[bool, float | None]:
    """Do not mistake a plain 429/rate-limit or insufficient paid credits for quota."""
    if not isinstance(body, dict) or not isinstance(body.get("error"), (dict, str)):
        return False, None
    error = body["error"]
    fields = error if isinstance(error, dict) else {"message": error}
    codes = {str(fields.get(key, "")).casefold() for key in ("code", "type")}
    message = str(fields.get("message", error)).casefold()
    reset = None
    for key in ("resets_at", "reset_at", "reset_time"):
        value = fields.get(key)
        if value is not None:
            try:
                reset = float(value)
                if reset > 10**12:
                    reset /= 1000
            except (TypeError, ValueError):
                try:
                    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                    if parsed.tzinfo:
                        reset = parsed.timestamp()
                except ValueError:
                    pass
            if reset is not None:
                break
    if reset is None and fields.get("resets_in_seconds") is not None:
        try:
            reset = now + max(0, float(fields["resets_in_seconds"]))
        except (ValueError, TypeError):
            pass
    explicit = bool(codes & {"usage_limit_reached", "weekly_limit_reached", "usage_limit_exceeded"})
    explicit |= bool(
        re.search(
            r"(?:weekly|usage|subscription)\s+limit.{0,50}(?:reached|exhausted|exceeded)", message
        )
    )
    explicit |= bool(
        reset is not None and "limit" in message and ("usage" in message or "quota" in message)
    )
    return explicit, reset


def retry_after(value: str | None, *, now: float) -> float:
    if not value:
        return 0
    try:
        return max(0, float(value))
    except ValueError:
        try:
            return max(0, parsedate_to_datetime(value).timestamp() - now)
        except (ValueError, TypeError, OverflowError):
            return 0


ACQUIRE = """
local clock = redis.call('TIME')
local now = tonumber(clock[1]) + tonumber(clock[2]) / 1000000
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', now)
redis.call('ZREMRANGEBYSCORE', KEYS[3], '-inf', now)
local cap = tonumber(redis.call('GET', KEYS[4]) or ARGV[4])
cap = math.min(cap, tonumber(ARGV[4]), 6)
if ARGV[2] == 'live' then redis.call('ZADD', KEYS[3], now + 30, ARGV[1]) end
if redis.call('ZCARD', KEYS[1]) >= cap then return 0 end
if ARGV[2] ~= 'live' and (redis.call('ZCARD', KEYS[2]) >= math.min(4, cap)
  or redis.call('ZCARD', KEYS[3]) > 0) then return 0 end
redis.call('ZADD', KEYS[1], now + tonumber(ARGV[3]), ARGV[1])
if ARGV[2] ~= 'live' then redis.call('ZADD', KEYS[2], now + tonumber(ARGV[3]), ARGV[1]) end
redis.call('ZREM', KEYS[3], ARGV[1])
local active = redis.call('ZCARD', KEYS[1])
local peak = tonumber(redis.call('HGET', KEYS[5], 'peak') or 0)
redis.call('HSET', KEYS[5], 'peak', math.max(peak, active))
redis.call('HINCRBY', KEYS[5], 'admissions', 1)
return 1
"""
RENEW = """
local clock = redis.call('TIME')
local expiry = tonumber(clock[1]) + tonumber(clock[2]) / 1000000 + tonumber(ARGV[2])
if not redis.call('ZSCORE', KEYS[1], ARGV[1]) then return 0 end
redis.call('ZADD', KEYS[1], 'XX', expiry, ARGV[1])
redis.call('ZADD', KEYS[2], 'XX', expiry, ARGV[1])
return 1
"""


class SharedRelayState:
    def __init__(
        self, client: redis.Redis, *, prefix: str = "coverguide:demo:relay:v1", cap: int = 6
    ):
        if not 1 <= cap <= 6:
            raise ValueError("Relay concurrency must be between one and six.")
        self.redis, self.prefix, self.cap = client, prefix, cap

    def key(self, suffix: str) -> str:
        return self.prefix + ":" + suffix

    def now(self) -> float:
        seconds, micros = self.redis.time()
        return seconds + micros / 1_000_000

    def model(self) -> str | None:
        """Known resets restore Luna without an extra request; unknown resets need probes."""
        with self.redis.lock(self.key("state-lock"), timeout=10, blocking_timeout=5):
            state = json.loads(self.redis.get(self.key("state")) or "{}")
            now = self.now()
            changed = False
            for model, block in list(state.items()):
                if block.get("reset_at") is not None and block["reset_at"] <= now:
                    del state[model]
                    changed = True
            if changed:
                self.redis.set(self.key("state"), json.dumps(state))
            return next((m for m in MODELS if m not in state), None)

    def trip(self, model: str, body: dict) -> None:
        if model not in MODELS:
            raise ValueError("Model is outside the subscription allowlist.")
        limited, reset = quota_error(body, now=self.now())
        if not limited:
            raise ValueError("Transient failures cannot switch models.")
        with self.redis.lock(self.key("state-lock"), timeout=10, blocking_timeout=5):
            state = json.loads(self.redis.get(self.key("state")) or "{}")
            now = self.now()
            # Expired provider reset values must not cause a hot retry loop.
            reset = reset if reset is not None and reset > now else None
            state[model] = {"reset_at": reset, "probe_at": reset or now + PROBE_INTERVAL}
            self.redis.set(self.key("state"), json.dumps(state))
            self.redis.xadd(
                self.key("switches"),
                {
                    "model": model,
                    "at": str(now),
                    "error": json.dumps(body["error"]),
                    "reset_at": str(reset),
                },
            )

    def recover(self, model: str) -> None:
        with self.redis.lock(self.key("state-lock"), timeout=10, blocking_timeout=5):
            state = json.loads(self.redis.get(self.key("state")) or "{}")
            state.pop(model, None)
            self.redis.set(self.key("state"), json.dumps(state))

    def defer_probe(self, model: str) -> None:
        with self.redis.lock(self.key("state-lock"), timeout=10, blocking_timeout=5):
            state = json.loads(self.redis.get(self.key("state")) or "{}")
            if model in state:
                state[model]["probe_at"] = self.now() + PROBE_INTERVAL
                self.redis.set(self.key("state"), json.dumps(state))

    def throttle(self) -> None:
        # Reduce on repeated transient failures, recover after a quiet minute.
        failures = self.redis.incr(self.key("recent-errors"))
        self.redis.expire(self.key("recent-errors"), 60)
        if failures >= 2:
            self.redis.set(self.key("cap"), max(1, self.cap - min(failures - 1, 4)), ex=60)

    def observe_429(self, model: str) -> None:
        if model != LUNA or self.model() != LUNA:
            return
        now = self.now()
        self.redis.set(self.key("luna-429-since"), str(now), nx=True, ex=86400)
        since = float(self.redis.get(self.key("luna-429-since")) or now)
        if now - since >= 1800 and self.redis.set(
            self.key("luna-429-warning"), "1", nx=True, ex=1800
        ):
            message = (
                "LUNA RELAY STALLED: HTTP 429 failures have persisted for over 30 minutes "
                "without a usage-limit switch. Inspect the relay error format; an unrecognised "
                "subscription-limit response may be blocking work. No automatic model override was made."
            )
            LOG.critical(message)
            self.redis.xadd(self.key("warnings"), {"at": str(now), "message": message})

    def clear_429(self, model: str) -> None:
        if model == LUNA:
            self.redis.delete(self.key("luna-429-since"), self.key("luna-429-warning"))

    @contextlib.contextmanager
    def slot(self, priority: str, *, deadline: float) -> Iterator[float]:
        if priority not in {"live", "background"}:
            raise ValueError("Unknown relay priority.")
        token = str(uuid.uuid4())
        started = time.monotonic()
        keys = [self.key(k) for k in ("active", "background", "waiting", "cap", "metrics")]
        stop = threading.Event()
        thread = None
        try:
            while not self.redis.eval(ACQUIRE, len(keys), *keys, token, priority, 240, self.cap):
                if time.monotonic() >= deadline:
                    raise RelayUnavailable("Relay queue deadline expired.")
                time.sleep(0.03 + random.random() * 0.03)

            def heartbeat():
                while not stop.wait(20):
                    try:
                        if not self.redis.eval(RENEW, 2, *keys[:2], token, 240):
                            return
                    except redis.RedisError:
                        return

            thread = threading.Thread(target=heartbeat, daemon=True)
            thread.start()
            yield time.monotonic() - started
        finally:
            stop.set()
            if thread:
                thread.join(timeout=1)
            with self.redis.pipeline(transaction=True) as pipe:
                for key in keys[:3]:
                    pipe.zrem(key, token)
                pipe.execute()


def strict_schema(schema: dict) -> dict:
    schema = json.loads(json.dumps(schema))

    def visit(item):
        if isinstance(item, dict):
            if item.get("type") == "object":
                item["additionalProperties"] = False
                item["required"] = list(item.get("properties", {}))
            for value in item.values():
                visit(value)
        elif isinstance(item, list):
            for value in item:
                visit(value)

    visit(schema)
    return schema


class Relay:
    def __init__(
        self, state: SharedRelayState, api_key: str, log_root: Path, *, post: Callable = httpx.post
    ):
        if not api_key:
            raise RelayUnavailable("The local relay credential is unavailable.")
        self.state, self.api_key, self.log_root, self.post = state, api_key, log_root, post

    @classmethod
    def configured(cls) -> Relay:
        from django.conf import settings

        if settings.AI_RELAY_BASE_URL.rstrip("/") != ENDPOINT.removesuffix("/v1/responses"):
            raise RelayUnavailable("Demo calls require the authorized loopback relay.")
        if settings.DATABASES["default"]["NAME"] not in {
            "coverguide_star_slice",
            "test_coverguide_star_slice",
        }:
            raise RelayUnavailable("Demo calls require the isolated database.")
        if settings.REDIS_URL != "redis://127.0.0.1:6401/0":
            raise RelayUnavailable("Demo calls require the isolated Redis.")
        client = redis.Redis.from_url(
            settings.REDIS_URL, decode_responses=True, socket_timeout=5, socket_connect_timeout=5
        )
        return cls(
            SharedRelayState(client, cap=int(os.getenv("COVERGUIDE_RELAY_CONCURRENCY", "6"))),
            settings.AI_RELAY_API_KEY,
            Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer",
        )

    def record(self, record: dict) -> None:
        self.log_root.mkdir(parents=True, exist_ok=True)
        data = (json.dumps(record, ensure_ascii=False) + "\n").encode()
        fd = os.open(
            self.log_root / "relay-calls.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600
        )
        try:
            os.write(fd, data)
        finally:
            os.close(fd)

    def _request(
        self,
        model: str,
        payload: dict,
        *,
        stage: str,
        priority: str,
        deadline: float,
        pinned: bool = False,
        probe: bool = False,
        transport_retry: int = 0,
        json_retry: int = 0,
    ) -> tuple[dict, dict]:
        record = {
            "call_id": str(uuid.uuid4()),
            "stage": stage,
            "model": model,
            "adapter": ADAPTER_VERSION,
            "priority": priority,
            "status": "failed",
            "queue_ms": 0,
            "model_ms": 0,
            "usage": {},
            "observed_model": None,
            "started_at": self.state.now(),
            "transport_retry": transport_retry,
            "json_retry": json_retry,
        }
        record["scope"] = AUDIT_CONTEXT.get()
        started = time.monotonic()
        try:
            with self.state.slot(priority, deadline=deadline) as queue_time:
                record["queue_ms"] = round(queue_time * 1000)
                # Calls waiting in the limiter must observe a switch before dispatch.
                if not probe and self.state.model() != model:
                    raise ModelChanged("Shared model changed before dispatch.")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RelayUnavailable("Relay call deadline expired.")
                model_started = time.monotonic()
                try:
                    response = self.post(
                        ENDPOINT,
                        json=payload,
                        headers={"Authorization": "Bearer " + self.api_key},
                        timeout=min(180, remaining),
                    )
                finally:
                    record["model_ms"] = round((time.monotonic() - model_started) * 1000)
                if len(response.content) > 2_000_000:
                    raise InvalidOutput("Oversized relay response.")
                try:
                    body = response.json()
                except ValueError:
                    body = {}
                limited, _ = quota_error(body, now=self.state.now())
                if limited:
                    self.state.trip(model, body)
                    record["status"] = "usage_limit"
                    raise ModelChanged("Subscription usage limit reached.")
                response.raise_for_status()
                if not isinstance(body, dict) or body.get("model") != model:
                    raise InvalidOutput("Relay model identity mismatch.")
                record["observed_model"] = body["model"]
                record["usage"] = body.get("usage", {})
                if not probe and body.get("status") != "completed":
                    raise InvalidOutput("Incomplete relay output.")
                record["status"] = "completed"
                self.state.clear_429(model)
                return body, record
        except httpx.HTTPStatusError as exc:
            record["http_status"] = exc.response.status_code
            if exc.response.status_code == 429:
                self.state.observe_429(model)
            raise
        finally:
            record["total_ms"] = round((time.monotonic() - started) * 1000)
            self.record(record)

    def probe_due(self, *, deadline: float) -> None:
        lock = self.state.redis.lock(self.state.key("probe-lock"), timeout=240, blocking=False)
        if not lock.acquire():
            return
        try:
            state = json.loads(self.state.redis.get(self.state.key("state")) or "{}")
            for model in MODELS:
                if model not in state or state[model]["probe_at"] > self.state.now():
                    continue
                self.state.defer_probe(model)
                try:
                    self._request(
                        model,
                        {
                            "model": model,
                            "input": [{"role": "user", "content": "OK"}],
                            "max_output_tokens": 1,
                            "store": False,
                            "stream": False,
                            "reasoning": {"effort": "low"},
                        },
                        stage="quota_probe",
                        priority="background",
                        deadline=deadline,
                        probe=True,
                    )
                except (ModelChanged, httpx.HTTPError, InvalidOutput, RelayUnavailable):
                    continue
                self.state.recover(model)
        finally:
            lock.release()

    def call(
        self,
        *,
        instructions: str,
        messages: list[dict],
        schema: dict,
        stage: str,
        priority: str = "background",
        max_tokens: int = 4096,
        timeout: float = 240,
        expected_model: str | None = None,
        value_validator: Callable | None = None,
    ) -> RelayResult:
        if not isinstance(messages, list) or not all(isinstance(m, dict) for m in messages):
            raise TypeError("Responses input must be a message list.")
        if expected_model is not None and expected_model not in MODELS:
            raise ValueError("Model is outside the subscription allowlist.")
        if not 1 <= max_tokens <= 8192:
            raise ValueError("Bound output to 1..8192 tokens.")
        schema = strict_schema(schema)
        validator = jsonschema.Draft202012Validator(schema)
        validator.check_schema(schema)
        deadline = time.monotonic() + timeout
        self.probe_due(deadline=deadline)
        repair = None
        call_ids: list[str] = []
        totals: dict[str, Any] = {}
        request_id = hashlib.sha256(
            json.dumps([instructions, messages, schema, stage], sort_keys=True).encode()
        ).hexdigest()
        retry_key = self.state.key("retry:" + request_id)
        transport_retries = 0
        switches = 0
        while time.monotonic() < deadline:
            model = self.state.model()
            if model is None:
                raise RelayUnavailable(
                    "Both subscription models are limited; AI work is paused pending a probe/reset."
                )
            if expected_model and expected_model != model:
                raise ModelChanged("Bake-off pair model changed; rerun both arms.")
            retained = json.loads(self.state.redis.get(retry_key) or "{}")
            delay = max(0, retained.get("next_at", 0) - self.state.now())
            if delay:
                if delay >= deadline - time.monotonic():
                    raise RelayUnavailable("Relay retry is deferred beyond this request deadline.")
                time.sleep(delay)
            inputs = list(messages)
            if repair:
                inputs.append(
                    {
                        "role": "user",
                        "content": "Return valid JSON matching the schema. Local validation error: "
                        + repair,
                    }
                )
            payload = {
                "model": model,
                "input": inputs,
                "instructions": instructions
                + "\nReturn JSON only, matching this schema exactly:\n"
                + json.dumps(schema, sort_keys=True),
                "reasoning": {"effort": "low"},
                "max_output_tokens": max_tokens,
                "stream": False,
                "store": False,
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "demo_output",
                        "strict": True,
                        "schema": schema,
                    }
                },
            }
            try:
                body, record = self._request(
                    model,
                    payload,
                    stage=stage,
                    priority=priority,
                    deadline=deadline,
                    pinned=bool(expected_model),
                    transport_retry=transport_retries,
                    json_retry=int(repair is not None),
                )
                call_ids.append(record["call_id"])
                totals = body.get("usage", {})
            except ModelChanged:
                if expected_model:
                    raise
                switches += 1
                if switches > 4:
                    raise RelayUnavailable(
                        "Subscription routing is changing; retry later."
                    ) from None
                continue
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else 0
                if status not in {0, 408, 429, 500, 502, 503, 504}:
                    raise RelayUnavailable(f"Relay rejected the request (HTTP {status}).") from None
                transport_retries += 1
                self.state.throttle()
                header = (
                    exc.response.headers.get("Retry-After")
                    if isinstance(exc, httpx.HTTPStatusError)
                    else None
                )
                delay = max(
                    retry_after(header, now=self.state.now()),
                    min(30, 2**transport_retries) + random.random(),
                )
                self.state.redis.set(
                    retry_key,
                    json.dumps(
                        {
                            "attempts": retained.get("attempts", 0) + 1,
                            "next_at": self.state.now() + delay,
                            "status": status,
                        }
                    ),
                    ex=86400,
                )
                if transport_retries >= 4:
                    raise RelayUnavailable(
                        "Relay transport is temporarily unavailable; retry state retained."
                    ) from None
                continue
            try:
                output = "".join(
                    c.get("text", "")
                    for item in body.get("output", [])
                    for c in item.get("content", [])
                    if c.get("type") == "output_text"
                )
                value = json.loads(output)
                validator.validate(value)
                if not isinstance(value, dict):
                    raise InvalidOutput("The output must be an object.")
                if value_validator is not None:
                    value_validator(value)
            except (ValueError, jsonschema.ValidationError, TypeError, AttributeError) as exc:
                if repair is not None:
                    raise InvalidOutput(
                        "Relay JSON/schema validation failed after one repair."
                    ) from None
                # No provider output or policy text in the repair error or logs.
                repair = (
                    "Invalid JSON, including any task-requested JSON inside the response string."
                    if isinstance(exc, json.JSONDecodeError)
                    else "JSON does not match the required schema."
                )
                continue
            self.state.redis.delete(retry_key)
            return RelayResult(value, model, tuple(call_ids), totals)
        raise RelayUnavailable("Relay deadline expired.")
