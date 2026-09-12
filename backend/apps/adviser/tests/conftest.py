import pytest

from apps.accounts.models import User
from apps.adviser.models import RouteConfiguration, RouteQualification
from apps.adviser.relay_routes import configuration_hash, route_values


@pytest.fixture
def qualified(db):
    values = route_values("gpt-6-astra")
    route = RouteConfiguration.objects.create(
        **values, configuration_hash=configuration_hash(values), qualification_state="qualified"
    )
    RouteQualification.objects.create(
        route=route, tested_configuration_hash=route.configuration_hash, state="qualified"
    )
    return route


@pytest.fixture
def user(db):
    return User.objects.create_user(email="ai@example.com", password="Valid-Test-Password42")
