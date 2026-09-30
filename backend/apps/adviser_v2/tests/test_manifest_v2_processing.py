from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from django.core.management import call_command

from apps.adviser_v2.processing.criterion_evidence import (
    CRITERIA,
    no_copay_body,
    quantity_support_problems,
)
from apps.adviser_v2.processing.manifest_v2 import (
    ANCHOR_PREFIX,
    executable_entry,
    manifest_product,
    raw_pdf_pages,
    validate_raw_quote,
)
from apps.adviser_v2.tests.test_star_manifest import local_fixture, pdf_bytes, star_manifest


def test_raw_reader_preserves_native_text_and_physical_page_boundaries():
    pages = raw_pdf_pages(pdf_bytes("Policy Wordings"), expected_pages=1)
    assert len(pages) == 1
    assert pages[0]["text"] == "Policy Wordings\n"
    assert pages[0]["document_char_start"] == 0
    assert pages[0]["document_char_end"] == len("Policy Wordings\n")
    with pytest.raises(ValueError, match="page count"):
        raw_pdf_pages(pdf_bytes("Policy Wordings"), expected_pages=2)


def test_unreadable_page_is_not_silently_omitted():
    with pytest.raises(ValueError, match="no reliable native text"):
        raw_pdf_pages(pdf_bytes(""), expected_pages=1)


@pytest.mark.parametrize("damage", [None, "quote", "page", "offset", "hash", "document_offset"])
def test_citation_checks_exact_text_physical_page_and_offsets(damage):
    text = "The co-payment is 10% for entry age 61 years and above.\n"
    page = {"text": text, "page_number": 20, "document_char_start": 17000}
    anchor = {
        "page": 20, "start": 0, "end": len(text),
        "page_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "document_start": 17000, "document_end": 17000 + len(text),
    }
    span = SimpleNamespace(
        quote=text, page=SimpleNamespace(page_number=20),
        locator={"physical_page": 20, "blob_sha256": "a" * 64},
    )
    damaged = deepcopy(anchor)
    if damage == "quote":
        span.quote = text.replace("10%", "0%")
    elif damage == "page":
        span.locator["physical_page"] = 19
    elif damage == "offset":
        damaged["end"] -= 1
    elif damage == "hash":
        damaged["page_text_sha256"] = "b" * 64
    elif damage == "document_offset":
        damaged["document_start"] = 16000
    span.context = {"notes": [ANCHOR_PREFIX + json.dumps(damaged)]}
    if damage:
        with pytest.raises(ValueError, match="Citation quotation"):
            validate_raw_quote(span, page, blob_sha256="a" * 64)
    else:
        validate_raw_quote(span, page, blob_sha256="a" * 64)


def test_raw_processing_is_v2_only_and_rejects_reference_evidence():
    capture = SimpleNamespace(discovery_run=SimpleNamespace(session_id="fixed-manifest:v1"))
    assert manifest_product(capture) is None
    product = star_manifest()["products"][2]
    reference = next(item for item in product["documents"] if item["evidence_use"] == "reference")
    capture.discovery_run = SimpleNamespace(session_id="fixed-manifest-v2:test", instructions=json.dumps({"manifest_schema_version": 2, "product": product}))
    capture.original_file = SimpleNamespace(sha256=reference["expected_sha256"])
    capture.source_url = SimpleNamespace(url=reference["url"])
    with pytest.raises(ValueError, match="Reference and excluded"):
        executable_entry(capture)


@pytest.mark.parametrize("value,unit,supported", [
    ("0.1", "ratio", True), ("0.2", "ratio", False),
    ("61", "year", True), ("61", "month", False),
    ("24", "month", True), ("500000", "money", True),
    ("5000000", "money", False), ("0", "ratio", False),
])
def test_numbers_and_units_must_match_quoted_support(value, unit, supported):
    quote = "Co-payment is 10% at entry age 61 years. Waiting period: 2 years. Sum insured Rs. 5 lakh."
    result = quantity_support_problems({"state": "finite", "value": value, "unit": unit}, [quote])
    assert (not result) is supported


def test_no_copay_derivation_preserves_conditions_and_does_not_infer_zero_elsewhere():
    body = {
        "schema_version": 1,
        "applies_when": {"node": "compare", "operator": "gte", "left": {"node": "input", "key": "entry_age"}, "right": {"node": "literal", "value": {"state": "finite", "value": "61", "unit": "year"}}},
        "inputs": [{"key": "entry_age", "unit": "year", "value_kind": "quantity", "required": True, "provenance_required": True}],
        "effects": [{"kind": "deduction", "target_key": "copay", "scope": {"insured_person": "each"}, "amount": {"node": "literal", "value": {"state": "finite", "value": "0.1", "unit": "ratio"}}}],
        "mandatory_rule_keys": [], "source_span_ids": ["original-citation"], "unresolved": [],
    }
    original = deepcopy(body)
    derived = no_copay_body("copay.deduction.copay_entry_age", body)
    assert derived is not None
    assert derived["effects"][0]["value"]["value"] == {"kind": "boolean", "value": False}
    for key in ("applies_when", "inputs", "source_span_ids"):
        assert derived[key] == body[key]
    assert derived["mandatory_rule_keys"] == ["copay.deduction.copay_entry_age"]
    assert body == original
    assert len(CRITERIA) == 13
    assert {item.key for item in CRITERIA}.isdisjoint({"no_copay", "budget"})
    body["unresolved"] = ["Uncertain base rate"]
    assert no_copay_body("copay.deduction.copay_entry_age", body) is None


@pytest.mark.django_db
def test_complete_raw_bundle_keeps_all_pages_and_excludes_reference_sources(tmp_path, settings, monkeypatch):
    from apps.adviser_v2.models import PolicyVersion
    from apps.adviser_v2.processing.manifest_v2 import (
        preserve_native_document,
        raw_bundle_passages,
        read_raw_document,
        reconcile_raw_document,
    )
    from apps.adviser_v2.processing.stages import RECONCILIATION_VERSION, STAGE_RUNNERS

    value, objects = local_fixture(tmp_path)
    for product in value["products"]:
        payload = pdf_bytes("Policy wording Customer information sheet Prospectus " + product["uin"])
        digest = hashlib.sha256(payload).hexdigest()
        path = objects / digest[:2] / digest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        for document in product["documents"]:
            document["expected_sha256"] = digest
    settings.COVERGUIDE_MANIFEST_ROOT = tmp_path / "manifests"
    settings.COVERGUIDE_LOCAL_OBJECT_ROOT = str(objects)
    manifest = tmp_path / "input.json"
    manifest.write_text(json.dumps(value))
    call_command("ingest_curated_manifest", manifest)
    monkeypatch.setitem(STAGE_RUNNERS, "read", read_raw_document)
    monkeypatch.setitem(STAGE_RUNNERS, "ocr", preserve_native_document)
    monkeypatch.setitem(STAGE_RUNNERS, "reconcile", lambda job: reconcile_raw_document(job, reconciliation_version=RECONCILIATION_VERSION))
    version = PolicyVersion.objects.get(uin=value["products"][2]["uin"])
    call_command("process_policy_bundle", str(version.id), documents_only=True)
    core = raw_bundle_passages(version)
    supplemented = raw_bundle_passages(version, include_prospectus=True)
    assert {item["document_role"] for item in core} == {"base_wording", "customer_information_sheet", "modern_treatment_schedule"}
    assert len(core) == 3 and len(supplemented) == 4
    assert all(item["page_char_start"] == 0 and item["page_char_end"] == len(item["passage"]) for item in supplemented)
    assert all("excluded-expenses" not in item["document_key"] for item in supplemented)
