import pytest
from django.test import Client

from apps.adviser import relay_routes
from apps.adviser.ai import RelayFailure
from apps.adviser.models import AIPreference, ModelCallAttempt, RouteConfiguration
from apps.adviser.relay_routes import (
    choose_model,
    configuration_hash,
    model_choices,
    qualify_model,
    route_snapshot,
    route_values,
    usable_route,
)

REQUESTED, REPORTED = "gemini/gemini-test", "gemini-test"


@pytest.fixture
def omni(settings):
    settings.DEBUG = True
    settings.OMNIROUTE_ENABLED = True
    settings.OMNIROUTE_BASE_URL = "http://127.0.0.1:20128"
    settings.OMNIROUTE_API_KEY = "omni-secret"
    settings.OMNIROUTE_LOGGING_DISABLED_CONFIRMED = True
    settings.COVERGUIDE_LOCAL_OMNIROUTE_PILOT_ACK = True
    settings.OMNIROUTE_MODELS = f"{REQUESTED}={REPORTED}"
    return settings


def qualified_omni_route(monkeypatch):
    async def passing(route, output, instruction):
        assert route.relay_type == "omniroute" and route.expected_model == REPORTED
        return REPORTED, {"input_tokens": 1, "output_tokens": 1}

    monkeypatch.setattr(relay_routes, "probe", passing)
    monkeypatch.setattr(
        relay_routes, "discover_models", lambda: pytest.fail("relay catalogue must not be used")
    )
    return qualify_model(REQUESTED, "omniroute")


def test_relay_route_values_and_hash_are_unchanged(settings):
    settings.AI_RELAY_BASE_URL = "http://127.0.0.1:8317"
    values = route_values("gpt-6-astra")
    assert values["relay_type"] == "cliproxyapi"
    assert "expected_identity" not in values["capabilities"]
    assert configuration_hash(values) == configuration_hash(
        route_values("gpt-6-astra", "cliproxyapi")
    )


def test_omniroute_route_pins_its_declared_identity_in_the_hash(omni):
    values = route_values(REQUESTED, "omniroute")
    assert values["relay_type"] == "omniroute" and values["base_url"] == "http://127.0.0.1:20128"
    assert values["capabilities"]["expected_identity"] == REPORTED
    omni.OMNIROUTE_MODELS = f"{REQUESTED}=other"
    assert configuration_hash(route_values(REQUESTED, "omniroute")) != configuration_hash(values)


def test_omniroute_route_values_fail_closed(omni):
    with pytest.raises(RelayFailure):
        route_values("gemini/not-listed", "omniroute")
    omni.OMNIROUTE_ENABLED = False
    with pytest.raises(RelayFailure):
        route_values(REQUESTED, "omniroute")


@pytest.mark.django_db(transaction=True)
def test_omniroute_qualification_is_selectable_until_the_provider_is_disabled(
    user, omni, monkeypatch
):
    qualification = qualified_omni_route(monkeypatch)
    route = qualification.route
    assert qualification.state == "qualified" and route.relay_type == "omniroute"
    assert ModelCallAttempt.objects.filter(route=route).count() == 2
    assert ModelCallAttempt.objects.first().upstream_reported_model == REPORTED
    snapshot = route_snapshot(route)
    assert (snapshot.relay_type, snapshot.model, snapshot.expected_model) == (
        "omniroute",
        REQUESTED,
        REPORTED,
    )
    assert model_choices(user.id)["models"] == [
        {"route_id": str(route.id), "model": REQUESTED, "provider": "omniroute"}
    ]
    choose_model(user.id, route.id)
    assert AIPreference.objects.get(user=user).route == route
    omni.OMNIROUTE_ENABLED = False
    assert not usable_route(route)
    result = model_choices(user.id)
    assert result["models"] == [] and not result["selected_available"]
    with pytest.raises(RelayFailure):
        choose_model(user.id, route.id)


@pytest.mark.django_db(transaction=True)
def test_changed_allowlist_identity_makes_an_old_route_unusable(user, omni, monkeypatch):
    route = qualified_omni_route(monkeypatch).route
    omni.OMNIROUTE_MODELS = f"{REQUESTED}=other"
    assert not usable_route(RouteConfiguration.objects.get(pk=route.pk))


def test_qualifying_a_disabled_or_unlisted_omniroute_model_is_refused(omni, db):
    with pytest.raises(RelayFailure):
        qualify_model("gemini/not-listed", "omniroute")
    omni.OMNIROUTE_ENABLED = False
    with pytest.raises(RelayFailure):
        qualify_model(REQUESTED, "omniroute")


def test_v1_admin_ai_routes_are_retired(user):
    user.is_staff = True
    user.save()
    browser = Client()
    browser.force_login(user)
    assert browser.get("/api/v1/admin/ai-relay/").status_code == 404
    assert browser.post("/api/v1/admin/ai-relay/qualifications/").status_code == 404
