import pytest
from django.core.checks import run_checks

from apps.adviser.ai import RelayFailure
from apps.adviser.providers import omniroute_models, omniroute_problems, provider_config


@pytest.fixture
def omni(settings):
    settings.OMNIROUTE_ENABLED = True
    settings.OMNIROUTE_BASE_URL = "http://127.0.0.1:20128"
    settings.OMNIROUTE_API_KEY = "omni-secret"
    settings.OMNIROUTE_LOGGING_DISABLED_CONFIRMED = True
    settings.OMNIROUTE_MODELS = "gemini/a=a, huggingface/deepseek-ai/V3=deepseek-ai/V3"
    return settings


def test_models_parse_into_requested_to_expected_pairs(omni):
    assert omniroute_models() == {"gemini/a": "a", "huggingface/deepseek-ai/V3": "deepseek-ai/V3"}


@pytest.mark.parametrize(
    "value",
    ["gemini/a", "gemini/a=", "=a", "a=a,a=b", "bad id=a", "a=b c", "*=a", "a=" + "x" * 161],
)
def test_malformed_model_lists_are_rejected(omni, value):
    omni.OMNIROUTE_MODELS = value
    with pytest.raises(RelayFailure) as caught:
        omniroute_models()
    assert caught.value.code == "provider_misconfigured"


def test_relay_config_is_unchanged(settings):
    settings.AI_RELAY_BASE_URL, settings.AI_RELAY_API_KEY = "http://127.0.0.1:8317", "relay-key"
    config = provider_config("cliproxyapi")
    assert (config.base_url, config.api_key) == ("http://127.0.0.1:8317", "relay-key")


def test_disabled_omniroute_has_no_config_and_no_check_errors(settings):
    settings.OMNIROUTE_ENABLED = False
    with pytest.raises(RelayFailure) as caught:
        provider_config("omniroute")
    assert caught.value.code == "provider_disabled"
    assert not [e for e in run_checks() if e.id.startswith("adviser.E10")]


def test_enabled_omniroute_returns_validated_config(omni):
    config = provider_config("omniroute")
    assert (config.base_url, config.api_key) == ("http://127.0.0.1:20128", "omni-secret")


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("OMNIROUTE_BASE_URL", "http://example.com:20128"),
        ("OMNIROUTE_API_KEY", ""),
        ("OMNIROUTE_LOGGING_DISABLED_CONFIRMED", False),
        ("OMNIROUTE_MODELS", ""),
    ],
)
def test_enabled_omniroute_fails_closed_without_naming_values(omni, name, value):
    setattr(omni, name, value)
    problems = omniroute_problems()
    assert len(problems) == 1 and "omni-secret" not in problems[0]
    with pytest.raises(RelayFailure) as caught:
        provider_config("omniroute")
    assert caught.value.code == "provider_misconfigured"
    assert [e for e in run_checks() if e.id.startswith("adviser.E10")]


def test_unknown_provider_is_unsupported():
    with pytest.raises(RelayFailure) as caught:
        provider_config("other")
    assert caught.value.code == "unsupported_route"
