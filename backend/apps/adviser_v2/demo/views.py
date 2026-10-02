"""Authenticated versioned demo endpoints; selection and pins are server-owned."""

import hashlib
import json
import time
from pathlib import Path

import pdfplumber
from django.conf import settings
from django.db import close_old_connections
from django.http import FileResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from pydantic import ValidationError as ContractError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import DemoPlanAnswer, DemoPlanIndex, DemoQuestion, DemoRelease, DemoSession
from .acquisition import INSURERS
from .charts import load_prices
from .citations import card_anchor
from .contracts import Citation, PlanCard, PremiumResult, Profile
from .highlighting import _normalized, clause_rectangles
from .matching import all_fits
from .needs import normalize
from .pricing import lookup
from .services import bundle_for, decrypted, question_payload, save_profile, submit, usable
from .tasks import demo_question


class ObjectOutput(serializers.Serializer):
    schema_version = serializers.IntegerField(default=1)
    data = serializers.JSONField(required=False)


class Health(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=ObjectOutput)
    def get(self, request):
        return Response({"schema_version": 1, "service": "coverguide-retrieval-demo", "ready": True})


class ProfileInput(serializers.Serializer):
    session_id = serializers.UUIDField(required=False)
    profile = serializers.JSONField()


class QuestionInput(serializers.Serializer):
    session_id = serializers.UUIDField()
    question = serializers.CharField(max_length=3000)
    plan_ids = serializers.ListField(child=serializers.CharField(max_length=160), min_length=2, max_length=5)


class CardCitationInput(serializers.Serializer):
    citation = serializers.JSONField()


class CardCitation(APIView):
    @extend_schema(request=CardCitationInput, responses=ObjectOutput)
    def post(self, request, index_id):
        index = get_object_or_404(DemoPlanIndex, pk=index_id, revoked_at__isnull=True)
        incoming = CardCitationInput(data=request.data)
        incoming.is_valid(raise_exception=True)
        bundle = bundle_for(index)
        try:
            anchor = card_anchor(index.card, bundle, Citation.model_validate(incoming.validated_data['citation']))
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return render_anchor(index.id, anchor, bundle)


def indexes():
    release = DemoRelease.objects.filter(active=True).first()
    return release, list(release.indexes.all()) if release else list(
        DemoPlanIndex.objects.order_by("plan_key", "-created_at").distinct("plan_key"))


class Catalogue(APIView):
    @extend_schema(responses=ObjectOutput)
    def get(self, request):
        release, rows = indexes()
        return Response({"schema_version": 1, "release_id": str(release.id) if release else None,
            "method": release.method if release else None,
            "plans": [row.card for row in sorted(rows, key=lambda r: (r.insurer.casefold(), r.name.casefold(), r.variant.casefold(), r.plan_key)) if row.card],
            "disclaimer": "Local demonstration. Not a recommendation. Document checks do not establish underwriting acceptance or claim payment. AI answers have not been reviewed by an insurance expert."})


class Coverage(APIView):
    @extend_schema(responses=ObjectOutput)
    def get(self, request):
        release, rows = indexes()
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
        register = root / "discovery/register.json"
        discovery = json.loads(register.read_text()) if register.exists() else []
        found = {r["insurer_id"]: r for r in discovery}
        recovered_file = root / 'retry-flagship-candidates.json'
        recovered = json.loads(recovered_file.read_text()) if recovered_file.exists() else []
        inventory_file = root / 'catalogue-inventory.json'
        inventory = json.loads(inventory_file.read_text()) if inventory_file.exists() else {'insurers': []}
        inventory = {r['insurer_id']: r for r in inventory['insurers']}
        return Response({"schema_version": 1, "selection_basis": "demo_sample",
            "release_id": str(release.id) if release else None, "method": release.method if release else None,
            "insurers": [{"id": key, "name": name, "source_url": url,
                "discovery_status": found.get(key, {}).get("status", "pending"),
                "candidate_document_count": len(found.get(key, {}).get("documents", [])),
                "browser_recovered_pdfs": len({r['sha256'] for r in recovered if r['insurer_id'] == key
                                               and r['status'] == 'acquired_unreviewed'}),
                "register_entries": inventory.get(key, {}).get('register_entries'),
                "catalogue_complete": False} for key, name, url in sorted(INSURERS, key=lambda r: r[1])],
            "plans": [{"id": r.plan_key, "name": r.name, "insurer": r.insurer, "uin": r.uin,
                       "edition": r.edition, "index_version": r.id, "models": r.models_used,
                       "revoked": bool(r.revoked_at), **r.coverage} for r in rows]})


