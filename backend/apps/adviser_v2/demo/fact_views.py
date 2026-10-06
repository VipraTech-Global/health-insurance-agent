"""Citations resolve the exact card version requested, never its replacement."""

import hashlib
import json
from pathlib import Path

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from ..models import DemoFactCard
from .citations import card_anchor, price_anchor
from .contracts import Citation
from .premium_sources import priced_bundle
from .services import bundle_for
from .views import CardCitationInput, ObjectOutput, render_anchor


class FactCitation(APIView):
    @extend_schema(request=CardCitationInput, responses=ObjectOutput)
    def post(self, request, card_id):
        row = get_object_or_404(
            DemoFactCard.objects.select_related("index"), pk=card_id, index__revoked_at__isnull=True
        )
        incoming = CardCitationInput(data=request.data)
        incoming.is_valid(raise_exception=True)
        bundle = bundle_for(row.index)
        try:
            anchor = card_anchor(
                row.card, bundle, Citation.model_validate(incoming.validated_data["citation"])
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return render_anchor(row.index_id, anchor, bundle)


class FactPriceCitation(APIView):
    @extend_schema(request=CardCitationInput, responses=ObjectOutput)
    def post(self, request, card_id):
        row = get_object_or_404(
            DemoFactCard.objects.select_related("index"), pk=card_id, index__revoked_at__isnull=True
        )
        incoming = CardCitationInput(data=request.data)
        incoming.is_valid(raise_exception=True)
        path = Path(row.card.get("pricing_artifact", ""))
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != row.card.get(
            "pricing_sha256"
        ):
            raise ValidationError("The pinned price artifact is unavailable or changed.")
        chart = json.loads(path.read_text())
        if chart["index_id"] != row.index_id:
            raise ValidationError("The chart belongs to a different index version.")
        bundle = priced_bundle(row.index)
        try:
            anchor = price_anchor(
                chart,
                bundle,
                row.index.plan_key,
                Citation.model_validate(incoming.validated_data["citation"]),
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return render_anchor(row.index_id, anchor, bundle)
