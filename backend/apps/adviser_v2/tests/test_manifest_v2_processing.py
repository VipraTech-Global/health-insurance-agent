from __future__ import annotations

import hashlib
import json
import time
import uuid
from copy import deepcopy
from types import SimpleNamespace

import pytest
from django.core.management import call_command

from apps.adviser_v2.processing.criterion_evidence import (
    CRITERIA,
    PROCESSING_VERSION,
    criterion_inventory_problems,
    no_copay_body,
    quantity_support_problems,
    request_bytes_with_headroom,
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


@pytest.mark.parametrize(
    "damage", [None, "quote", "page", "offset", "hash", "document_offset", "page_file"]
)
def test_citation_checks_exact_text_physical_page_and_offsets(damage):
    text = "The co-payment is 10% for entry age 61 years and above.\n"
    page = {"text": text, "page_number": 20, "document_char_start": 17000}
    anchor = {
        "page": 20,
        "start": 0,
        "end": len(text),
        "page_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "document_start": 17000,
        "document_end": 17000 + len(text),
    }
    span = SimpleNamespace(
        quote=text,
        page=SimpleNamespace(page_number=20, original_file=SimpleNamespace(sha256="a" * 64)),
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
    elif damage == "page_file":
        span.page.original_file.sha256 = "b" * 64
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
    capture.discovery_run = SimpleNamespace(
        session_id="fixed-manifest-v2:test",
        instructions=json.dumps({"manifest_schema_version": 2, "product": product}),
    )
    capture.original_file = SimpleNamespace(sha256=reference["expected_sha256"])
    capture.source_url = SimpleNamespace(url=reference["url"])
    with pytest.raises(ValueError, match="Reference and excluded"):
        executable_entry(capture)


@pytest.mark.parametrize(
    "value,unit,supported",
    [
        ("0.1", "ratio", True),
        ("0.2", "ratio", False),
        ("61", "year", True),
        ("61", "month", False),
        ("24", "month", True),
        ("500000", "money", True),
        ("5000000", "money", False),
        ("0", "ratio", False),
    ],
)
def test_numbers_and_units_must_match_quoted_support(value, unit, supported):
    quote = (
        "Co-payment is 10% at entry age 61 years. Waiting period: 2 years. Sum insured Rs. 5 lakh."
    )
    result = quantity_support_problems({"state": "finite", "value": value, "unit": unit}, [quote])
    assert (not result) is supported


def test_no_copay_derivation_preserves_conditions_and_does_not_infer_zero_elsewhere():
    from apps.adviser_v2.contracts import validate_contract
    from apps.adviser_v2.rule_validation import rule_semantic_problems

    body = {
        "schema_version": 1,
        "applies_when": {
            "node": "compare",
            "operator": "gte",
            "left": {"node": "input", "key": "entry_age"},
            "right": {
                "node": "literal",
                "value": {"state": "finite", "value": "61", "unit": "year"},
            },
        },
        "inputs": [
            {
                "key": "entry_age",
                "unit": "year",
                "value_kind": "quantity",
                "required": True,
                "provenance_required": True,
            },
            {
                "key": "admissible_claim_amount",
                "unit": "money",
                "value_kind": "quantity",
                "required": True,
                "provenance_required": True,
            },
        ],
        "effects": [
            {
                "kind": "deduction",
                "target_key": "copay",
                "scope": {
                    "subject": "policy",
                    "subject_ids": [],
                    "period": "policy_term",
                    "benefit_keys": [],
                    "reset": "never",
                },
                "amount": {
                    "node": "literal",
                    "value": {"state": "finite", "value": "0.1", "unit": "ratio"},
                },
                "order_after_rule_keys": [],
                "base_input": "admissible_claim_amount",
            }
        ],
        "mandatory_rule_keys": [],
        "source_span_ids": [str(uuid.uuid4())],
        "unresolved": [],
        "rounding": {"mode": "none", "scale": 0, "authority_span_ids": []},
    }
    validate_contract("RuleV1", body)
    assert rule_semantic_problems(body) == []
    original = deepcopy(body)
    derived = no_copay_body("copay.deduction.copay_entry_age", body)
    assert derived is not None
    validate_contract("RuleV1", derived)
    assert rule_semantic_problems(derived) == []
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
def test_complete_raw_bundle_keeps_all_pages_and_excludes_reference_sources(
    tmp_path, settings, monkeypatch
):
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
        payload = pdf_bytes(
            "Policy wording Customer information sheet Prospectus " + product["uin"]
        )
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
    monkeypatch.setitem(
        STAGE_RUNNERS,
        "reconcile",
        lambda job: reconcile_raw_document(job, reconciliation_version=RECONCILIATION_VERSION),
    )
    version = PolicyVersion.objects.get(uin=value["products"][2]["uin"])
    call_command("process_policy_bundle", str(version.id), documents_only=True)
    core = raw_bundle_passages(version)
    supplemented = raw_bundle_passages(version, include_prospectus=True)
    assert {item["document_role"] for item in core} == {
        "base_wording",
        "customer_information_sheet",
        "modern_treatment_schedule",
    }
    assert len(core) == 3 and len(supplemented) == 4
    assert all(
        item["page_char_start"] == 0 and item["page_char_end"] == len(item["passage"])
        for item in supplemented
    )
    assert all("excluded-expenses" not in item["document_key"] for item in supplemented)


def test_request_budget_rejects_whole_input_without_truncation():
    messages = [{"role": "user", "content": "START" + "x" * 810000 + "END"}]
    with pytest.raises(ValueError, match="No text was truncated"):
        request_bytes_with_headroom("gpt-6-sol", messages, {})
    assert messages[0]["content"].endswith("END")


def test_v2_retry_is_bounded_and_keeps_complete_core_plus_needed_prospectus(monkeypatch):
    from apps.adviser_v2.processing import stages
    from apps.adviser_v2.schemas import PolicyRuleExtractionV1

    criterion = CRITERIA[0]
    version = SimpleNamespace(id=uuid.uuid4(), uin="exact-uin")
    core = [
        {"evidence_span_id": str(uuid.uuid4()), "passage": "START" + "original text " * 600 + "END"}
    ]
    whole = [
        *core,
        {"evidence_span_id": str(uuid.uuid4()), "passage": "Complete applicable prospectus"},
    ]
    requests = []
    monkeypatch.setattr(
        stages, "_selected_variant_name", lambda _version: "Base policy without optional covers"
    )
    monkeypatch.setattr(stages, "_renew_rule_lease", lambda _job: None)

    def model(**kwargs):
        requests.append(kwargs["messages"])
        return PolicyRuleExtractionV1(
            schema_version=1,
            policy_version_id=str(version.id),
            rules=[],
            omitted_inventory_categories=[criterion.category],
            material_issues=[
                f"{criterion.category}: {criterion.key}: The supplied source does not establish an explicit new-purchase sum-insured choice."
            ],
        )

    monkeypatch.setattr(stages, "call_model", model)
    result = stages._run_extraction_batch(
        job=SimpleNamespace(),
        policy_version=version,
        encoded_passages=json.dumps(core),
        categories=(criterion.category,),
        evidence_batch_label="1/1",
        deadline=time.monotonic() + 60,
        criterion=criterion,
        max_attempts=2,
        prospectus_supplement=lambda: json.dumps(whole),
    )
    assert result.rules == [] and len(requests) == 2
    assert all(core[0]["passage"] in request[-1]["content"] for request in requests)
    assert "Complete applicable prospectus" not in requests[0][-1]["content"]
    assert "Complete applicable prospectus" in requests[1][-1]["content"]


def test_thirteen_criteria_count_excludes_derived_no_copay_and_budget():
    from apps.adviser_v2.processing.criterion_pipeline import validated_criteria

    rules = [
        SimpleNamespace(id=uuid.uuid4(), rule_key=f"{c.category}.definition.{c.key}_supported")
        for c in CRITERIA[:6]
    ]
    extraction = SimpleNamespace(rules=rules, material_issues=[])
    review = SimpleNamespace(reviews=[], missing_rules=[])
    verified = [
        *rules,
        SimpleNamespace(id=uuid.uuid4(), rule_key="copay.definition.no_copay_derived"),
    ]
    statuses = validated_criteria(extraction, review, verified, [])
    assert len(statuses) == 13
    assert sum(item["status"] == "unknown" for item in statuses) == 7
    assert all(item["unknown_reasons"] for item in statuses if item["status"] == "unknown")


@pytest.mark.parametrize("unknown_count", [6, 7])
def test_publication_blocks_at_seven_unresolved_source_criteria(unknown_count):
    rule_id = str(uuid.uuid4())
    artifact = {
        "manifest_processing_version": PROCESSING_VERSION,
        "criteria": [
            {
                "criterion": criterion.key,
                "status": "unknown" if i < unknown_count else "supported",
                "rule_ids": [] if i < unknown_count else [rule_id],
                "unknown_reasons": ["Independent review did not confirm the source rule."]
                if i < unknown_count
                else [],
            }
            for i, criterion in enumerate(CRITERIA)
        ],
        "criterion_count": 13,
        "unresolved_criterion_count": unknown_count,
        "verified_rule_ids": [rule_id],
        "budget": {"status": "unavailable"},
    }
    assert criterion_inventory_problems(artifact) == (
        ["manifest_v2_seven_unresolved_criteria_stop"] if unknown_count == 7 else []
    )
    artifact["criteria"][0]["unknown_reasons"] = []
    assert "manifest_v2_unknown_reason_missing" in criterion_inventory_problems(artifact)