class Fit(APIView):
    @extend_schema(request=ProfileInput, responses=ObjectOutput)
    def post(self, request):
        incoming = ProfileInput(data=request.data)
        incoming.is_valid(raise_exception=True)
        try:
            profile = Profile.model_validate(incoming.validated_data["profile"])
            previous = None
            if incoming.validated_data.get("session_id"):
                old = DemoSession.objects.get(pk=incoming.validated_data["session_id"], owner=request.user)
                previous = decrypted(old.profile_ciphertext, old.id)
            profile = normalize(profile, previous)
            session = save_profile(request.user, profile, incoming.validated_data.get("session_id"))
        except (ContractError, ValueError, DemoSession.DoesNotExist) as exc:
            raise ValidationError("Profile could not be accepted: " + str(exc)) from exc
        _, rows = indexes()
        cards = [PlanCard.model_validate(row.card) for row in rows if row.card and row.revoked_at is None]
        return Response({"schema_version": 1, "session_id": str(session.id), "revision": session.profile_revision,
                         "normalized_needs": [n.model_dump() for n in profile.normalized_needs],
                         "needs_model": profile.needs_model,
                         "results": [r.model_dump() for r in all_fits(cards, profile)]})


class Questions(APIView):
    @extend_schema(request=QuestionInput, responses=ObjectOutput)
    def post(self, request):
        incoming = QuestionInput(data=request.data)
        incoming.is_valid(raise_exception=True)
        try:
            question = submit(request.user, **incoming.validated_data)
        except (ValueError, DemoSession.DoesNotExist, DemoRelease.DoesNotExist) as exc:
            raise ValidationError("Question unavailable: " + str(exc)) from exc
        demo_question.apply_async(args=[str(question.id)], queue="demo_live")
        return Response(question_payload(question), status=202)


class QuestionDetail(APIView):
    @extend_schema(responses=ObjectOutput)
    def get(self, request, pk):
        question = get_object_or_404(DemoQuestion.objects.select_related("session__owner"), pk=pk, session__owner=request.user)
        return Response(question_payload(question))


class Cancel(APIView):
    @extend_schema(request=None, responses=ObjectOutput)
    def post(self, request, pk):
        question = get_object_or_404(DemoQuestion, pk=pk, session__owner=request.user)
        DemoQuestion.objects.filter(pk=question.pk).update(state="cancelled", cancelled_at=timezone.now())
        return Response({"schema_version": 1, "id": str(pk), "state": "cancelled"})


