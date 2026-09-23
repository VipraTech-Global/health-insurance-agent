#!/usr/bin/env python3
"""Apply and verify CoverGuide's least-privilege OmniRoute policy.

The dashboard password is read from OmniRoute's root-only-style runtime env file.
Neither that password nor the management-session cookie is ever printed.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "http://127.0.0.1:20128"
RUNTIME_ENV = Path("/home/akhilesh/.config/omniroute/runtime.env")
COVERGUIDE_KEY_NAME = "CoverGuide"
ALLOWED_MODELS = [
    "gemini/gemini-3.5-flash-lite",
    "gemini/gemini-3.1-flash-lite",
]


def _runtime_value(name: str) -> str:
    for raw_line in RUNTIME_ENV.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.removeprefix("export ").strip() != name:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        return value
    value = os.environ.get("OMNIROUTE_DASHBOARD_PASSWORD", "")
    if value:
        return value
    raise RuntimeError(
        f"{name} is absent from {RUNTIME_ENV}; provide OMNIROUTE_DASHBOARD_PASSWORD "
        "through a protected process environment to reconfigure"
    )


def _unwrap(value: Any) -> Any:
    collection_fields = {"data", "items", "providers", "connections", "keys"}
    while isinstance(value, dict) and set(value) & collection_fields:
        for field in ("data", "items", "providers", "connections", "keys"):
            if field in value and isinstance(value[field], (dict, list)):
                value = value[field]
                break
        else:
            break
    return value


def _json(response: httpx.Response) -> Any:
    response.raise_for_status()
    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"OmniRoute returned non-JSON for {response.request.url.path}") from exc


def _find_coverguide_key(client: httpx.Client) -> dict[str, Any]:
    values = _unwrap(_json(client.get("/api/keys")))
    if not isinstance(values, list):
        raise RuntimeError("OmniRoute returned an unexpected API-key listing")
    matches = [item for item in values if item.get("name") == COVERGUIDE_KEY_NAME]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one {COVERGUIDE_KEY_NAME!r} API key")
    return matches[0]


def _gemini_connection_ids(client: httpx.Client) -> list[str]:
    values = _unwrap(_json(client.get("/api/providers")))
    if not isinstance(values, list):
        raise RuntimeError("OmniRoute returned an unexpected provider listing")
    ids = sorted(
        str(item["id"])
        for item in values
        if item.get("provider") == "gemini" and item.get("isActive", item.get("active", True))
    )
    if len(ids) != 5:
        raise RuntimeError(f"Expected five active Gemini connections; found {len(ids)}")
    return ids


def _expected_key_policy(connection_ids: list[str]) -> dict[str, Any]:
    return {
        "modelAccessMode": "restricted",
        "allowedModels": ALLOWED_MODELS,
        "allowedCombos": [],
        "allowedConnections": connection_ids,
        "noLog": True,
        "autoResolve": False,
        "expiresAt": None,
        "compressionEnabled": False,
        "cacheDefaultMode": "bypass",
    }


def _verify(key: dict[str, Any], settings: dict[str, Any], connection_ids: list[str]) -> None:
    expected = _expected_key_policy(connection_ids)
    for field, expected_value in expected.items():
        actual = key.get(field)
        if field in {"allowedModels", "allowedConnections"}:
            if sorted(actual or []) != sorted(expected_value):
                raise RuntimeError(f"CoverGuide API-key policy mismatch: {field}")
        elif actual != expected_value:
            raise RuntimeError(f"CoverGuide API-key policy mismatch: {field}")

    provider_policy = settings.get("providerStrategies", {}).get("gemini", {})
    if provider_policy != {"fallbackStrategy": "round-robin", "stickyRoundRobinLimit": 1}:
        raise RuntimeError("Gemini round-robin policy was not persisted exactly")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without changing OmniRoute")
    args = parser.parse_args()

    password = _runtime_value("INITIAL_PASSWORD")
    with httpx.Client(base_url=BASE_URL, timeout=20, trust_env=False) as client:
        _json(client.post("/api/auth/login", json={"password": password}))
        key = _find_coverguide_key(client)
        connection_ids = _gemini_connection_ids(client)
        settings = _unwrap(_json(client.get("/api/settings")))
        if not isinstance(settings, dict):
            raise RuntimeError("OmniRoute returned unexpected settings")

        if not args.check:
            key = _unwrap(
                _json(
                    client.patch(
                        f"/api/keys/{key['id']}", json=_expected_key_policy(connection_ids)
                    )
                )
            )
            provider_strategies = dict(settings.get("providerStrategies") or {})
            provider_strategies["gemini"] = {
                "fallbackStrategy": "round-robin",
                "stickyRoundRobinLimit": 1,
            }
            settings = _unwrap(
                _json(
                    client.patch("/api/settings", json={"providerStrategies": provider_strategies})
                )
            )
            key = _find_coverguide_key(client)
            settings = _unwrap(_json(client.get("/api/settings")))

        _verify(key, settings, connection_ids)

    action = "verified" if args.check else "configured and verified"
    print(
        f"CoverGuide OmniRoute policy {action}: five Gemini connections, "
        "two models, round-robin limit 1, no logging/compression/combinations."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
