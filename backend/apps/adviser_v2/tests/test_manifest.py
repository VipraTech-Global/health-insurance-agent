from __future__ import annotations

import hashlib
from copy import deepcopy

import pytest
from django.utils import timezone
from pydantic import ValidationError

from apps.adviser_v2.management.commands.ingest_curated_manifest import Command
from apps.adviser_v2.manifest import ALL_DOCUMENT_ROLES, CuratedManifest, is_complete_pdf
from apps.adviser_v2.models import AuditEvent, DiscoveryRun, Insurer
from apps.adviser_v2.processing.identity import (
    reconcile_capture_identity,
    verify_observed_identity,
)
from apps.adviser_v2.readiness import _document_identity_blockers, role_inventory_blockers


def product(index: int) -> dict[str, object]:
    roles = []
    documents = []
    applicable = {
        "base_wording",
        "customer_information_sheet",
        "prospectus",
        "product_page",
    }
    for role in sorted(ALL_DOCUMENT_ROLES):
        state = "applicable" if role in applicable else "not_applicable"
        roles.append({"role": role, "applicability": state, "reason": "Reviewed decision."})
        if state == "applicable":
            documents.append(
                {
                    "document_key": f"{role}-{index}",
                    "role": role,
                    "url": f"https://insurer{index}.example/{role}.pdf",
                    "authority": "insurer_issued",
                    "expected_media_type": (
                        "text/html" if role == "product_page" else "application/pdf"
                    ),
                    "required": True,
                    "applicability": state,
                    "applicability_reason": "Required for the complete reviewed bundle.",
                }
            )
    return {
        "product_key": f"product-{index}",
        "insurer": f"Insurer {index}",
        "name": f"Product {index}",
        "uin": f"UIN-{index}",
        "variant": "Base",
        "role_decisions": roles,
        "documents": documents,
    }


def manifest() -> dict[str, object]:
    return {
        "schema_version": 1,
        "manifest_id": "five-products",
        "freeze_date": "2026-09-13",
        "official_hosts": [f"insurer{index}.example" for index in range(5)],
        "products": [product(index) for index in range(5)],
    }


def captured_product() -> dict[str, object]:
    value = deepcopy(product(0))
    for document in value["documents"]:  # type: ignore[index,union-attr]
        document["expected_applicability"] = document.pop("applicability")
    return value


def test_manifest_requires_exactly_five_complete_distinct_bundles() -> None:
    parsed = CuratedManifest.model_validate(manifest())
    assert len(parsed.products) == 5
    assert all(len(item.role_decisions) == len(ALL_DOCUMENT_ROLES) for item in parsed.products)


def test_manifest_rejects_silent_role_omission() -> None:
    value = deepcopy(manifest())
    value["products"][0]["role_decisions"].pop()  # type: ignore[index,union-attr]
    with pytest.raises(ValidationError, match="Every document role"):
        CuratedManifest.model_validate(value)


def test_pdf_completeness_allows_small_bounded_official_response_trailer() -> None:
    assert is_complete_pdf(b"%PDF-1.7\nbody\n%%EOF" + b"x" * 10_000)
    assert not is_complete_pdf(b"%PDF-1.7\nbody\n%%EOF" + b"x" * 70_000)
    assert not is_complete_pdf(b"not a pdf\n%%EOF")


def test_release_gate_rechecks_every_captured_role_decision() -> None:
    value = captured_product()
    assert role_inventory_blockers(value) == []

    value["role_decisions"].pop()  # type: ignore[index,union-attr]
    assert any(
        item.startswith("document_role_decision_missing:")
        for item in role_inventory_blockers(value)
    )


def test_release_gate_rejects_optional_label_on_an_applicable_document() -> None:
    value = captured_product()
    value["documents"][0]["required"] = False  # type: ignore[index,union-attr]

    assert any(
        item.startswith("applicable_document_not_required:")
        for item in role_inventory_blockers(value)
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("payload", "expected_kind", "expected_status", "has_span_id"),
    [
        (
            b"<html><body>Current product UIN-0 is available.</body></html>",
            "uin",
            "observed",
            True,
        ),
        (
            b"<html><body>Current product is available.</body></html>",
            "expected_uin",
            "unresolved",
            False,
        ),
    ],
)
def test_manifest_uin_is_observed_only_when_present_in_source(
    payload: bytes,
    expected_kind: str,
    expected_status: str,
    has_span_id: bool,
    settings,
    tmp_path,
) -> None:
    settings.COVERGUIDE_V2_STORAGE_ROOT = tmp_path
    parsed_product = CuratedManifest.model_validate(manifest()).products[0]
    product_page = next(item for item in parsed_product.documents if item.role == "product_page")
    insurer = Insurer.objects.create(name=parsed_product.insurer)
    run = DiscoveryRun.objects.create(
        insurer=insurer,
        instructions="Fixed test manifest only.",
        session_id=f"manifest-identity-{expected_status}",
        model_name="none",
        completed_at=timezone.now(),
        status="completed",
    )
    digest = hashlib.sha256(payload).hexdigest()

    capture, span = Command()._record_capture(
        run,
        insurer,
        parsed_product,
        product_page,
        payload,
        {"sha256": digest, "http_status": 200},
    )

    capture.document_version.refresh_from_db()
    identifier = capture.document_version.identifiers[0]
    assert identifier["kind"] == expected_kind
    assert identifier["status"] == expected_status
    assert ("span_id" in identifier) is has_span_id
    assert span.verification == "unverified"

    verified_count = verify_observed_identity(capture, uin=parsed_product.uin)
    span.refresh_from_db()
    assert verified_count == (1 if expected_status == "observed" else 0)
    assert span.verification == ("text_verified" if expected_status == "observed" else "unverified")
    assert verify_observed_identity(capture, uin=parsed_product.uin) == 0
    assert _document_identity_blockers(
        capture,
        uin=parsed_product.uin,
        require_observed=True,
    ) == ([] if expected_status == "observed" else ["authoritative_uin_not_observed"])

    if expected_status == "unresolved":
        capture.document_version.identifiers = [
            {
                "issuer": parsed_product.insurer,
                "kind": "uin",
                "value": parsed_product.uin,
                "span_id": str(span.id),
                "status": "observed",
            }
        ]
        capture.document_version.save(update_fields=["identifiers", "updated_at"])
        reconcile_capture_identity(
            capture,
            payload,
            uin=parsed_product.uin,
            issuer=parsed_product.insurer,
            notes=["Fixed test manifest only."],
            record_audit=True,
        )
        capture.document_version.refresh_from_db()
        corrected = capture.document_version.identifiers[0]
        assert corrected["kind"] == "expected_uin"
        assert corrected["status"] == "unresolved"
        assert "span_id" not in corrected
        assert (
            AuditEvent.objects.filter(
                operation="document_identity_reconciled",
                object_id=capture.document_version_id,
                outcome="succeeded",
            ).count()
            == 1
        )