class Events(APIView):
    @extend_schema(responses={(200, "text/event-stream"): str})
    def get(self, request, pk):
        get_object_or_404(DemoQuestion, pk=pk, session__owner=request.user)
        owner_id = request.user.id

        def stream():
            previous = None
            for _ in range(600):
                question = DemoQuestion.objects.select_related("session__owner").filter(pk=pk, session__owner_id=owner_id).first()
                if question is None:
                    yield 'event: cancelled\ndata: {"state":"cancelled"}\n\n'
                    return
                payload = question_payload(question)
                close_old_connections()  # Streaming waits must not reserve a SQL pool slot.
                encoded = json.dumps(payload)
                if encoded != previous:
                    yield "data: " + encoded + "\n\n"
                    previous = encoded
                if payload["state"] in {"completed", "cancelled"}:
                    return
                time.sleep(1)
        response = StreamingHttpResponse(stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-store"
        response["X-Accel-Buffering"] = "no"
        return response


class Price(APIView):
    @extend_schema(responses=ObjectOutput)
    def get(self, request, index_id):
        index = get_object_or_404(DemoPlanIndex, pk=index_id, revoked_at__isnull=True)
        bundle = bundle_for(index)
        chart_path = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer/premiums" / (index.id + ".json")
        if chart_path.exists():
            chart = json.loads(chart_path.read_text())
            if chart["index_id"] != index.id:
                raise ValidationError("Chart identity differs from the pinned plan index.")
            prices, cells = load_prices(chart)
            if chart["status"] == "source_unavailable":
                return Response(PremiumResult(status="source_unavailable", amount_printed=None, missing_axes=[], citations=[]).model_dump())
            result = lookup(prices=prices, cells=cells, required_axes=set(chart["required_axes"]),
                            selected=dict(request.query_params.items()), published=True)
            result.axis_options = {axis: sorted({p.axes[axis] for p in prices}) for axis in chart["required_axes"]}
            return Response(result.model_dump())
        # Unparsed published charts are distinct from a known absence of a chart.
        status = "invalid_chart" if any(d.get("role") == "premium_chart" for d in bundle.get("documents", [])) else "source_unavailable"
        return Response(PremiumResult(status=status, amount_printed=None, missing_axes=[], citations=[]).model_dump())


class Document(APIView):
    @extend_schema(responses={(200, "application/pdf"): bytes})
    def get(self, request, index_id, sha):
        index = get_object_or_404(DemoPlanIndex, pk=index_id, revoked_at__isnull=True)
        bundle = bundle_for(index)
        docs = [d for d in bundle.get("documents", []) if d["sha256"] == sha]
        if len(docs) != 1:
            raise ValidationError("Document is outside the pinned plan edition.")
        path = Path(docs[0]["path"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise ValidationError("The preserved document failed its integrity check.")
        response = FileResponse(path.open("rb"), content_type="application/pdf")
        response["Cache-Control"] = "no-store"
        return response


class CitationDetail(APIView):
    @extend_schema(responses=ObjectOutput)
    def get(self, request, answer_id, position):
        row = get_object_or_404(DemoPlanAnswer.objects.select_related("question__session__owner", "index"),
                                pk=answer_id, question__session__owner=request.user, index__revoked_at__isnull=True)
        if not usable(row.question) or not row.result_ciphertext:
            raise ValidationError("This answer is no longer available.")
        result = decrypted(row.result_ciphertext, row.id)
        validation = result.get("validation") or {}
        if result.get("status") != "answered" or validation.get("checks") != [True]*6:
            raise ValidationError("No accepted citation is available.")
        anchors = validation.get("anchors", [])
        if not 0 <= position < len(anchors):
            raise ValidationError("Unknown citation.")
        anchor = anchors[position]
        bundle = bundle_for(row.index)
        return render_anchor(row.index_id, anchor, bundle)


def render_anchor(index_id, anchor, bundle):
    doc = next(d for d in bundle["documents"] if d["sha256"] == anchor["document_sha256"])
    raw_page = next(p for p in bundle["pages"] if p["evidence_span_id"] == anchor["page_id"])
    raw = raw_page["passage"]
    if raw[anchor["start"]:anchor["end"]] != anchor["quote"]:
        raise ValidationError("Citation offsets no longer match the original source.")
    path = Path(doc["path"])
    if hashlib.sha256(path.read_bytes()).hexdigest() != anchor["document_sha256"]:
        raise ValidationError("Document integrity check failed.")
    if anchor["method"] == "ocr":
        boxes = [word["bbox"] for word in raw_page.get("ocr_words", [])
                 if word["start"] < anchor["end"] and word["end"] > anchor["start"]]
        if not boxes:
            raise ValidationError("The OCR source has no preserved highlight geometry.")
    else:
        boxes = native_boxes(path, anchor, raw)
    return Response({**anchor, "boxes": boxes,
                     "pdf_url": f"/api/v2/demo/documents/{index_id}/{anchor['document_sha256']}/"})


def native_boxes(path, anchor, raw):
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[anchor["page"] - 1]
        chars = tuple({key: char[key] for key in ("text", "x0", "x1", "top", "bottom")} for char in page.chars)
        occurrence = _normalized(raw[:anchor["start"]]).count(_normalized(anchor["quote"]))
        try:
            boxes = clause_rectangles(chars, anchor["quote"], occurrence)
        except ValueError as exc:
            raise ValidationError("Exact source text is available, but its highlight could not be resolved.") from exc
    return boxes
