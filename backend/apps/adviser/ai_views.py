from dataclasses import asdict
from typing import Any

from django.contrib.auth.models import AnonymousUser
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .ai import RelayFailure
from .relay_accounts import (
    RelayAccountError,
    cancel_account_login,
    disconnect_account,
    forget_account,
    poll_account_login,
    provider_account_summary,
    restore_account,
    start_account_login,
)
from .relay_management import RelayManagementError
from .relay_routes import choose_model, discover_models, model_choices, qualify_model


class ModelChoiceSerializer(serializers.Serializer[dict[str, Any]]):
    route_id = serializers.UUIDField()
    model = serializers.CharField()


class ModelListSerializer(serializers.Serializer[dict[str, Any]]):
    models = ModelChoiceSerializer(many=True)
    selected_route_id = serializers.UUIDField(allow_null=True)
    selected_model = serializers.CharField(allow_null=True)
    selected_available = serializers.BooleanField()


class PreferenceInputSerializer(serializers.Serializer[dict[str, Any]]):
    route_id = serializers.UUIDField()


class QualificationInputSerializer(serializers.Serializer[dict[str, Any]]):
    model = serializers.RegexField(r"^gpt-[a-zA-Z0-9._-]{1,190}$")


class QualificationSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    route_id = serializers.UUIDField()
    model = serializers.CharField()
    state = serializers.CharField()
    results = serializers.DictField()


class AccountSerializer(serializers.Serializer[dict[str, Any]]):
    provider = serializers.CharField()
    label = serializers.CharField()  # type: ignore[assignment]
    state = serializers.CharField()
    masked_identifier = serializers.CharField()
    has_active_account = serializers.BooleanField()
    can_restore = serializers.BooleanField()
    login_in_progress = serializers.BooleanField()
    action_required = serializers.BooleanField()


class RelayStatusSerializer(serializers.Serializer[dict[str, Any]]):
    account = AccountSerializer()
    discovered_models = serializers.ListField(child=serializers.CharField())
    catalogue_error = serializers.CharField(allow_null=True)
    laptop_wide = serializers.BooleanField()


class AccountActionSerializer(serializers.Serializer[dict[str, Any]]):
    action = serializers.ChoiceField(
        choices=["connect", "status", "cancel", "disconnect", "restore", "forget"]
    )


class AccountActionResultSerializer(serializers.Serializer[dict[str, Any]]):
    account = AccountSerializer(required=False)
    provider = serializers.CharField(required=False)
    authorization_url = serializers.URLField(required=False)
    expires_at = serializers.IntegerField(required=False)


class SafeRelayView(APIView):
    def handle_exception(self, exc: Exception) -> Response:
        if isinstance(exc, (RelayFailure, RelayAccountError, RelayManagementError)):
            return Response(
                {
                    "error": {
                        "code": exc.code
                        if isinstance(exc, RelayFailure)
                        else "relay_account_failed",
                        "message": str(exc),
                    }
                },
                status=409 if isinstance(exc, RelayAccountError) else 503,
            )
        return super().handle_exception(exc)

    def finalize_response(self, request: Request, response: Any, *args: Any, **kwargs: Any) -> Any:
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response


class AIModels(SafeRelayView):
    serializer_class = ModelListSerializer

    def get(self, request: Request) -> Response:
        assert not isinstance(request.user, AnonymousUser)
        return Response(model_choices(request.user.pk))


class AIPreferences(SafeRelayView):
    @extend_schema(request=PreferenceInputSerializer, responses=ModelListSerializer)
    def patch(self, request: Request) -> Response:
        serializer = PreferenceInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assert not isinstance(request.user, AnonymousUser)
        return Response(choose_model(request.user.pk, serializer.validated_data["route_id"]))


class AdminRelay(SafeRelayView):
    permission_classes = [IsAdminUser]
    serializer_class = RelayStatusSerializer

    def get(self, request: Request) -> Response:
        models: list[str] = []
        error = None
        try:
            models = discover_models()
        except RelayFailure as exc:
            error = str(exc)
        return Response(
            {
                "account": asdict(provider_account_summary("codex")),
                "discovered_models": models,
                "catalogue_error": error,
                "laptop_wide": True,
            }
        )


class AdminAccountAction(SafeRelayView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=AccountActionSerializer, responses=AccountActionResultSerializer)
    def post(self, request: Request) -> Response:
        serializer = AccountActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        if action == "connect":
            return Response(asdict(start_account_login("codex")))
        actions = {
            "status": poll_account_login,
            "cancel": cancel_account_login,
            "disconnect": disconnect_account,
            "restore": restore_account,
            "forget": forget_account,
        }
        return Response({"account": asdict(actions[action]("codex"))})


class AdminQualification(SafeRelayView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=QualificationInputSerializer, responses=QualificationSerializer)
    def post(self, request: Request) -> Response:
        serializer = QualificationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        qualification = qualify_model(serializer.validated_data["model"])
        return Response(
            {
                "id": str(qualification.id),
                "route_id": str(qualification.route_id),
                "model": qualification.route.configured_model,
                "state": qualification.state,
                "results": qualification.evaluation_results,
            }
        )
