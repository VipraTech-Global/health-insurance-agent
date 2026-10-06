from __future__ import annotations

import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path

import httpx
import pytest
from django.core.management import call_command
from pydantic import ValidationError

from apps.adviser_v2.manifest import (
    CuratedManifest,
    CuratedManifestV2,
    acquire_manifest_entry,
    manifest_sha256,
)
from apps.adviser_v2.models import PolicyVersionDocument, ProcessingJob, SourceCapture
from apps.adviser_v2.readiness import load_captured_manifest, role_inventory_blockers
from apps.adviser_v2.services.releases import _release_report
from apps.adviser_v2.tests.test_manifest import manifest as v1_manifest

ROOT = Path(__file__).resolve().parents[4]
MANIFEST = ROOT / "data/manifests/star-three-plan-2026-09-30.json"


def pdf_bytes(text: str) -> bytes:
    """Small real PDF so integrity tests exercise the parser, not a mocked page count."""
    content = f"BT /F1 12 Tf 30 700 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"\nendstream",
    ]
    payload = b"%PDF-1.4\n"
    offsets = [0]
    for number, value in enumerate(objects, 1):
        offsets.append(len(payload))
        payload += f"{number} 0 obj\n".encode() + value + b"\nendobj\n"
    xref = len(payload)
    payload += b"xref\n0 6\n0000000000 65535 f \n"
    payload += b"".join(f"{offset:010} 00000 n \n".encode() for offset in offsets[1:])
    return payload + f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()


def star_manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def local_fixture(tmp_path: Path) -> tuple[dict, Path]:
    value = star_manifest()
    objects = tmp_path / "objects"
    for product in value["products"]:
        payload = pdf_bytes("Policy wording " + product["uin"])
        digest = hashlib.sha256(payload).hexdigest()
        path = objects / digest[:2] / digest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        for document in product["documents"]:
            document.update(expected_sha256=digest, page_count=1)
        for cover in product["optional_covers"]:
            cover["page_number"] = 1
    return value, objects


def test_v1_contract_stays_five_products_and_rejects_v2_fields():
    value = v1_manifest()
    assert len(CuratedManifest.model_validate(value).products) == 5
    value["products"] = value["products"][:3]
    with pytest.raises(ValidationError, match="five"):
        CuratedManifest.model_validate(value)
    value = v1_manifest()
    value["products"][0]["optional_covers"] = []
    with pytest.raises(ValidationError, match="Extra inputs"):
        CuratedManifest.model_validate(value)


def test_approved_star_manifest_keeps_assure_sheet_reference_and_options_unselected():
    manifest = CuratedManifestV2.model_validate(star_manifest())
    assert sum(d.evidence_use == "executable" for p in manifest.products for d in p.documents) == 16
    assure = manifest.products[2]
    sheet = next(d for d in assure.documents if d.role == "excluded_expenses")
    assert (sheet.applicability, sheet.evidence_use, sheet.required) == (
        "applicable",
        "reference",
        False,
    )
    assert all(not cover.selected for p in manifest.products for cover in p.optional_covers)


@pytest.mark.parametrize(
    "mutation",
    ["selected", "wrong_page", "missing_core", "wrong_host", "wrong_count", "reference_required"],
)
def test_v2_rejects_scope_and_evidence_boundary_changes(mutation):
    value = star_manifest()
    product = value["products"][0]
    if mutation == "selected":
        product["optional_covers"][0]["selected"] = True
    elif mutation == "wrong_page":
        product["optional_covers"][0]["page_number"] = 999
    elif mutation == "missing_core":
        product["documents"] = [d for d in product["documents"] if d["role"] != "base_wording"]
    elif mutation == "wrong_host":
        value["official_hosts"].append("attacker.cloudfront.net")
    elif mutation == "wrong_count":
        value["products"].pop()
    else:
        sheet = next(
            d for d in value["products"][2]["documents"] if d["role"] == "excluded_expenses"
        )
        sheet["required"] = True
    with pytest.raises(ValidationError):
        CuratedManifestV2.model_validate(value)


@pytest.mark.parametrize("failure", [None, "hash", "pages"])
def test_local_objects_are_verified_without_network_or_corrupt_fallback(tmp_path, failure):
    value, root = local_fixture(tmp_path)
    entry = CuratedManifestV2.model_validate(value).products[0].documents[0]
    if failure == "hash":
        (root / entry.expected_sha256[:2] / entry.expected_sha256).write_bytes(pdf_bytes("changed"))
    elif failure == "pages":
        entry = entry.model_copy(update={"page_count": 2})
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: pytest.fail("Unexpected HTTP"))
    ) as client:
        if failure:
            with pytest.raises(ValueError, match="SHA-256|page count"):
                acquire_manifest_entry(
                    entry, set(value["official_hosts"]), client, local_object_root=root
                )
        else:
            _, metadata = acquire_manifest_entry(
                entry, set(value["official_hosts"]), client, local_object_root=root
            )
            assert metadata["acquisition_method"] == "verified_local_object"
            assert metadata["http_status"] is None  # No HTTP request occurred.
            assert metadata["page_count"] == 1


