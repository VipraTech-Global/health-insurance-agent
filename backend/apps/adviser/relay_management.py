from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx
from django.conf import settings

from .ai import loopback_url as _loopback_api_url

MANAGED_PROVIDERS = frozenset({"codex"})
MAX_MANAGEMENT_RESPONSE_BYTES = 262_144
MANAGEMENT_TIMEOUT_SECONDS = 5.0


class RelayManagementError(RuntimeError):
    """A safe relay-management failure without provider secrets or paths."""


@dataclass(frozen=True, slots=True)
class RelayCredential:
    opaque_id: str
    provider: str
    disabled: bool
    unavailable: bool
    masked_identifier: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class RelayOAuthStart:
    authorization_url: str
    state: str


@dataclass(frozen=True, slots=True)
class _CredentialRecord:
    credential: RelayCredential
    name: str


def _provider(value: str) -> str:
    if value not in MANAGED_PROVIDERS:
        raise RelayManagementError("Unsupported subscription provider")
    return value


def _bounded_string(value: object, *, maximum: int = 256) -> str:
    if not isinstance(value, str):
        return ""
    normalized = value.strip()
    if not normalized or len(normalized) > maximum or any(ord(char) < 32 for char in normalized):
        return ""
    return normalized


def _masked_identifier(value: object) -> str:
    identifier = _bounded_string(value, maximum=320)
    if not identifier:
        return "Account ••••"
    if "@" in identifier:
        local, domain = identifier.rsplit("@", 1)
        domain_name, separator, suffix = domain.rpartition(".")
        masked_domain = f"{domain_name[:1]}***{separator}{suffix}" if separator else "***"
        return f"{local[:1]}***@{masked_domain}"
    return f"{identifier[:3]}***{identifier[-2:]}" if len(identifier) > 5 else "Account ••••"


def _management_base_url() -> str:
    relay_url = _loopback_api_url(str(settings.AI_RELAY_BASE_URL).strip())
    parsed = urlsplit(relay_url)
    return urlunsplit((parsed.scheme, parsed.netloc, "/v0/management", "", ""))


def _build_management_http_client() -> httpx.Client:
    return httpx.Client(
        timeout=httpx.Timeout(MANAGEMENT_TIMEOUT_SECONDS, connect=2.0),
        follow_redirects=False,
        trust_env=False,
    )


