from __future__ import annotations

import json

import httpx
import pytest
from django.test import override_settings

from apps.adviser import relay_management


def management_settings() -> override_settings:
    return override_settings(
        AI_RELAY_BASE_URL="http://127.0.0.1:8317/v1",
        AI_RELAY_MANAGEMENT_KEY="m" * 64,
    )


def install_transport(monkeypatch, handler) -> list[httpx.Request]:
    requests: list[httpx.Request] = []

    def recording_handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    transport = httpx.MockTransport(recording_handler)
    monkeypatch.setattr(
        relay_management,
        "_build_management_http_client",
        lambda: httpx.Client(transport=transport, timeout=5, trust_env=False),
    )
    return requests


def test_management_client_returns_only_valid_masked_provider_summaries(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Management-Key"] == "m" * 64
        return httpx.Response(
            200,
            json={
                "files": [
                    {
                        "auth_index": "opaque-codex",
                        "name": "codex-private@example.com.json",
                        "provider": "codex",
                        "email": "private@example.com",
                        "disabled": False,
                        "unavailable": False,
                        "updated_at": "2026-08-18T10:00:00Z",
                        "path": "/private/token/path",
                        "access_token": "must-not-escape",
                    },
                    {
                        "auth_index": "other-provider",
                        "name": "gemini.json",
                        "provider": "gemini-cli",
                        "disabled": False,
                    },
                ]
            },
        )

    install_transport(monkeypatch, handler)
    with management_settings():
        credentials = relay_management.RelayManagementClient().credentials("codex")

    assert credentials == (
        relay_management.RelayCredential(
            opaque_id="opaque-codex",
            provider="codex",
            disabled=False,
            unavailable=False,
            masked_identifier="p***@e***.com",
            updated_at="2026-08-18T10:00:00Z",
        ),
    )
    assert "private@example.com" not in repr(credentials)
    assert "must-not-escape" not in repr(credentials)


def test_management_client_resolves_opaque_id_before_status_change(monkeypatch) -> None:
    disabled = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal disabled
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "files": [
                        {
                            "auth_index": "opaque-1",
                            "name": "codex-account.json",
                            "provider": "codex",
                            "disabled": disabled,
                            "unavailable": False,
                        }
                    ]
                },
            )
        payload = json.loads(request.content)
        assert payload == {
            "name": "codex-account.json",
            "auth_index": "opaque-1",
            "disabled": True,
        }
        disabled = True
        return httpx.Response(200, json={"status": "ok", "disabled": True})

    requests = install_transport(monkeypatch, handler)
    with management_settings():
        relay_management.RelayManagementClient().set_disabled("codex", "opaque-1", disabled=True)

    assert [(request.method, request.url.path) for request in requests] == [
        ("GET", "/v0/management/auth-files"),
        ("PATCH", "/v0/management/auth-files/status"),
    ]


def test_management_client_uses_fixed_oauth_paths_and_validates_status(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/codex-auth-url"):
            return httpx.Response(
                200,
                json={
                    "status": "ok",
                    "url": "https://auth.openai.com/oauth/authorize?state=relay-state",
                    "state": "relay-state",
                },
            )
        if request.url.path.endswith("/get-auth-status"):
            return httpx.Response(200, json={"status": "wait"})
        if request.url.path.endswith("/oauth-session"):
            return httpx.Response(200, json={"status": "ok", "cancelled": True})
        return httpx.Response(404)

    requests = install_transport(monkeypatch, handler)
    with management_settings():
        client = relay_management.RelayManagementClient()
        started = client.start_oauth("codex")
        assert client.oauth_status(started.state) == "wait"
        client.cancel_oauth(started.state)

    assert [request.method for request in requests] == ["GET", "GET", "DELETE"]
    assert dict(requests[0].url.params) == {"is_webui": "true"}
    assert dict(requests[1].url.params) == {"state": "relay-state"}


@pytest.mark.parametrize("provider", ("anthropic", "../codex", "", "vertex"))
def test_management_client_rejects_non_allowlisted_provider(provider: str) -> None:
    with (
        management_settings(),
        pytest.raises(relay_management.RelayManagementError, match="Unsupported"),
    ):
        relay_management.RelayManagementClient().credentials(provider)


@pytest.mark.parametrize(
    "response",
    (
        httpx.Response(302, headers={"location": "https://example.com"}),
        httpx.Response(200, content=b"not-json"),
        httpx.Response(200, content=b"x" * (relay_management.MAX_MANAGEMENT_RESPONSE_BYTES + 1)),
    ),
)
def test_management_client_rejects_redirect_malformed_and_oversized_responses(
    monkeypatch, response: httpx.Response
) -> None:
    install_transport(monkeypatch, lambda _request: response)
    with management_settings(), pytest.raises(relay_management.RelayManagementError):
        relay_management.RelayManagementClient().credentials("codex")


def test_management_key_is_separate_and_required() -> None:
    with (
        override_settings(
            AI_RELAY_BASE_URL="http://127.0.0.1:8317/v1",
            AI_RELAY_API_KEY="provider-key-is-not-management-key",
            AI_RELAY_MANAGEMENT_KEY="",
        ),
        pytest.raises(relay_management.RelayManagementError, match="not configured"),
    ):
        relay_management.RelayManagementClient()
