import hashlib
import ipaddress
import json

from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpRequest, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import User


def _body(request: HttpRequest) -> dict[str, object]:
    try:
        value = json.loads(request.body or b"{}")
    except json.JSONDecodeError as exc:
        raise ValidationError("Request body must be valid JSON") from exc
    if not isinstance(value, dict):
        raise ValidationError("Request body must be an object")
    return value


def _error(code: str, message: str, status: int) -> JsonResponse:
    return JsonResponse({"error": {"code": code, "message": message}}, status=status)


def _increment_limiter(key: str, limit: int) -> bool:
    if cache.add(key, 1, timeout=60):
        return False
    try:
        return cache.incr(key) > limit
    except ValueError:
        cache.set(key, 1, timeout=60)
        return False


def _rate_limited(request: HttpRequest, scope: str, email: str, *, limit: int) -> bool:
    peer = request.META.get("REMOTE_ADDR", "unknown")
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "").strip()
    try:
        trusted_proxy = ipaddress.ip_address(peer).is_loopback
    except ValueError:
        trusted_proxy = False
    address = forwarded if trusted_proxy and forwarded and "," not in forwarded else peer
    identity = hashlib.sha256(email.encode()).hexdigest() if email else "missing"
    address_limited = _increment_limiter(f"{scope}:address:{address}"[:240], limit * 5)
    identity_limited = _increment_limiter(f"{scope}:identity:{identity}"[:240], limit)
    return address_limited or identity_limited


@ensure_csrf_cookie
@require_GET
def csrf_state(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"csrfToken": get_token(request)})


@require_POST
def register(request: HttpRequest) -> JsonResponse:
    try:
        data = _body(request)
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        if _rate_limited(request, "register-attempt", email, limit=5):
            return _error("rate_limited", "Too many registration attempts. Try again shortly.", 429)
        validate_password(password)
        user = User.objects.create_user(email=email, password=password)
    except (ValidationError, ValueError) as exc:
        message = exc.messages[0] if isinstance(exc, ValidationError) else str(exc)
        return _error("invalid_registration", message, 400)
    except IntegrityError:
        return _error("email_in_use", "An account already uses this email.", 409)
    login(request, user)
    return JsonResponse({"user": {"id": str(user.id), "email": user.email}}, status=201)


@require_POST
def login_view(request: HttpRequest) -> JsonResponse:
    try:
        data = _body(request)
    except ValidationError as exc:
        return _error("invalid_json", exc.messages[0], 400)
    email = str(data.get("email", "")).lower()
    if _rate_limited(request, "login-attempt", email, limit=10):
        return _error("rate_limited", "Too many login attempts. Try again shortly.", 429)
    user = authenticate(request, email=email, password=data.get("password"))
    if user is None or user.deleted_at is not None:
        return _error("invalid_credentials", "Email or password is incorrect.", 401)
    login(request, user)
    return JsonResponse({"user": {"id": str(user.id), "email": user.email}})


@require_POST
def logout_view(request: HttpRequest) -> JsonResponse:
    logout(request)
    return JsonResponse({"ok": True})


@require_GET
def session_view(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False})
    return JsonResponse(
        {"authenticated": True, "user": {"id": str(request.user.id), "email": request.user.email, "is_staff": request.user.is_staff}}
    )


@require_POST
def change_password(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return _error("not_authenticated", "Authentication is required.", 401)
    try:
        data = _body(request)
        current = str(data.get("current_password", ""))
        password = str(data.get("new_password", ""))
        if not request.user.check_password(current):
            return _error("invalid_password", "Current password is incorrect.", 400)
        validate_password(password, request.user)
        request.user.set_password(password)
        request.user.save(update_fields=["password"])
        update_session_auth_hash(request, request.user)
    except ValidationError as exc:
        return _error("invalid_password", exc.messages[0], 400)
    return JsonResponse({"ok": True})


@require_http_methods(["DELETE"])
def delete_account(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return _error("not_authenticated", "Authentication is required.", 401)
    from apps.adviser.models import AnswerArtifact, Conversation, RecommendationSnapshot

    user = request.user
    if settings.COVERGUIDE_V2_ENABLED:
        from apps.adviser_v2.services.erasure import erase_account, has_v2_private_data

        if has_v2_private_data(user.id):
            erase_account(user.id)
            logout(request)
            return JsonResponse({}, status=204)
    logout(request)
    with transaction.atomic():
        RecommendationSnapshot.objects.filter(owner=user).delete()
        AnswerArtifact.objects.filter(attempt__turn__conversation__owner=user).delete()
        Conversation.objects.filter(owner=user).delete()
        user.delete()
    return JsonResponse({}, status=204)