class RelayManagementClient:
    def __init__(self) -> None:
        self.base_url = _management_base_url()
        self.management_key = str(settings.AI_RELAY_MANAGEMENT_KEY).strip()
        if len(self.management_key) < 32:
            raise RelayManagementError("Relay account management is not configured")

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = _build_management_http_client()
        response: httpx.Response | None = None
        try:
            request_kwargs: dict[str, Any] = {
                "params": params,
                "headers": {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-Management-Key": self.management_key,
                },
            }
            if payload is not None:
                request_kwargs["json"] = payload
            request = client.build_request(method, f"{self.base_url}/{path}", **request_kwargs)
            response = client.send(request, stream=True)
            if response.is_redirect:
                raise RelayManagementError("The relay returned an unsupported redirect")
            if response.status_code >= 400:
                raise RelayManagementError("The relay account operation failed safely")
            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > MAX_MANAGEMENT_RESPONSE_BYTES:
                    raise RelayManagementError("The relay account response exceeded the size limit")
                chunks.append(chunk)
        except RelayManagementError:
            raise
        except httpx.HTTPError as error:
            raise RelayManagementError("The relay account service is unavailable") from error
        finally:
            if response is not None:
                response.close()
            client.close()
        try:
            decoded = json.loads(b"".join(chunks))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise RelayManagementError(
                "The relay account service returned malformed data"
            ) from error
        if not isinstance(decoded, dict):
            raise RelayManagementError("The relay account service returned malformed data")
        return decoded

    def _records(self, provider: str) -> tuple[_CredentialRecord, ...]:
        selected_provider = _provider(provider)
        files = self._request("GET", "auth-files").get("files")
        if not isinstance(files, list) or len(files) > 100:
            raise RelayManagementError("The relay account service returned malformed data")
        records: list[_CredentialRecord] = []
        seen: set[str] = set()
        for value in files:
            if not isinstance(value, dict):
                raise RelayManagementError("The relay account service returned malformed data")
            record_provider = _bounded_string(value.get("provider") or value.get("type")).casefold()
            if record_provider != selected_provider:
                continue
            opaque_id = _bounded_string(value.get("auth_index"))
            name = _bounded_string(value.get("name"))
            disabled = value.get("disabled")
            unavailable = value.get("unavailable", False)
            if (
                not opaque_id
                or opaque_id in seen
                or not name.endswith(".json")
                or "/" in name
                or "\\" in name
                or not isinstance(disabled, bool)
                or not isinstance(unavailable, bool)
            ):
                raise RelayManagementError("The relay account service returned malformed data")
            seen.add(opaque_id)
            identifier = value.get("email") or value.get("account") or value.get("label")
            updated_at = _bounded_string(value.get("updated_at") or value.get("modtime"))
            records.append(
                _CredentialRecord(
                    credential=RelayCredential(
                        opaque_id=opaque_id,
                        provider=selected_provider,
                        disabled=disabled,
                        unavailable=unavailable,
                        masked_identifier=_masked_identifier(identifier),
                        updated_at=updated_at,
                    ),
                    name=name,
                )
            )
        return tuple(records)

    def credentials(self, provider: str) -> tuple[RelayCredential, ...]:
        return tuple(record.credential for record in self._records(provider))

    def _record(self, provider: str, opaque_id: str) -> _CredentialRecord:
        selected_id = _bounded_string(opaque_id)
        if not selected_id:
            raise RelayManagementError("The relay credential identifier is invalid")
        matches = [
            record
            for record in self._records(provider)
            if record.credential.opaque_id == selected_id
        ]
        if len(matches) != 1:
            raise RelayManagementError("The relay credential is no longer available")
        return matches[0]

    def set_disabled(self, provider: str, opaque_id: str, *, disabled: bool) -> None:
        record = self._record(provider, opaque_id)
        result = self._request(
            "PATCH",
            "auth-files/status",
            payload={
                "name": record.name,
                "auth_index": record.credential.opaque_id,
                "disabled": disabled,
            },
        )
        if result.get("status") != "ok" or result.get("disabled") is not disabled:
            raise RelayManagementError("The relay account operation was not confirmed")

    def delete(self, provider: str, opaque_id: str) -> None:
        record = self._record(provider, opaque_id)
        result = self._request("DELETE", "auth-files", params={"name": record.name})
        if result.get("status") != "ok":
            raise RelayManagementError("The relay account operation was not confirmed")

    def start_oauth(self, provider: str) -> RelayOAuthStart:
        selected_provider = _provider(provider)
        endpoint = "codex-auth-url" if selected_provider == "codex" else "anthropic-auth-url"
        result = self._request("GET", endpoint, params={"is_webui": "true"})
        state = _bounded_string(result.get("state"), maximum=128)
        authorization_url = _bounded_string(result.get("url"), maximum=4096)
        parsed = urlsplit(authorization_url)
        if (
            result.get("status") != "ok"
            or not state
            or parsed.scheme != "https"
            or parsed.hostname != "auth.openai.com"
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise RelayManagementError("The relay returned an invalid authorization link")
        return RelayOAuthStart(authorization_url=authorization_url, state=state)

    def oauth_status(self, state: str) -> str:
        selected_state = _bounded_string(state, maximum=128)
        if not selected_state:
            raise RelayManagementError("The relay login state is invalid")
        result = self._request("GET", "get-auth-status", params={"state": selected_state})
        status = result.get("status")
        if not isinstance(status, str) or status not in {"wait", "ok", "error"}:
            raise RelayManagementError("The relay returned an invalid login status")
        return status

    def cancel_oauth(self, state: str) -> None:
        selected_state = _bounded_string(state, maximum=128)
        if not selected_state:
            raise RelayManagementError("The relay login state is invalid")
        result = self._request("DELETE", "oauth-session", params={"state": selected_state})
        if result.get("status") != "ok" or not isinstance(result.get("cancelled"), bool):
            raise RelayManagementError("The relay login cancellation was not confirmed")
