"""Server-side AI provider configuration: credentials, the OmniRoute allowlist and validation.

Keys are read from settings at call time and never stored in route rows or logged.
"""

import re
from dataclasses import dataclass

from django.conf import settings
from django.core.checks import Error, register

from .ai import RelayFailure, loopback_url

OMNIROUTE_MODEL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}")


@dataclass(frozen=True)
class ProviderConfig:
    relay_type: str
    base_url: str
    api_key: str


def omniroute_models() -> dict[str, str]:
    """Return the allowlist as ``{requested id: expected reported id}``; raise if malformed."""

    result: dict[str, str] = {}
    for entry in (part.strip() for part in str(settings.OMNIROUTE_MODELS).split(",")):
        if not entry:
            continue
        requested, separator, expected = (piece.strip() for piece in entry.partition("="))
        if (
            not separator
            or not OMNIROUTE_MODEL_ID.fullmatch(requested)
            or not OMNIROUTE_MODEL_ID.fullmatch(expected)
            or requested in result
        ):
            raise RelayFailure(
                "provider_misconfigured",
                "OMNIROUTE_MODELS must list unique requested-id=reported-id pairs.",
            )
        result[requested] = expected
    return result


def omniroute_problems() -> list[str]:
    """Human-readable settings problems; messages name settings only, never their values."""

    problems: list[str] = []
    try:
        loopback_url(str(settings.OMNIROUTE_BASE_URL))
    except RelayFailure:
        problems.append("OMNIROUTE_BASE_URL must be a literal loopback HTTP address and port.")
    if not settings.OMNIROUTE_API_KEY:
        problems.append("OMNIROUTE_API_KEY is required.")
    if not settings.OMNIROUTE_LOGGING_DISABLED_CONFIRMED:
        problems.append(
            "OMNIROUTE_LOGGING_DISABLED_CONFIRMED=1 is required once request logging and "
            "prompt compression are disabled on the gateway key."
        )
    if not settings.COVERGUIDE_LOCAL_OMNIROUTE_PILOT_ACK:
        problems.append(
            "COVERGUIDE_LOCAL_OMNIROUTE_PILOT_ACK=1 is required for local pilot data."
        )
    if not settings.DEBUG:
        problems.append("OmniRoute pilot routing is restricted to DEBUG/local mode.")
    try:
        if not omniroute_models():
            problems.append("OMNIROUTE_MODELS must list at least one model.")
    except RelayFailure:
        problems.append("OMNIROUTE_MODELS must list unique requested-id=reported-id pairs.")
    return problems


def provider_config(relay_type: str) -> ProviderConfig:
    if relay_type == "cliproxyapi":
        return ProviderConfig(relay_type, settings.AI_RELAY_BASE_URL, settings.AI_RELAY_API_KEY)
    if relay_type == "omniroute":
        if not settings.OMNIROUTE_ENABLED:
            raise RelayFailure("provider_disabled", "The OmniRoute provider is not enabled.")
        if problems := omniroute_problems():
            raise RelayFailure("provider_misconfigured", problems[0])
        return ProviderConfig(
            relay_type, loopback_url(settings.OMNIROUTE_BASE_URL), settings.OMNIROUTE_API_KEY
        )
    raise RelayFailure("unsupported_route", "This route is not enabled.")


@register()
def check_omniroute_settings(app_configs: object, **kwargs: object) -> list[Error]:
    if not settings.OMNIROUTE_ENABLED:
        return []
    return [
        Error(problem, id=f"adviser.E10{index}")
        for index, problem in enumerate(omniroute_problems(), start=1)
    ]
