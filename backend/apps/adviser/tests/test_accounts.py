import json
import uuid

import pytest
from django.test import Client, RequestFactory
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.views import _rate_limited
from apps.adviser.services import create_conversation


def csrf(client: Client) -> str:
    client.get(reverse("csrf"))
    return client.cookies["csrftoken"].value


def test_identity_limit_survives_forwarded_address_rotation() -> None:
    factory = RequestFactory()
    email = f"limit-{uuid.uuid4()}@example.com"
    results = []
    for index in range(11):
        request = factory.get(
            "/",
            REMOTE_ADDR="127.0.0.1",
            HTTP_X_FORWARDED_FOR=f"198.51.100.{index + 1}",
        )
        results.append(_rate_limited(request, "test-login", email, limit=10))
    assert results[:10] == [False] * 10
    assert results[10] is True


@pytest.mark.django_db
def test_register_rotates_session_and_account_deletion_removes_personal_data() -> None:
    browser = Client(enforce_csrf_checks=True)
    response = browser.post(
        reverse("register"),
        data=json.dumps(
            {
                "email": "delete-me@example.com",
                "password": "Valid-Deletion-Password-42",
            }
        ),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf(browser),
    )
    assert response.status_code == 201
    user = User.objects.get(email="delete-me@example.com")
    conversation = create_conversation(user.id, "Private medical discussion")

    response = browser.delete(
        reverse("delete-account"),
        HTTP_X_CSRFTOKEN=csrf(browser),
    )
    assert response.status_code == 204
    assert not User.objects.filter(id=user.id).exists()
    assert not conversation.__class__.objects.filter(id=conversation.id).exists()


@pytest.mark.django_db
def test_password_change_keeps_session_authenticated() -> None:
    user = User.objects.create_user(
        email="password@example.com",
        password="Valid-Old-Password-42",
    )
    browser = Client(enforce_csrf_checks=True)
    browser.force_login(user)
    response = browser.post(
        reverse("password"),
        data=json.dumps(
            {
                "current_password": "Valid-Old-Password-42",
                "new_password": "Valid-New-Password-43",
            }
        ),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf(browser),
    )
    assert response.status_code == 200
    assert browser.get(reverse("session")).json()["authenticated"] is True
