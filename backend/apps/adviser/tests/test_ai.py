import asyncio
import json
from dataclasses import replace

import httpx
import pytest

from apps.adviser.ai import (
    MAX_RESPONSE_BYTES,
    InterviewDraft,
    RelayFailure,
    RelayRoute,
    StrictRelayAdapter,
    StructuredAnswerDraft,
    loopback_url,
    validate_strict_schema,
)


def route(**changes):
    return replace(
        RelayRoute(
            "cliproxyapi", "http://127.0.0.1:8317", "gpt-test", "openai_responses", 32000, 10, True
        ),
        **changes,
    )


def envelope(**changes):
    result = {
        "model": "gpt-test",
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(
                            {
                                "outcome": "needs_input",
                                "introduction": "Confirm your profile.",
                                "claims": [],
                                "follow_up": None,
                            }
                        ),
                    }
                ],
            }
        ],
    }
    result.update(changes)
    return result


@pytest.mark.asyncio
async def test_relay_preserves_full_messages_responses_and_schema():
    captured = []

    def handler(request):
        assert request.url.path == "/v1/responses"
        captured.append(json.loads(request.content))
        return httpx.Response(200, json=envelope())

    messages = [
        {"role": role, "content": text}
        for role, text in [
            ("system", "Keep evidence IDs"),
            ("user", "First question"),
            ("assistant", "First answer"),
            ("user", "Latest question"),
        ]
    ]
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await StrictRelayAdapter(route(), client, "secret").generate_structured_answer(messages, 5)
    assert len(captured) == 1 and captured[0]["input"] == messages
    assert captured[0]["model"] == "gpt-test" and captured[0]["store"] is False
    format = captured[0]["text"]["format"]
    assert format["strict"] and format["type"] == "json_schema"
    validate_strict_schema(format["schema"])
    assert set(format["schema"]["required"]) == {"outcome", "introduction", "claims", "follow_up"}


@pytest.mark.parametrize(
    "status,code",
    [
        (429, "provider_quota"),
        (404, "model_missing"),
        (503, "provider_unavailable"),
        (401, "provider_rejected"),
        (302, "provider_redirect"),
    ],
)
@pytest.mark.asyncio
async def test_provider_errors_are_safe_and_never_retried(status, code):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            status, headers={"Location": "https://example.com"}, text="private-provider-token"
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), follow_redirects=True
    ) as client:
        with pytest.raises(RelayFailure) as failure:
            await StrictRelayAdapter(route(), client, "secret").generate_structured_answer([], 5)
    assert failure.value.code == code and len(calls) == 1
    assert "private" not in str(failure.value)


@pytest.mark.parametrize(
    "body,code",
    [
        (envelope(model="other"), "model_identity_mismatch"),
        (envelope(model=None), "model_identity_mismatch"),
        (envelope(status="incomplete"), "incomplete_response"),
        (envelope(output=[]), "invalid_structured_output"),
        (envelope(output=["malformed"]), "invalid_structured_output"),
        ([], "malformed_response"),
    ],
)
@pytest.mark.asyncio
async def test_rejects_unverifiable_responses(body, code):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))
    ) as client:
        with pytest.raises(RelayFailure) as failure:
            await StrictRelayAdapter(route(), client, "secret").generate_structured_answer([], 5)
    assert failure.value.code == code


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8317",
        "http://127.0.0.1.evil:8317",
        "http://192.168.1.1:8317",
        "http://user:pass@127.0.0.1:8317",
        "http://127.0.0.1:8317/?x=secret",
        "http://127.0.0.1:8317/other",
        "https://127.0.0.1:8317",
        "http://127.0.0.1",
    ],
)
def test_loopback_enforcement(url):
    with pytest.raises(RelayFailure):
        loopback_url(url)


def test_nested_required_schema_rejected():
    schema = StructuredAnswerDraft.model_json_schema()
    schema["$defs"]["ClaimDraft"]["required"].remove("note")
    with pytest.raises(RelayFailure, match="Every schema property"):
        validate_strict_schema(schema)
    validate_strict_schema(InterviewDraft.model_json_schema())


@pytest.mark.asyncio
async def test_size_context_and_absolute_deadline():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, content=b"x" * (MAX_RESPONSE_BYTES + 1))
        )
    ) as client:
        with pytest.raises(RelayFailure) as failure:
            await StrictRelayAdapter(route(), client, "secret").generate_structured_answer([], 5)
        assert failure.value.code == "response_too_large"
        with pytest.raises(RelayFailure) as failure:
            await StrictRelayAdapter(
                route(context_limit=10), client, "secret"
            ).generate_structured_answer([], 5)
        assert failure.value.code == "context_limit"

    async def slow(_):
        await asyncio.sleep(1)
        return httpx.Response(200, json=envelope())

    async with httpx.AsyncClient(transport=httpx.MockTransport(slow)) as client:
        with pytest.raises(RelayFailure) as failure:
            await StrictRelayAdapter(route(), client, "secret").generate_structured_answer([], 0.01)
        assert failure.value.code == "provider_timeout"
