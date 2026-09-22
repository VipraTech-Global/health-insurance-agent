from __future__ import annotations

from pathlib import Path

import pytest
from django.test import Client

from apps.accounts.models import User
from apps.adviser_v2.crypto import commitment_key_ring, encryption_key_ring
from apps.adviser_v2.model_gateway import schema_sha256
from apps.adviser_v2.models import ModelQualification, ModelRoute
from apps.adviser_v2.role_routes import configured_route
from apps.adviser_v2.schemas import CustomerInterpretationV1, RecommendationDraftV1


@pytest.fixture(autouse=True)
def v2_server_keys(settings, tmp_path: Path):
    encoded = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="
    settings.COVERGUIDE_ENCRYPTION_KEYS = f"test-v1:{encoded}"
    settings.COVERGUIDE_COMMITMENT_KEYS = f"test-v1:{encoded}"
    settings.COVERGUIDE_V2_STORAGE_ROOT = tmp_path / "v2"
    encryption_key_ring.cache_clear()
    commitment_key_ring.cache_clear()
    yield
    encryption_key_ring.cache_clear()
    commitment_key_ring.cache_clear()


@pytest.fixture
def qualified_interactive_routes(db: None) -> None:
    for role, output_type in (
        ("fact_interpretation", CustomerInterpretationV1),
        ("recommendation_answer", RecommendationDraftV1),
    ):
        role_route = configured_route(role)
        route, _ = ModelRoute.objects.get_or_create(
            route_key=role_route.route_key,
            defaults={
                "endpoint_profile": role_route.endpoint_profile,
                "requested_model": role_route.requested_model,
                "adapter_version": role_route.configuration["adapter_version"],
                "configuration_sha256": role_route.configuration_sha256,
            },
        )
        ModelQualification.objects.get_or_create(
            route=route,
            schema_name=role,
            schema_sha256=schema_sha256(output_type),
            observed_model=role_route.expected_model,
            result="passed",
            defaults={
                "capabilities": {
                    "structured_output": True,
                    "max_context_tokens_tested": 1,
                    "image_input_tested": False,
                    "image_formats": [],
                    "schema_test_artifact_hashes": [],
                    "identity_exact": True,
                    "latency_ms": 1,
                    "limitations": [],
                }
            },
        )


@pytest.fixture
def v2_user(db: None, qualified_interactive_routes: None) -> User:
    return User.objects.create_user(email="v2@example.com", password="Valid-V2-Password-42")


@pytest.fixture
def v2_client(v2_user: User) -> Client:
    browser = Client(enforce_csrf_checks=True)
    browser.force_login(v2_user)
    browser.get("/api/v1/auth/csrf/")
    return browser
