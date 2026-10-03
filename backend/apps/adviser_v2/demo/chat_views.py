from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import DemoConversation
from .chat_services import StaleTurn, commit_turn, payload, start


class ChatOutput(serializers.Serializer):
    schema_version = serializers.IntegerField(default=2)
    id = serializers.UUIDField()
    state = serializers.JSONField()
    cards = serializers.JSONField()
    release_id = serializers.UUIDField()


class TurnInput(serializers.Serializer):
    request_id = serializers.UUIDField()
    revision = serializers.IntegerField(min_value=0)
    text = serializers.CharField(max_length=3000)


class Conversations(APIView):
    @extend_schema(operation_id="demo_start_conversation", request=None, responses=ChatOutput)
    def post(self, request):
        return Response(start(request.user), status=201)


class ConversationDetail(APIView):
    @extend_schema(responses=ChatOutput)
    def get(self, request, pk):
        conversation = get_object_or_404(
            DemoConversation.objects.select_related("release"), pk=pk, session__owner=request.user
        )
        return Response(payload(conversation))

    @extend_schema(operation_id="demo_commit_chat_turn", request=TurnInput, responses=ChatOutput)
    def post(self, request, pk):
        get_object_or_404(DemoConversation, pk=pk, session__owner=request.user)
        incoming = TurnInput(data=request.data)
        incoming.is_valid(raise_exception=True)
        try:
            result = commit_turn(request.user, pk, **incoming.validated_data)
        except StaleTurn as exc:
            return Response({"detail": str(exc)}, status=409)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(result)
