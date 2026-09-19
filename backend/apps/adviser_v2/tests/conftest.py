from __future__ import annotations

from pathlib import Path

import pytest
from django.test import Client

from apps.accounts.models import User
from apps.adviser_v2.crypto import commitment_key_ring, encryption_key_ring


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
def v2_user(db: None) -> User:
    return User.objects.create_user(email="v2@example.com", password="Valid-V2-Password-42")


@pytest.fixture
def v2_client(v2_user: User) -> Client:
    browser = Client(enforce_csrf_checks=True)
    browser.force_login(v2_user)
    browser.get("/api/v1/auth/csrf/")
    return browser
