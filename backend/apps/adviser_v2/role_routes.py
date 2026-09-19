"""Operator-selected model route per v2 role. Customers never choose a route.

A role runs on the exact relay model by default. The two interactive roles may instead be
pointed at an allowlisted OmniRoute model with ``omniroute:<requested id>``. Extraction and review
also handle private uploads, so they stay relay-only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from django.conf import settings

from apps.adviser.ai import RelayFailure
from apps.adviser.providers import omniroute_models, provider_config

RELAY_ENDPOINT_PROFILE = "shared-job-in-loopback-relay"
OMNIROUTE_ENDPOINT_PROFILE = "omniroute-loopback"
ADAPTER_VERSION = "strict-relay-v2/1"
OMNIROUTE_PREFIX = "omniroute:"
# Byte bound for the whole history; sized for the smallest allowlisted context (~128k tokens).
OMNIROUTE_CONTEXT_LIMIT_BYTES = 400_000

# schema name -> (relay model setting, OmniRoute route setting or None when relay-only)
ROLE_SETTINGS: dict[str, tuple[str, str | None]] = {
    "fact_interpretation": (
        "COVERGUIDE_CUSTOMER_INTERPRETATION_MODEL",
        "COVERGUIDE_CUSTOMER_INTERPRETATION_ROUTE",
    ),
    "policy_extraction": ("COVERGUIDE_POLICY_EXTRACTION_MODEL", None),
    "policy_review": ("COVERGUIDE_POLICY_REVIEW_MODEL", None),
    "recommendation_answer": (
        "COVERGUIDE_FINAL_EXPLANATION_MODEL",
        "COVERGUIDE_FINAL_EXPLANATION_ROUTE",
    ),
}


@dataclass(frozen=True)
class RoleRoute:
    relay_type: str
    requested_model: str
    expected_model: str

    @classmethod
    def relay(cls, model: str) -> RoleRoute:
        return cls("cliproxyapi", model, model)

    @property
    def is_omniroute(self) -> bool:
        return self.relay_type == "omniroute"

    @property
    def endpoint_profile(self) -> str:
        return OMNIROUTE_ENDPOINT_PROFILE if self.is_omniroute else RELAY_ENDPOINT_PROFILE

    @property
    def configuration(self) -> dict[str, str]:
        config = {
            "endpoint_profile": self.endpoint_profile,
            "base_url": provider_config(self.relay_type).base_url,
            "requested_model": self.requested_model,
            "adapter_version": ADAPTER_VERSION,
        }
        if self.is_omniroute:
            config["expected_model"] = self.expected_model
        return config

    @property
    def configuration_sha256(self) -> str:
        return hashlib.sha256(
            json.dumps(self.configuration, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    @property
    def route_key(self) -> str:
        digest = self.configuration_sha256
        # OmniRoute keys carry the full digest; relay keys keep their historical short form.
        return (
            f"omniroute:{digest}" if self.is_omniroute else f"{self.requested_model}:{digest[:16]}"
        )


def configured_route(schema_name: str) -> RoleRoute:
    """Resolve the route the operator configured for one role; fail closed, never fall back."""

    model_setting, route_setting = ROLE_SETTINGS[schema_name]
    relay_model = getattr(settings, model_setting)
    override = str(getattr(settings, route_setting, "") or "").strip() if route_setting else ""
    if not override:
        return RoleRoute.relay(relay_model)
    if not override.startswith(OMNIROUTE_PREFIX):
        raise RelayFailure("provider_misconfigured", f"{route_setting} must be omniroute:<id>.")
    provider_config("omniroute")  # raises when disabled or misconfigured
    requested = override.removeprefix(OMNIROUTE_PREFIX)
    expected = omniroute_models().get(requested)
    if expected is None:
        raise RelayFailure(
            "provider_misconfigured", f"{route_setting} names a model outside OMNIROUTE_MODELS."
        )
    return RoleRoute("omniroute", requested, expected)