def test_missing_local_object_fetches_only_its_exact_url(tmp_path, monkeypatch):
    value, root = local_fixture(tmp_path)
    entry = CuratedManifestV2.model_validate(value).products[0].documents[0]
    path = root / entry.expected_sha256[:2] / entry.expected_sha256
    payload = path.read_bytes()
    path.unlink()
    monkeypatch.setattr(
        "apps.adviser_v2.manifest.socket.getaddrinfo",
        lambda *_args, **_kw: [(None, None, None, None, ("1.1.1.1", 443))],
    )
    requested = []

    def serve(request):
        requested.append(str(request.url))
        return httpx.Response(200, content=payload, headers={"content-type": "application/pdf"})

    with httpx.Client(transport=httpx.MockTransport(serve)) as client:
        _, metadata = acquire_manifest_entry(
            entry, set(value["official_hosts"]), client, local_object_root=root
        )
    assert requested == [str(entry.url)]
    assert metadata["acquisition_method"] == "official_url_missing_local_object"


@pytest.mark.django_db
def test_ingestion_preserves_metadata_but_only_executable_bundle_members(
    tmp_path, settings, monkeypatch
):
    value, root = local_fixture(tmp_path)
    manifest_path = tmp_path / "input.json"
    manifest_path.write_text(json.dumps(value))
    settings.COVERGUIDE_MANIFEST_ROOT = tmp_path / "manifests"
    settings.COVERGUIDE_LOCAL_OBJECT_ROOT = str(root)
    monkeypatch.setattr(
        "apps.adviser_v2.manifest.download_manifest_entry",
        lambda *_args: pytest.fail("Unexpected HTTP"),
    )
    call_command("ingest_curated_manifest", manifest_path)
    captured_path = settings.COVERGUIDE_MANIFEST_ROOT / f"{value['manifest_id']}-captured.json"
    captured = load_captured_manifest(captured_path)
    assert SourceCapture.objects.count() == 23
    assert PolicyVersionDocument.objects.count() == 16
    assert not ProcessingJob.objects.exists()
    for product in captured["products"]:
        assert role_inventory_blockers(product) == []
        members = set(
            PolicyVersionDocument.objects.filter(
                policy_version_id=product["policy_version_id"]
            ).values_list("document_version_id", flat=True)
        )
        for document in product["documents"]:
            assert (document["document_version_id"] in {str(pk) for pk in members}) == (
                document["evidence_use"] == "executable"
            )
    # A checksum alone cannot turn an unresolved document into executable evidence.
    damaged = deepcopy(captured)
    document = damaged["products"][2]["documents"][0]
    document.update(expected_applicability="needs_human_decision", evidence_use="executable")
    damaged.pop("manifest_sha256")
    damaged["manifest_sha256"] = manifest_sha256(damaged)
    captured_path.write_text(json.dumps(damaged))
    with pytest.raises(ValueError, match="version-2 manifest is invalid"):
        load_captured_manifest(captured_path)


def test_actual_three_product_manifest_requires_explicit_demo_request():
    with pytest.raises(ValueError, match="explicit three-product demo"):
        _release_report({"products": [{}, {}, {}]}, {}, 5)


def test_actual_three_product_report_retains_catalogue_blockers():
    report = {"ready": False, "blockers": ["release_uins_not_distinct"], "products": []}
    assert _release_report({"schema_version": 2}, report, 3) == report


def test_database_and_storage_configuration_support_explicit_isolation(monkeypatch, tmp_path):
    monkeypatch.setenv("POSTGRES_DB", "coverguide_star_slice")
    monkeypatch.setenv("POSTGRES_TEST_DB", "test_coverguide_star_slice")
    monkeypatch.setenv("COVERGUIDE_V2_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6401/0")
    configured = runpy.run_path(str(ROOT / "backend/config/settings.py"))
    assert configured["DATABASES"]["default"]["NAME"] == "coverguide_star_slice"
    assert configured["DATABASES"]["default"]["TEST"]["NAME"] == "test_coverguide_star_slice"
    assert configured["CELERY_BROKER_URL"] == "redis://127.0.0.1:6401/0"
    assert configured["COVERGUIDE_V2_STORAGE_ROOT"] == tmp_path / "storage"
