"""Implement each fail-closed processing stage without hidden network discovery."""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from collections import Counter, defaultdict
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django.db import connection, transaction
from django.db.models import Value
from django.utils import timezone

from apps.adviser.ai import RelayFailure

from ..contracts import contract_schema_document, validate_contract
from ..embedding import embed_texts, policy_index_version, qualified_embedding_status
from ..model_gateway import call_model
from ..models import (
    DocumentPage,
    EvidenceSpan,
    ModelAttempt,
    OriginalFile,
    PolicyRule,
    PolicyRuleEvidence,
    PolicyRuleLink,
    PolicyRuleTableCell,
    PolicySearchChunk,
    PolicyVersion,
    PolicyVersionDocument,
    ProcessingJob,
    ProductVariant,
    SourceCapture,
)
from ..registries import RULE_TYPES
from ..rule_engine import table_selectors_overlap
from ..rule_validation import (
    rule_graph_problems,
    rule_link_references,
    rule_semantic_problems,
    semantic_contract_summary,
)
from ..schemas import (
    ExtractedPolicyRule,
    PolicyRuleExtractionV1,
    PolicyRuleReviewV1,
    ReviewedPolicyRule,
)
from ..storage import read_private
from .artifacts import parent_artifact, read_artifact, source_bytes
from .readers import (
    DependencyUnavailable,
    classify_bytes,
    docling_layout,
    issue,
    native_pdf_read,
    ocr_pdf_pages,
)

INVENTORY_CATEGORIES = frozenset(
    {
        "eligibility",
        "family_composition",
        "sum_insured_choices",
        "waiting_periods",
        "room_and_icu_limits",
        "copay",
        "deductible",
        "restoration",
        "cumulative_bonus",
        "pre_and_post_hospitalisation",
        "exclusions",
        "special_treatments",
        "portability",
        "geography",
        "maternity_and_newborn",
        "selectable_options",
        "premium_rates",
    }
)
CRITICAL_INVENTORY_CATEGORIES = frozenset(
    {
        "eligibility",
        "family_composition",
        "sum_insured_choices",
        "waiting_periods",
        "room_and_icu_limits",
        "copay",
        "deductible",
        "restoration",
        "exclusions",
        "selectable_options",
    }
)
MAX_MODEL_PASSAGE_CHARACTERS = 350_000
RULE_PROMPT_VERSION = "coverguide-rule-prompts/14"
RULE_REVIEW_PROMPT_VERSION = "coverguide-rule-review-prompts/14"
RULE_VALIDATOR_VERSION = "coverguide-rule-validator/5"
RECONCILIATION_VERSION = "coverguide-reconciliation/2"
RULE_CALL_TIMEOUT_SECONDS = 1_800.0
RULE_STAGE_TIMEOUT_SECONDS = 7_200.0
RULE_BATCH_MAX_ATTEMPTS = 3
RULE_RETRYABLE_RELAY_CODES = frozenset(
    {"provider_timeout", "provider_transport", "invalid_structured_output"}
)
INVENTORY_CATEGORY_BATCHES = (
    (
        "eligibility",
        "family_composition",
        "sum_insured_choices",
        "selectable_options",
        "premium_rates",
    ),
    (
        "waiting_periods",
        "pre_and_post_hospitalisation",
        "portability",
        "maternity_and_newborn",
    ),
    ("room_and_icu_limits", "copay", "deductible", "geography"),
    ("restoration", "cumulative_bonus", "exclusions", "special_treatments"),
)


def _rule_contract_prompt() -> str:
    return json.dumps(
        {
            "registered_rule_types": sorted(RULE_TYPES),
            "rule_v1_json_schema": contract_schema_document("RuleV1"),
            "table_selectors_v1_json_schema": contract_schema_document("TableSelectorsV1"),
            "expression_v1_json_schema": contract_schema_document("ExpressionV1"),
            "semantic_constraints": semantic_contract_summary(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _remaining_rule_seconds(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise RelayFailure("provider_timeout", "The offline rule-stage deadline expired.")
    return min(remaining, RULE_CALL_TIMEOUT_SECONDS)


def _renew_rule_lease(job: ProcessingJob) -> None:
    if job.lease_token is None:
        raise ValueError("Rule processing requires an active fenced worker lease.")
    lease_until = timezone.now() + timedelta(seconds=RULE_CALL_TIMEOUT_SECONDS + 300)
    updated = ProcessingJob.objects.filter(
        pk=job.id,
        state="running",
        lease_token=job.lease_token,
    ).update(lease_until=lease_until)
    if updated != 1:
        raise ValueError("Rule processing lost its active fenced worker lease.")
    job.lease_until = lease_until


def _stable_rule_key_instruction() -> str:
    return (
        "Use deterministic lower-snake-case rule_key values in the form "
        "inventory_category.rule_type.short_semantic_slug. The slug must describe the "
        "operative trigger and effect, not cite page numbers or evidence IDs."
    )


def _buying_scope_instruction() -> str:
    return (
        "Each passage includes its exact document role, authority, version and physical page. "
        "Extract rules for new-purchase comparison and option selection, not an exhaustive claims "
        "adjudication manual. Contractual policy wording and applicable endorsements define "
        "operative cover; CIS, prospectus, rate tables and proposal questions may define supported "
        "buying choices and disclosures. Do not silently resolve a substantive source conflict. "
        "Represent insurer underwriting discretion as an unknown eligibility outcome with the "
        "required inputs. Represent a customer-specific schedule selection as a required input, "
        "not a corpus omission, when the bundle establishes the allowed choice and its operation. "
        "Use material_issues only for a decision-critical buying rule that the complete official "
        "bundle cannot support or a conflict that cannot be represented safely. "
    )


def _authored_amount_instruction() -> str:
    return (
        "When a passage is a genuine rate chart, premium slab table, sum-insured schedule or "
        "fixing rule (not merely a customer-facing illustration example), author a coverage rule "
        'with target_key "sum_insured" for an available sum-insured figure or target_key '
        '"budget" for a stated premium/instalment figure. Use a literal amount for a single '
        "stated figure "
        "and a table_lookup amount with table_cells for a slab or rate table, citing the exact "
        "evidence span for every value. Never infer, interpolate or fabricate a figure the source "
        "does not state, and never author such a rule from a single illustrative example premium. "
    )


def _eligibility_and_schedule_table_instruction() -> str:
    return (
        "Two specific patterns are frequently mis-encoded; check every candidate against both. "
        "First, when a CIS, prospectus or rate annexure presents an entry-age medical-test "
        "schedule, a family-composition maximum (for example allowed adults/children per floater "
        "or individual policy), or a sum-insured basis (for example floater vs individual) as a "
        "table keyed by age band, relationship, or plan variant, encode it as a table_lookup with "
        "the complete axes and every applicable cell -- never simplify a tabular schedule into a "
        "single literal or categorical fact, even when the underlying rule is easy to paraphrase "
        "in words. Second, an entry-age, relationship or composition criterion is a necessary "
        "input to eligibility, not a determinative one, whenever the bundle separately states that "
        "proposal acceptance is subject to insurer underwriting or discretion: encode the "
        "eligibility effect's outcome as dependent on that underwriting/acceptance input rather "
        "than asserting eligible or ineligible from the criterion alone. Do not drop this "
        "dependency to keep a rule simple. "
    )


def _table_output_instruction() -> str:
    return (
        "Every extracted rule must include table_cells and table_footnote_span_ids. For a rule "
        "without a source table, both arrays must be empty and its RuleV1 body must not use a "
        "table_lookup. For a table-backed rule, declare the complete axes in body.table, return "
        "every applicable original cell, encode each selectors field as a JSON-encoded "
        "TableSelectorsV1 array and each cell value as a JSON-encoded ExpressionV1 object, and "
        "cite the exact cell evidence_span_id. Cite every applicable table footnote separately; "
        "never infer missing cells or collapse overlapping ranges. "
    )


type NormalizedTableCell = tuple[list[dict[str, object]], dict[str, object], str]


def _normalized_selectors(selectors: list[object]) -> list[dict[str, object]] | None:
    by_axis: dict[str, dict[str, object]] = {}
    for value in selectors:
        if not isinstance(value, dict) or not isinstance(value.get("axis"), str):
            return None
        selector = {str(key): item for key, item in value.items()}
        axis = selector["axis"]
        assert isinstance(axis, str)
        if axis in by_axis:
            return None
        by_axis[axis] = selector
    return [by_axis[axis] for axis in sorted(by_axis)]


def _table_lookup_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        if value.get("node") == "table_lookup" and isinstance(value.get("table_key"), str):
            keys.add(value["table_key"])
        for child in value.values():
            keys.update(_table_lookup_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_table_lookup_keys(child))
    return keys


def _semantic_table_cells(rule: ExtractedPolicyRule) -> str:
    values: list[dict[str, object]] = []
    for cell in rule.table_cells:
        selectors = _normalized_selectors(cell.selectors)
        values.append(
            {
                "selectors": selectors if selectors is not None else cell.selectors,
                "value": cell.value,
            }
        )
    values.sort(key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")))
    return json.dumps(values, sort_keys=True, separators=(",", ":"))


def _table_rule_problems(
    rule: ExtractedPolicyRule,
    body: dict[str, Any],
    *,
    allowed_span_ids: set[str] | None = None,
) -> tuple[list[str], list[NormalizedTableCell], set[str], set[str]]:
    problems: list[str] = []
    normalized_cells: list[NormalizedTableCell] = []
    header_span_ids: set[str] = set()
    footnote_span_ids = set(rule.table_footnote_span_ids)
    if len(footnote_span_ids) != len(rule.table_footnote_span_ids):
        problems.append("table_footnote_span_ids contains duplicates")
    table = body.get("table")
    lookup_keys = _table_lookup_keys(body)
    if table is None:
        if lookup_keys:
            problems.append("table_lookup is present without a body.table definition")
        if rule.table_cells:
            problems.append("table_cells must be empty when body.table is absent")
        if rule.table_footnote_span_ids:
            problems.append("table_footnote_span_ids must be empty when body.table is absent")
        return problems, normalized_cells, header_span_ids, footnote_span_ids
    if not isinstance(table, dict):
        problems.append("body.table must be an object or null")
        return problems, normalized_cells, header_span_ids, footnote_span_ids
    table_key = table.get("table_key")
    if not isinstance(table_key, str) or lookup_keys != {table_key}:
        problems.append("table_lookup keys must resolve exactly to body.table.table_key")
    axes = table.get("axes")
    if not isinstance(axes, list):
        problems.append("body.table.axes must be an array")
        return problems, normalized_cells, header_span_ids, footnote_span_ids
    axis_by_key: dict[str, dict[str, object]] = {}
    for axis in axes:
        if not isinstance(axis, dict) or not isinstance(axis.get("key"), str):
            problems.append("every table axis must have a string key")
            continue
        key = axis["key"]
        if key in axis_by_key:
            problems.append(f"table axis {key} is declared more than once")
            continue
        axis_by_key[key] = {str(name): value for name, value in axis.items()}
        header_span_id = axis.get("header_span_id")
        if isinstance(header_span_id, str):
            header_span_ids.add(header_span_id)
    if not rule.table_cells:
        problems.append("a table-backed rule must preserve at least one original table cell")
    known_selector_keys: set[str] = set()
    axis_currencies: dict[str, set[str | None]] = defaultdict(set)
    result_currencies: set[str | None] = set()
    result_unit = table.get("result_unit")
    for index, cell in enumerate(rule.table_cells):
        selectors = _normalized_selectors(cell.selectors)
        if selectors is None:
            problems.append(f"table cell {index} repeats or malforms an axis selector")
            continue
        selector_axes = {selector["axis"] for selector in selectors}
        if selector_axes != set(axis_by_key):
            problems.append(f"table cell {index} does not select every declared axis exactly once")
            continue
        for selector in selectors:
            axis_key = selector["axis"]
            assert isinstance(axis_key, str)
            axis = axis_by_key[axis_key]
            selector_value = selector.get("value")
            if not isinstance(selector_value, dict):
                problems.append(f"table cell {index} axis {axis_key} has no typed value")
                continue
            value_kind = axis.get("value_kind")
            axis_unit = axis.get("unit")
            if value_kind == "quantity":
                if selector_value.get("state") != "finite":
                    problems.append(
                        f"table cell {index} axis {axis_key} requires a finite quantity selector"
                    )
                elif selector_value.get("unit") != axis_unit:
                    problems.append(f"table cell {index} axis {axis_key} has the wrong unit")
                axis_currencies[axis_key].add(
                    selector_value.get("currency")
                    if isinstance(selector_value.get("currency"), str)
                    else None
                )
            elif value_kind == "code":
                if (
                    selector_value.get("kind") != "code"
                    or selector_value.get("namespace") != axis_unit
                ):
                    problems.append(
                        f"table cell {index} axis {axis_key} has the wrong code namespace"
                    )
                if selector.get("operator") != "eq":
                    problems.append(f"table cell {index} axis {axis_key} code selector must use eq")
        canonical_key = json.dumps(selectors, sort_keys=True, separators=(",", ":"))
        if canonical_key in known_selector_keys:
            problems.append(f"table cell {index} duplicates another selector set")
        known_selector_keys.add(canonical_key)
        literal = cell.value if cell.value.get("node") == "literal" else None
        typed_result = literal.get("value") if isinstance(literal, dict) else None
        if isinstance(typed_result, dict) and typed_result.get("state") == "finite":
            if typed_result.get("unit") != result_unit:
                problems.append(f"table cell {index} result has the wrong unit")
            result_currencies.add(
                typed_result.get("currency")
                if isinstance(typed_result.get("currency"), str)
                else None
            )
        normalized_cells.append((selectors, cell.value, cell.evidence_span_id))
    for axis_key, currencies in axis_currencies.items():
        if len(currencies) > 1:
            problems.append(f"table axis {axis_key} mixes currencies")
    if len(result_currencies) > 1:
        problems.append("table results mix currencies")
    for index, left in enumerate(normalized_cells):
        for right in normalized_cells[index + 1 :]:
            overlap = table_selectors_overlap(left[0], right[0])
            if overlap is None:
                problems.append("table cell ranges could not be compared deterministically")
            elif overlap:
                problems.append("table cell selector ranges overlap")
    evidence_ids = (
        header_span_ids | footnote_span_ids | {cell.evidence_span_id for cell in rule.table_cells}
    )
    if allowed_span_ids is not None and not evidence_ids.issubset(allowed_span_ids):
        problems.append("table evidence cites a span outside the reconciled policy bundle")
    return problems, normalized_cells, header_span_ids, footnote_span_ids


def _rule_table_targets(rule: ExtractedPolicyRule) -> list[str]:
    body = rule.body
    problems, _cells, _headers, _footnotes = _table_rule_problems(rule, body)
    return [f"{rule.rule_key}: {problem}." for problem in problems]


def _extraction_batch_targets(
    policy_version_id: str,
    categories: tuple[str, ...],
    result: PolicyRuleExtractionV1,
) -> list[str]:
    targets: list[str] = []
    category_set = set(categories)
    returned_categories = {item.inventory_category for item in result.rules}
    returned_categories.update(result.omitted_inventory_categories)
    if result.policy_version_id != policy_version_id:
        targets.append("Return the exact supplied policy_version_id.")
    unknown = returned_categories - category_set
    if unknown:
        targets.append("Remove categories outside this batch: " + ",".join(sorted(unknown)))
    accounted = returned_categories | {
        description.partition(":")[0]
        for description in result.material_issues
        if description.partition(":")[0] in category_set
    }
    unaccounted = category_set - accounted
    if unaccounted:
        targets.append(
            "Explicitly account for every batch category through a rule, "
            "omitted_inventory_categories, or a category-prefixed material issue. "
            "Missing disposition: " + ",".join(sorted(unaccounted))
        )
    keys = [item.rule_key for item in result.rules]
    if len(keys) != len(set(keys)):
        targets.append("Return unique deterministic rule_key values within the batch.")
    for rule in result.rules:
        targets.extend(_rule_table_targets(rule))
    return targets


def _review_batch_targets(
    policy_version_id: str,
    categories: tuple[str, ...],
    result: PolicyRuleReviewV1,
    candidates: tuple[ExtractedPolicyRule, ...] = (),
) -> list[str]:
    del candidates
    targets: list[str] = []
    if result.policy_version_id != policy_version_id:
        targets.append("Return the exact supplied policy_version_id.")
    if len(result.inventory_categories) != len(set(result.inventory_categories)):
        targets.append("Return each inventory category exactly once.")
    if set(result.inventory_categories) != set(categories):
        targets.append("Set inventory_categories to exactly the fixed batch.")
    return targets


def _combine_extraction_batches(
    policy_version_id: str,
    values: list[tuple[tuple[str, ...], PolicyRuleExtractionV1]],
) -> PolicyRuleExtractionV1:
    rules = []
    omitted: set[str] = set()
    material_issues: list[str] = []
    known_rule_keys: set[str] = set()
    for categories, value in values:
        if value.policy_version_id != policy_version_id:
            raise ValueError("Policy extraction returned a different policy-version identity.")
        category_set = set(categories)
        returned_categories = {item.inventory_category for item in value.rules}
        returned_categories.update(value.omitted_inventory_categories)
        if not returned_categories.issubset(category_set):
            raise ValueError("Policy extraction returned a category outside its fixed batch.")
        missing_accounting = category_set - returned_categories
        if missing_accounting and not value.material_issues:
            raise ValueError("Policy extraction failed to account for every batched category.")
        for rule in value.rules:
            if rule.rule_key in known_rule_keys:
                raise ValueError("Policy extraction returned a duplicate cross-batch rule key.")
            known_rule_keys.add(rule.rule_key)
            rules.append(rule)
        omitted.update(value.omitted_inventory_categories)
        omitted.update(missing_accounting)
        material_issues.extend(value.material_issues)
    return PolicyRuleExtractionV1(
        schema_version=1,
        policy_version_id=policy_version_id,
        rules=rules,
        omitted_inventory_categories=sorted(omitted),
        material_issues=material_issues,
    )


def _combine_review_batches(
    policy_version_id: str,
    values: list[tuple[tuple[str, ...], PolicyRuleReviewV1]],
) -> PolicyRuleReviewV1:
    inventory: set[str] = set()
    reviews = []
    missing_rules = []
    known_rule_keys: set[str] = set()
    for categories, value in values:
        if value.policy_version_id != policy_version_id:
            raise ValueError("Independent review returned a different policy-version identity.")
        category_set = set(categories)
        if set(value.inventory_categories) != category_set:
            raise ValueError("Independent review did not inventory its exact fixed batch.")
        if not {item.inventory_category for item in value.missing_rules}.issubset(category_set):
            raise ValueError("Independent review returned a rule outside its fixed batch.")
        for reviewed in value.reviews:
            if reviewed.rule_key in known_rule_keys:
                raise ValueError("Independent review returned a duplicate cross-batch rule key.")
            known_rule_keys.add(reviewed.rule_key)
            reviews.append(reviewed)
        for rule in value.missing_rules:
            if rule.rule_key in known_rule_keys:
                raise ValueError("Independent review returned a duplicate cross-batch rule key.")
            known_rule_keys.add(rule.rule_key)
            missing_rules.append(rule)
        inventory.update(value.inventory_categories)
    return PolicyRuleReviewV1(
        schema_version=1,
        policy_version_id=policy_version_id,
        inventory_categories=sorted(inventory),
        reviews=reviews,
        missing_rules=missing_rules,
    )


def _capture(job: ProcessingJob) -> SourceCapture:
    capture = job.source_capture
    if not job.source_capture_id or capture is None:
        raise ValueError("This processing stage requires a public source capture.")
    return capture


def _original(job: ProcessingJob) -> OriginalFile:
    if job.source_capture_id:
        original = _capture(job).original_file
    else:
        upload = job.customer_uploaded_document
        if upload is None:
            raise ValueError("This processing stage requires a customer upload.")
        original = upload.original_file
    if original is None:
        raise ValueError("The processing source has no preserved original file.")
    return original


def _declared_kind(job: ProcessingJob) -> str | None:
    if job.source_capture_id:
        capture = _capture(job)
        if capture.document_version_id and capture.document_version is not None:
            return capture.document_version.document_series.kind
    if job.customer_uploaded_document_id:
        upload = job.customer_uploaded_document
        if upload is not None:
            return upload.kind
    return None


def run_classify(job: ProcessingJob) -> dict[str, Any]:
    result = classify_bytes(source_bytes(job), _declared_kind(job))
    if job.customer_uploaded_document_id:
        result["relevant"] = True
    return result


def run_read(job: ProcessingJob) -> dict[str, Any]:
    classification = parent_artifact(job)
    payload = source_bytes(job)
    if classification["media_type"] == "text/html":
        from ..manifest import html_text

        text = html_text(payload)
        return {
            "schema_version": 1,
            "classification": classification,
            "native": {
                "schema_version": 1,
                "reader": "html-text/1",
                "pages": [
                    {
                        "page_number": 1,
                        "width": 0.0,
                        "height": 0.0,
                        "rotation": 0,
                        "text": text,
                        "lines": [],
                        "words": [],
                        "tables": [],
                        "figure_count": 0,
                        "needs_ocr": False,
                        "unreliable_reasons": [],
                        "native_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    }
                ],
            },
            "layout": {
                "schema_version": 1,
                "reader": "html-dom/1",
                "nodes": [{"order": 0, "label": "text", "text": text, "provenance": []}],
                "node_counts": {"text": 1},
            },
            "issues": [],
        }
    native = native_pdf_read(payload)
    layout = docling_layout(payload)
    _request_ocr_for_layout_disagreements(native, layout)
    original = _original(job)
    DocumentPage.objects.bulk_create(
        [
            DocumentPage(original_file=original, page_number=item["page_number"])
            for item in native["pages"]
        ],
        ignore_conflicts=True,
    )
    return {
        "schema_version": 1,
        "classification": classification,
        "native": native,
        "layout": layout,
        "issues": [],
    }


def run_ocr(job: ProcessingJob) -> dict[str, Any]:
    read = parent_artifact(job)
    pages = read["native"]["pages"]
    requested = [int(item["page_number"]) for item in pages if item["needs_ocr"]]
    ocr = ocr_pdf_pages(source_bytes(job), requested) if requested else {}
    result = dict(read)
    result["ocr"] = {
        "schema_version": 1,
        "reader": "tesseract-eng+hin",
        "requested_pages": requested,
        "pages": {str(key): value for key, value in ocr.items()},
    }
    return result


def _normalized_similarity(left: str, right: str) -> float:
    left_tokens = Counter(re.findall(r"[a-z0-9]+", left.casefold()))
    right_tokens = Counter(re.findall(r"[a-z0-9]+", right.casefold()))
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    common = sum((left_tokens & right_tokens).values())
    return min(common / left_tokens.total(), common / right_tokens.total())


def _request_ocr_for_layout_disagreements(
    native: dict[str, Any], layout: dict[str, Any]
) -> list[int]:
    """Treat independent-reader disagreement as an unreliable native text layer."""

    layout_pages = _docling_page_text(layout)
    requested: list[int] = []
    for page in native.get("pages", []):
        page_number = int(page["page_number"])
        native_text = str(page.get("text", ""))
        layout_text = layout_pages.get(page_number, "")
        if not native_text.strip() or not layout_text.strip():
            continue
        if _normalized_similarity(native_text, layout_text) >= 0.50:
            continue
        reasons = page.setdefault("unreliable_reasons", [])
        if "native_layout_disagreement" not in reasons:
            reasons.append("native_layout_disagreement")
        page["needs_ocr"] = True
        requested.append(page_number)
    return requested


def _docling_page_text(layout: dict[str, Any]) -> dict[int, str]:
    values: dict[int, list[str]] = defaultdict(list)
    if layout.get("reader") == "html-dom/1":
        values[1].extend(str(node.get("text", "")) for node in layout.get("nodes", []))
        return {1: "\n".join(values[1])}
    for node in layout.get("nodes", []):
        for provenance in node.get("provenance", []):
            if not isinstance(provenance, dict):
                continue
            raw_page = provenance.get("page_no", provenance.get("page"))
            if isinstance(raw_page, int):
                values[raw_page].append(str(node.get("text", "")))
    return {key: "\n".join(value) for key, value in values.items()}


def _docling_page_table_text(layout: dict[str, Any]) -> dict[int, str]:
    values: dict[int, list[str]] = defaultdict(list)
    for node in layout.get("nodes", []):
        if node.get("label") != "table":
            continue
        pages = {
            raw_page
            for provenance in node.get("provenance", [])
            if isinstance(provenance, dict)
            and isinstance(
                raw_page := provenance.get("page_no", provenance.get("page")),
                int,
            )
        }
        for page_number in pages:
            values[page_number].append(str(node.get("text", "")))
    return {key: "\n".join(value) for key, value in values.items()}


def _is_meaningful_native_table(table: Any) -> bool:
    if not isinstance(table, list) or len(table) < 2:
        return False
    column_count = max((len(row) for row in table if isinstance(row, list)), default=0)
    nonempty = sum(
        bool(str(cell).strip())
        for row in table
        if isinstance(row, list)
        for cell in row
        if cell is not None
    )
    return column_count >= 2 and nonempty >= 6


def _is_preservable_native_table(table: Any) -> bool:
    """Retain compact two-by-two grids without treating them as reader conflicts."""

    if not isinstance(table, list) or len(table) < 2:
        return False
    populated_rows = 0
    populated_columns: set[int] = set()
    nonempty = 0
    for row in table:
        if not isinstance(row, list):
            continue
        row_nonempty = 0
        for column_index, cell in enumerate(row):
            if cell is None or not str(cell).strip():
                continue
            nonempty += 1
            row_nonempty += 1
            populated_columns.add(column_index)
        populated_rows += int(row_nonempty >= 2)
    return populated_rows >= 2 and len(populated_columns) >= 2 and nonempty >= 4


def _native_table_text(page: dict[str, Any]) -> str:
    rows: list[str] = []
    for table in page.get("tables", []):
        if not _is_meaningful_native_table(table):
            continue
        for row in table:
            if not isinstance(row, list):
                continue
            values = [str(cell).strip() if cell is not None else "" for cell in row]
            if any(values):
                rows.append(" | ".join(values))
    return "\n".join(rows)


def _native_table_evidence(
    page: dict[str, Any],
) -> list[tuple[int, str, dict[str, Any]]]:
    """Preserve every meaningful native cell with explicit grid coordinates."""

    evidence: list[tuple[int, str, dict[str, Any]]] = []
    for table_index, table in enumerate(page.get("tables", []), 1):
        if not _is_preservable_native_table(table):
            continue
        coordinates: list[str] = []
        quote_lines = [f"Native table {table_index}; zero-based row and column coordinates."]
        for row_index, row in enumerate(table):
            if not isinstance(row, list):
                continue
            row_values = [str(cell).strip() if cell is not None else "" for cell in row]
            if any(row_values):
                quote_lines.append(
                    f"row={row_index};values={json.dumps(row_values, ensure_ascii=False)}"
                )
            for column_index, cell in enumerate(row):
                value = str(cell).strip() if cell is not None else ""
                if not value:
                    continue
                encoded_value = json.dumps(value, ensure_ascii=False)
                coordinate = (
                    f"table={table_index};row={row_index};column={column_index};"
                    f"value={encoded_value}"
                )
                if len(coordinate) > 10_000:
                    raise ValueError("A native table cell exceeds the closed evidence contract.")
                coordinates.append(coordinate)
        if not coordinates:
            continue
        evidence.append(
            (
                table_index,
                "\n".join(quote_lines),
                {
                    "span_ids": [],
                    "table": {
                        "selector_semantics": [
                            "Table indices are one-based in native pdfplumber reading order.",
                            (
                                "Rows and columns are zero-based source grid coordinates; "
                                "merged-cell semantics remain unresolved until rule validation."
                            ),
                            "Cell values are JSON-encoded source text.",
                        ],
                        "column_labels": [],
                        "row_labels": [],
                        "cell_coordinates": coordinates,
                        "units": [],
                        "footnote_span_ids": [],
                        "continued_page_ids": [],
                    },
                    "notes": [
                        "Native table grid retained separately from flattened page reading order."
                    ],
                },
            )
        )
    return evidence


def _has_meaningful_native_table(page: dict[str, Any]) -> bool:
    return any(_is_meaningful_native_table(table) for table in page.get("tables", []))


def _span_groups(
    page: dict[str, Any],
    selected_text: str,
    *,
    use_native_lines: bool = True,
) -> list[tuple[str, list[float]]]:
    lines = page.get("lines", []) if use_native_lines else []
    groups: list[tuple[str, list[float]]] = []
    if lines:
        current: list[dict[str, Any]] = []
        size = 0
        for line in lines:
            text = str(line.get("text", "")).strip()
            if not text:
                continue
            if current and size + len(text) > 2_500:
                groups.append(
                    _line_group(
                        current,
                        width=float(page["width"]),
                        height=float(page["height"]),
                    )
                )
                current, size = [], 0
            current.append(line)
            size += len(text) + 1
        if current:
            groups.append(
                _line_group(
                    current,
                    width=float(page["width"]),
                    height=float(page["height"]),
                )
            )
    elif selected_text.strip():
        chunks = [
            selected_text[index : index + 2_500] for index in range(0, len(selected_text), 2_500)
        ]
        bbox = [0.0, 0.0, float(page["width"]), float(page["height"])]
        groups.extend((chunk, bbox) for chunk in chunks if chunk.strip())
    return groups


def _line_group(
    lines: list[dict[str, Any]], *, width: float, height: float
) -> tuple[str, list[float]]:
    left = min(float(item["x0"]) for item in lines)
    top = min(float(item["top"]) for item in lines)
    right = max(float(item["x1"]) for item in lines)
    bottom = max(float(item["bottom"]) for item in lines)
    return (
        "\n".join(str(item["text"]) for item in lines),
        [
            max(0.0, min(width, left)),
            max(0.0, min(height, top)),
            max(0.0, min(width, right)),
            max(0.0, min(height, bottom)),
        ],
    )


def _evidence_source_kwargs(job: ProcessingJob) -> dict[str, object]:
    if job.source_capture_id:
        return {"source_capture": job.source_capture, "customer_uploaded_document": None}
    return {"source_capture": None, "customer_uploaded_document": job.customer_uploaded_document}


def run_reconcile(job: ProcessingJob) -> dict[str, Any]:
    read = parent_artifact(job)
    pages: list[dict[str, Any]] = read["native"]["pages"]
    ocr_pages: dict[str, str] = read.get("ocr", {}).get("pages", {})
    docling_pages = _docling_page_text(read["layout"])
    docling_tables = _docling_page_table_text(read["layout"])
    original = _original(job)
    issues: list[dict[str, Any]] = list(read.get("issues", []))
    spans: list[dict[str, Any]] = []
    is_html = read["classification"]["media_type"] == "text/html"
    for page in pages:
        page_number = int(page["page_number"])
        native_text = str(page["text"])
        ocr_text = str(ocr_pages.get(str(page_number), ""))
        selected_text = ocr_text if page["needs_ocr"] else native_text
        method = "ocr_verified" if page["needs_ocr"] else ("html" if is_html else "native_text")
        page_row = None
        if not is_html:
            page_row = DocumentPage.objects.get(original_file=original, page_number=page_number)
        page_issues: list[dict[str, Any]] = []
        if not selected_text.strip():
            page_issues.append(
                issue(
                    "unreadable_page",
                    f"Physical page {page_number} has no usable native or OCR text.",
                    material=True,
                    retry_instruction="Visually inspect and transcribe this exact physical page.",
                )
            )
        layout_text = docling_pages.get(page_number, "")
        if selected_text.strip() and not layout_text.strip():
            page_issues.append(
                issue(
                    "layout_page_missing",
                    f"Docling returned no reading-order content for physical page {page_number}.",
                    material=True,
                    retry_instruction="Visually verify the complete physical page text and order.",
                )
            )
        elif layout_text and selected_text:
            similarity = _normalized_similarity(layout_text, selected_text)
            if similarity < 0.50:
                page_issues.append(
                    issue(
                        "reader_text_disagreement",
                        f"Readers disagree on physical page {page_number} (similarity {similarity:.3f}).",
                        material=True,
                        retry_instruction="Visually reconcile the native/OCR text with Docling order.",
                    )
                )
        docling_table_count = sum(
            1
            for node in read["layout"].get("nodes", [])
            if node.get("label") == "table"
            and any(
                isinstance(prov, dict) and prov.get("page_no", prov.get("page")) == page_number
                for prov in node.get("provenance", [])
            )
        )
        meaningful_native_table = _has_meaningful_native_table(page)
        if meaningful_native_table and docling_table_count == 0:
            page_issues.append(
                issue(
                    "reader_table_disagreement",
                    f"pdfplumber found a table on physical page {page_number}; Docling did not.",
                    material=True,
                    retry_instruction="Visually reconcile the table, axes, units and footnotes.",
                )
            )
        elif meaningful_native_table:
            table_similarity = _normalized_similarity(
                _native_table_text(page),
                docling_tables.get(page_number, ""),
            )
            if table_similarity < 0.80:
                page_issues.append(
                    issue(
                        "reader_table_text_disagreement",
                        "Readers disagree on table cells or labels on physical page "
                        f"{page_number} (similarity {table_similarity:.3f}).",
                        material=True,
                        retry_instruction=(
                            "Visually reconcile every table axis, cell, unit and footnote."
                        ),
                    )
                )
        docling_picture_count = sum(
            1
            for node in read["layout"].get("nodes", [])
            if node.get("label") == "picture"
            and any(
                isinstance(prov, dict) and prov.get("page_no", prov.get("page")) == page_number
                for prov in node.get("provenance", [])
            )
        )
        native_figure_count = int(page.get("figure_count", 0))
        if native_figure_count != docling_picture_count:
            page_issues.append(
                issue(
                    "reader_figure_count_disagreement",
                    "Readers report different figure counts on physical page "
                    f"{page_number} (native={native_figure_count}, "
                    f"Docling={docling_picture_count}).",
                    material=False,
                    retry_instruction=(
                        "Visually inspect figures before relying on figure-only information."
                    ),
                )
            )
        for index, (quote, bbox) in enumerate(
            _span_groups(page, selected_text, use_native_lines=not page["needs_ocr"]), 1
        ):
            quote_hash = hashlib.sha256(quote.encode()).hexdigest()[:16]
            section = f"processed-page-{page_number}-{index}-{quote_hash}"
            locator: dict[str, Any]
            if is_html:
                locator = {
                    "schema_version": 1,
                    "blob_sha256": original.sha256,
                    "resolver_version": "coverguide-html/1",
                    "kind": "html_element",
                    "encoding": "utf-8",
                    "selector": "body",
                    "selector_language": "css",
                    "occurrence": 0,
                    "text_interpretation": "decoded_text_content",
                    "attribute_name": None,
                }
            else:
                locator = {
                    "schema_version": 1,
                    "blob_sha256": original.sha256,
                    "resolver_version": "coverguide-pdf/1",
                    "kind": "pdf_region",
                    "physical_page": page_number,
                    "bbox": bbox,
                    "coordinate_space": "unrotated_pdf_points",
                    "rotation": int(page["rotation"]),
                }
            context = {
                "span_ids": [],
                "notes": [
                    f"Reader reconciliation for physical page {page_number}.",
                    *(
                        ["Possible footnote region."]
                        if bbox[1] > float(page["height"]) * 0.80
                        else []
                    ),
                ],
            }
            desired_verification = "text_verified" if not page_issues else "unverified"
            span, created = EvidenceSpan.objects.get_or_create(
                page=page_row,
                section_label=section,
                **_evidence_source_kwargs(job),
                defaults={
                    "quote": quote,
                    "context": context,
                    "method": method,
                    "verification": desired_verification,
                    "locator": locator,
                },
            )
            if (
                not created
                and span.verification not in {"visually_verified", "reviewed"}
                and span.verification != desired_verification
            ):
                if PolicyRuleEvidence.objects.filter(evidence_span=span).exists():
                    page_issues.append(
                        issue(
                            "published_evidence_reader_conflict",
                            f"A newly detected reader conflict affects cited evidence on physical page {page_number}.",
                            material=True,
                            retry_instruction="Reconcile the cited page before creating a replacement release.",
                            region_span_ids=[str(span.id)],
                        )
                    )
                else:
                    span.context = context
                    span.method = method
                    span.verification = desired_verification
                    span.locator = locator
                    span.save(update_fields=["context", "method", "verification", "locator"])
            spans.append(
                {
                    "id": str(span.id),
                    "page_number": page_number,
                    "quote": quote,
                    "method": method,
                }
            )
        if not is_html and not page["needs_ocr"]:
            assert page_row is not None
            table_locator = {
                "schema_version": 1,
                "blob_sha256": original.sha256,
                "resolver_version": "coverguide-pdf/1",
                "kind": "pdf_region",
                "physical_page": page_number,
                "bbox": [0.0, 0.0, float(page["width"]), float(page["height"])],
                "coordinate_space": "unrotated_pdf_points",
                "rotation": int(page["rotation"]),
            }
            for table_index, quote, context in _native_table_evidence(page):
                quote_hash = hashlib.sha256(quote.encode()).hexdigest()[:16]
                section = f"processed-table-{page_number}-{table_index}-{quote_hash}"
                desired_verification = "text_verified" if not page_issues else "unverified"
                span, created = EvidenceSpan.objects.get_or_create(
                    page=page_row,
                    section_label=section,
                    **_evidence_source_kwargs(job),
                    defaults={
                        "quote": quote,
                        "context": context,
                        "method": "native_text",
                        "verification": desired_verification,
                        "locator": table_locator,
                    },
                )
                if (
                    not created
                    and span.verification not in {"visually_verified", "reviewed"}
                    and span.verification != desired_verification
                ):
                    if PolicyRuleEvidence.objects.filter(evidence_span=span).exists():
                        page_issues.append(
                            issue(
                                "published_evidence_reader_conflict",
                                "A newly detected reader conflict affects cited table evidence "
                                f"on physical page {page_number}.",
                                material=True,
                                retry_instruction=(
                                    "Reconcile the cited table before creating a replacement release."
                                ),
                                region_span_ids=[str(span.id)],
                            )
                        )
                    else:
                        span.context = context
                        span.method = "native_text"
                        span.verification = desired_verification
                        span.locator = table_locator
                        span.save(update_fields=["context", "method", "verification", "locator"])
                spans.append(
                    {
                        "id": str(span.id),
                        "page_number": page_number,
                        "quote": quote,
                        "method": "native_text",
                        "table_index": table_index,
                    }
                )
        issues.extend(page_issues)
        if page_row is not None:
            page_row.review_state = "unresolved" if page_issues else "text_read"
            page_row.save(update_fields=["review_state", "updated_at"])
    if job.customer_uploaded_document_id:
        upload = job.customer_uploaded_document
        if upload is None:
            raise ValueError("Processing job references a missing customer document.")
        upload.review_status = "readable" if not issues else "conflicted"
        upload.save(update_fields=["review_status", "updated_at"])
    elif not any(item.get("material") and not item.get("resolved") for item in issues):
        document_version = _capture(job).document_version
        if document_version is not None:
            document_version.review_status = "verified"
            document_version.save(update_fields=["review_status", "updated_at"])
    return {
        "schema_version": 1,
        "reconciliation_version": RECONCILIATION_VERSION,
        "document_sha256": original.sha256,
        "page_count": len(pages),
        "page_numbers": [int(item["page_number"]) for item in pages],
        "evidence_spans": spans,
        "issues": issues,
    }


def _policy_version(job: ProcessingJob) -> PolicyVersion:
    capture = _capture(job)
    if not capture.document_version_id:
        raise ValueError("Policy-rule processing requires a public document version.")
    version_ids = PolicyVersionDocument.objects.filter(
        document_version_id=capture.document_version_id
    ).values_list("policy_version_id", flat=True)
    versions = PolicyVersion.objects.filter(id__in=version_ids)
    if versions.count() != 1:
        raise ValueError("The processing source must belong to exactly one policy version.")
    return versions.get()


def _selected_variant_name(policy_version: PolicyVersion) -> str:
    names = list(
        ProductVariant.objects.filter(policy_version=policy_version).values_list("name", flat=True)
    )
    if len(names) != 1 or not names[0].strip():
        raise ValueError("Rule processing requires exactly one selected comparison variant.")
    return names[0]


def _bundle_passages(policy_version: PolicyVersion) -> list[dict[str, Any]]:
    memberships = {
        item.document_version_id: item
        for item in PolicyVersionDocument.objects.filter(
            policy_version=policy_version
        ).select_related("document_version__document_series")
    }
    document_ids = set(memberships)
    capture_ids: list[uuid.UUID] = []
    for document_id in sorted(document_ids, key=str):
        capture = (
            SourceCapture.objects.filter(
                document_version_id=document_id,
                status="captured",
                original_file__isnull=False,
            )
            .order_by("-completed_at", "-created_at")
            .first()
        )
        if capture is None:
            raise ValueError(
                f"Policy bundle document {document_id} has no current successful capture."
            )
        capture_ids.append(capture.id)
    spans = (
        EvidenceSpan.objects.filter(
            source_capture_id__in=capture_ids,
            verification__in=["text_verified", "visually_verified", "reviewed"],
        )
        .select_related(
            "source_capture__document_version__document_series",
            "page",
        )
        .order_by("source_capture_id", "page__page_number", "created_at")
    )
    passages: list[dict[str, Any]] = []
    for span in spans:
        capture = span.source_capture
        if capture is None or capture.document_version_id is None:
            raise ValueError("Public bundle evidence is missing its document identity.")
        membership = memberships[capture.document_version_id]
        version = membership.document_version
        series = version.document_series
        passages.append(
            {
                "evidence_span_id": str(span.id),
                "passage": span.quote,
                "document_version_id": str(version.id),
                "document_role": membership.role,
                "document_kind": series.kind,
                "document_authority": series.authority,
                "document_name": series.name,
                "required_for_policy": membership.required_for_policy,
                "physical_page": span.page.page_number if span.page is not None else None,
                "published_on": str(version.published_on) if version.published_on else None,
                "effective_from": (str(version.effective_from) if version.effective_from else None),
                "effective_to": str(version.effective_to) if version.effective_to else None,
            }
        )
    return passages


def _passage_payloads(policy_version: PolicyVersion) -> list[tuple[list[dict[str, Any]], str]]:
    passages = _bundle_passages(policy_version)
    if not passages:
        raise ValueError("The policy bundle has no reconciled verified passages.")
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_size = 2
    for passage in passages:
        encoded_passage = json.dumps(passage, ensure_ascii=False, separators=(",", ":"))
        added_size = len(encoded_passage) + (1 if current else 0)
        if len(encoded_passage) + 2 > MAX_MODEL_PASSAGE_CHARACTERS:
            raise ValueError("One exact evidence passage exceeds the qualified extraction context.")
        if current and current_size + added_size > MAX_MODEL_PASSAGE_CHARACTERS:
            batches.append(current)
            current = []
            current_size = 2
            added_size = len(encoded_passage)
        current.append(passage)
        current_size += added_size
    if current:
        batches.append(current)
    return [
        (batch, json.dumps(batch, ensure_ascii=False, separators=(",", ":"))) for batch in batches
    ]


def _previous_extraction_batch(
    job: ProcessingJob, categories: tuple[str, ...]
) -> tuple[PolicyRuleExtractionV1 | None, int]:
    category_set = set(categories)
    previous: PolicyRuleExtractionV1 | None = None
    attempt_count = 0
    attempts = ModelAttempt.objects.filter(
        # A different ProcessingJob can belong to an older rule-prompt
        # version despite sharing the document adapter and parent artifact.
        # call_model separately reuses only byte-for-byte request commitments.
        processing_job=job,
        qualification__schema_name="policy_extraction",
        status="succeeded",
        response_storage_key__isnull=False,
        response_storage_sha256__isnull=False,
    ).order_by("-created_at")
    for attempt in attempts:
        assert attempt.response_storage_key is not None
        assert attempt.response_storage_sha256 is not None
        namespace = attempt.owner_id or uuid.UUID(int=0)
        payload = read_private(
            namespace,
            f"model-result-{attempt.id}",
            attempt.response_storage_key,
            attempt.response_storage_sha256,
        )
        result = PolicyRuleExtractionV1.model_validate_json(payload)
        observed_categories = {item.inventory_category for item in result.rules}
        observed_categories.update(result.omitted_inventory_categories)
        observed_categories.update(
            description.partition(":")[0]
            for description in result.material_issues
            if description.partition(":")[0] in INVENTORY_CATEGORIES
        )
        if not observed_categories or not observed_categories.issubset(category_set):
            continue
        attempt_count += 1
        if previous is None:
            previous = result
    return previous, attempt_count


def _run_extraction_batch(
    *,
    job: ProcessingJob,
    policy_version: PolicyVersion,
    encoded_passages: str,
    categories: tuple[str, ...],
    evidence_batch_label: str,
    deadline: float,
) -> PolicyRuleExtractionV1:
    variant_name = _selected_variant_name(policy_version)
    previous: PolicyRuleExtractionV1 | None = None
    targets: list[str] = []
    for attempt_number in range(1, RULE_BATCH_MAX_ATTEMPTS + 1):
        _renew_rule_lease(job)
        retry_context = ""
        if targets:
            retry_context = (
                "This is targeted retry "
                f"{attempt_number - 1} of {RULE_BATCH_MAX_ATTEMPTS - 1}. Return a complete "
                "replacement for this batch, retaining correct rules while encoding every "
                "unresolved item. "
                + (
                    "Previous output: " + previous.model_dump_json() + " "
                    if previous is not None
                    else ""
                )
                + " Unresolved items: "
                + json.dumps(targets, ensure_ascii=False)
            )
        messages = [
            {
                "role": "system",
                "content": (
                    f"Prompt protocol: {RULE_PROMPT_VERSION}. "
                    "Return PolicyRuleExtractionV1 only. Extract atomic executable RuleV1 bodies. "
                    "Each body field must be a JSON-encoded RuleV1 object string. "
                    "Use only supplied exact evidence_span_ids. Work only on this fixed inventory "
                    "batch. Every category in the batch is REQUIRED to have an explicit "
                    "disposition: a rule, an entry in omitted_inventory_categories, or a "
                    "material_issues entry prefixed exactly 'category: description'. A category "
                    "with none of these is a validation failure and forces a retry -- never silently "
                    "skip a category. Do not report categories outside the batch. "
                    "Preserve all definitions, restrictions, exceptions, dependencies, table axes "
                    "and units relevant to the batch. Passages may describe other variants or "
                    "optional add-ons: attribute only rules that apply to the selected comparison "
                    "variant, and encode any required configuration applicability explicitly. "
                    + _buying_scope_instruction()
                    + _table_output_instruction()
                    + _stable_rule_key_instruction()
                    + _authored_amount_instruction()
                    + _eligibility_and_schedule_table_instruction()
                ),
            },
            {
                "role": "system",
                "content": "Fixed inventory batch: " + json.dumps(categories),
            },
            *(
                [
                    {
                        "role": "system",
                        "content": (
                            f"Evidence batch: {evidence_batch_label}. Extract only rules whose "
                            "complete support is present in this evidence batch. Category omissions "
                            "apply only to this evidence batch; the pipeline combines every batch "
                            "without dropping IDs."
                        ),
                    }
                ]
                if evidence_batch_label != "1/1"
                else []
            ),
            {
                "role": "system",
                "content": "Approved executable rule contract: " + _rule_contract_prompt(),
            },
        ]
        if retry_context:
            messages.append({"role": "system", "content": retry_context})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Policy version {policy_version.id}, UIN {policy_version.uin}. "
                    f"Selected comparison variant: {variant_name}. "
                    f"Original passages: {encoded_passages}"
                ),
            }
        )
        try:
            result = call_model(
                model=settings.COVERGUIDE_POLICY_EXTRACTION_MODEL,
                schema_name="policy_extraction",
                output_type=PolicyRuleExtractionV1,
                messages=messages,
                remaining_seconds=_remaining_rule_seconds(deadline),
                processing_job=job,
                reuse_successful_processing_result=True,
            )
        except RelayFailure as exc:
            if (
                exc.code not in RULE_RETRYABLE_RELAY_CODES
                or attempt_number >= RULE_BATCH_MAX_ATTEMPTS
            ):
                raise
            targets = [
                f"The prior call failed technically with {exc.code}; retry exactly this batch."
            ]
            continue
        targets = _extraction_batch_targets(str(policy_version.id), categories, result)
        if not targets:
            return result
        previous = result
    assert previous is not None
    return previous


def _combine_extraction_evidence_batches(
    policy_version_id: str,
    categories: tuple[str, ...],
    values: list[PolicyRuleExtractionV1],
) -> PolicyRuleExtractionV1:
    category_set = set(categories)
    by_key: dict[str, list[ExtractedPolicyRule]] = defaultdict(list)
    material_issues: list[str] = []
    for value in values:
        if value.policy_version_id != policy_version_id:
            raise ValueError("Policy extraction returned a different policy-version identity.")
        material_issues.extend(value.material_issues)
        for rule in value.rules:
            if rule.inventory_category not in category_set:
                material_issues.append(
                    f"{rule.rule_key}: category outside its fixed evidence batch was excluded."
                )
                continue
            by_key[rule.rule_key].append(rule)
    rules: list[ExtractedPolicyRule] = []
    for rule_key in sorted(by_key):
        candidates = by_key[rule_key]
        if len(candidates) != 1:
            material_issues.append(
                f"{rule_key}: duplicate cross-evidence rule key was excluded as ambiguous."
            )
            continue
        rules.append(candidates[0])
    covered = {item.inventory_category for item in rules}
    return PolicyRuleExtractionV1(
        schema_version=1,
        policy_version_id=policy_version_id,
        rules=rules,
        omitted_inventory_categories=sorted(category_set - covered),
        material_issues=material_issues,
    )


def run_extract(job: ProcessingJob) -> dict[str, Any]:
    policy_version = _policy_version(job)
    payloads = _passage_payloads(policy_version)
    deadline = time.monotonic() + RULE_STAGE_TIMEOUT_SECONDS
    results: list[tuple[tuple[str, ...], PolicyRuleExtractionV1]] = []
    for categories in INVENTORY_CATEGORY_BATCHES:
        evidence_results = [
            _run_extraction_batch(
                job=job,
                policy_version=policy_version,
                encoded_passages=encoded,
                categories=categories,
                evidence_batch_label=f"{index}/{len(payloads)}",
                deadline=deadline,
            )
            for index, (_passages, encoded) in enumerate(payloads, start=1)
        ]
        result = _combine_extraction_evidence_batches(
            str(policy_version.id), categories, evidence_results
        )
        results.append((categories, result))
    return _combine_extraction_batches(str(policy_version.id), results).model_dump(mode="json")


def _run_review_batch(
    *,
    job: ProcessingJob,
    policy_version: PolicyVersion,
    encoded_passages: str,
    categories: tuple[str, ...],
    candidates: tuple[ExtractedPolicyRule, ...],
    evidence_batch_label: str,
    deadline: float,
) -> PolicyRuleReviewV1:
    variant_name = _selected_variant_name(policy_version)
    previous: PolicyRuleReviewV1 | None = None
    targets: list[str] = []
    for attempt_index in range(RULE_BATCH_MAX_ATTEMPTS):
        _renew_rule_lease(job)
        retry_context = ""
        if previous is not None:
            retry_context = (
                "This is targeted retry "
                f"{attempt_index} of {RULE_BATCH_MAX_ATTEMPTS - 1}. Return a complete corrected "
                "independent review for this batch. Re-check every candidate against the original "
                "passages. Your previous output: "
                + previous.model_dump_json()
                + " Structural corrections: "
                + json.dumps(targets, ensure_ascii=False)
            )
        messages = [
            {
                "role": "system",
                "content": (
                    f"Prompt protocol: {RULE_REVIEW_PROMPT_VERSION}; candidate extraction "
                    f"protocol: {RULE_PROMPT_VERSION}. "
                    "Independently verify each supplied candidate rule against the original policy "
                    "passages. Return PolicyRuleReviewV1 only and review every candidate key exactly "
                    "once. Use verdict agree only when every condition, input, effect, number, unit, "
                    "scope, dependency, table relationship and evidence span is supported. For an "
                    "agreement, return the exact candidate RuleV1 as independent_body and cite every "
                    "candidate evidence span; otherwise return disagree, missing or ambiguous and "
                    "explain the material issue. Put independently discovered additional atomic "
                    "RuleV1 rules in missing_rules. Each body field must be a JSON-encoded RuleV1 "
                    "object string. Use only supplied evidence_span_ids. Set inventory_categories "
                    "to exactly the fixed batch and do not return rules from another category. "
                    "Passages may describe other variants or optional add-ons: inventory only "
                    "rules that apply to the selected comparison variant and encode any required "
                    "configuration applicability explicitly. "
                    + _buying_scope_instruction()
                    + _table_output_instruction()
                    + _stable_rule_key_instruction()
                    + _authored_amount_instruction()
                    + _eligibility_and_schedule_table_instruction()
                ),
            },
            {
                "role": "system",
                "content": "Fixed inventory batch: " + json.dumps(categories),
            },
            *(
                [
                    {
                        "role": "system",
                        "content": (
                            f"Evidence batch: {evidence_batch_label}. Review candidates only against "
                            "this exact part of the reconciled bundle. Use missing when the required "
                            "evidence is outside this part; use disagree or ambiguous for an actual "
                            "conflict."
                        ),
                    }
                ]
                if evidence_batch_label != "1/1"
                else []
            ),
            {
                "role": "system",
                "content": "Approved executable rule contract: " + _rule_contract_prompt(),
            },
            {
                "role": "system",
                "content": "Candidate rules requiring independent verification: "
                + json.dumps(
                    [item.model_dump(mode="json") for item in candidates],
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            },
        ]
        if retry_context:
            messages.append({"role": "system", "content": retry_context})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Policy version {policy_version.id}, UIN {policy_version.uin}. "
                    f"Selected comparison variant: {variant_name}. "
                    f"Original passages: {encoded_passages}"
                ),
            }
        )
        try:
            result = call_model(
                model=settings.COVERGUIDE_POLICY_REVIEW_MODEL,
                schema_name="policy_review",
                output_type=PolicyRuleReviewV1,
                messages=messages,
                remaining_seconds=_remaining_rule_seconds(deadline),
                processing_job=job,
                reuse_successful_processing_result=True,
            )
        except RelayFailure as exc:
            if (
                exc.code not in RULE_RETRYABLE_RELAY_CODES
                or attempt_index + 1 >= RULE_BATCH_MAX_ATTEMPTS
            ):
                raise
            targets = [
                f"The prior call failed technically with {exc.code}; retry exactly this batch."
            ]
            continue
        targets = _review_batch_targets(str(policy_version.id), categories, result, candidates)
        if not targets:
            return result
        previous = result
    # A structurally valid response may still contain rule-level table or inventory
    # defects after both targeted retries. Preserve it for the deterministic
    # validation stage, which excludes those individual rules and records warnings.
    # Transport, identity and response-schema failures still fail closed above.
    assert previous is not None
    return previous


def _combine_review_evidence_batches(
    policy_version_id: str,
    categories: tuple[str, ...],
    candidates: tuple[ExtractedPolicyRule, ...],
    values: list[PolicyRuleReviewV1],
) -> PolicyRuleReviewV1:
    reviews_by_key: dict[str, list[ReviewedPolicyRule]] = defaultdict(list)
    missing_by_key: dict[str, list[ExtractedPolicyRule]] = defaultdict(list)
    for value in values:
        if value.policy_version_id != policy_version_id:
            raise ValueError("Independent review returned a different policy-version identity.")
        if set(value.inventory_categories) != set(categories):
            raise ValueError("Independent review did not inventory its exact fixed batch.")
        for reviewed in value.reviews:
            reviews_by_key[reviewed.rule_key].append(reviewed)
        for rule in value.missing_rules:
            if rule.inventory_category in set(categories):
                missing_by_key[rule.rule_key].append(rule)
    combined_reviews: list[ReviewedPolicyRule] = []
    for candidate in candidates:
        reviews = reviews_by_key.get(candidate.rule_key, [])
        conflicting = next(
            (item for item in reviews if item.verdict in {"disagree", "ambiguous"}), None
        )
        agreements = [
            item
            for item in reviews
            if item.verdict == "agree"
            and item.independent_body is not None
            and _semantic_body(item.independent_body) == _semantic_body(candidate.body)
        ]
        if conflicting is not None:
            combined_reviews.append(conflicting)
        elif agreements:
            evidence_span_ids = sorted(
                {span_id for item in agreements for span_id in item.evidence_span_ids}
            )
            combined_reviews.append(
                ReviewedPolicyRule(
                    rule_key=candidate.rule_key,
                    verdict="agree",
                    independent_body=candidate.body,
                    evidence_span_ids=evidence_span_ids,
                    material_issue=None,
                )
            )
        else:
            combined_reviews.append(
                ReviewedPolicyRule(
                    rule_key=candidate.rule_key,
                    verdict="missing",
                    independent_body=None,
                    evidence_span_ids=[],
                    material_issue="No evidence batch independently verified the complete rule.",
                )
            )
    missing_rules = [
        rules[0]
        for rule_key, rules in sorted(missing_by_key.items())
        if len(rules) == 1 and rule_key not in {item.rule_key for item in candidates}
    ]
    return PolicyRuleReviewV1(
        schema_version=1,
        policy_version_id=policy_version_id,
        inventory_categories=list(categories),
        reviews=combined_reviews,
        missing_rules=missing_rules,
    )


def run_independent_review(job: ProcessingJob) -> dict[str, Any]:
    policy_version = _policy_version(job)
    payloads = _passage_payloads(policy_version)
    extraction = PolicyRuleExtractionV1.model_validate(read_artifact(_ancestor(job, "extract")))
    deadline = time.monotonic() + RULE_STAGE_TIMEOUT_SECONDS
    results: list[tuple[tuple[str, ...], PolicyRuleReviewV1]] = []
    for categories in INVENTORY_CATEGORY_BATCHES:
        category_set = set(categories)
        candidates = tuple(
            item for item in extraction.rules if item.inventory_category in category_set
        )
        evidence_results = [
            _run_review_batch(
                job=job,
                policy_version=policy_version,
                encoded_passages=encoded,
                categories=categories,
                candidates=candidates,
                evidence_batch_label=f"{index}/{len(payloads)}",
                deadline=deadline,
            )
            for index, (_passages, encoded) in enumerate(payloads, start=1)
        ]
        result = _combine_review_evidence_batches(
            str(policy_version.id), categories, candidates, evidence_results
        )
        results.append((categories, result))
    return _combine_review_batches(str(policy_version.id), results).model_dump(mode="json")


def _ancestor(job: ProcessingJob, stage: str) -> ProcessingJob:
    current = job.parent_job
    while current is not None:
        if current.stage == stage:
            return current
        current = current.parent_job
    raise ValueError(f"Processing lineage is missing required {stage} stage.")


def _semantic_body(body: dict[str, Any]) -> str:
    normalized = dict(body)
    normalized.pop("source_span_ids", None)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def _evidence_role(body: dict[str, Any]) -> str:
    effects = [item for item in body.get("effects", []) if isinstance(item, dict)]
    kinds = {item.get("kind") for item in effects}
    if "exception" in kinds:
        return "excepts"
    if "exclusion" in kinds or "limit" in kinds or "deduction" in kinds or "waiting" in kinds:
        return "restricts"
    if any(
        item.get("kind") == "eligibility" and item.get("decision") != "eligible" for item in effects
    ):
        return "restricts"
    if "definition" in kinds:
        return "defines"
    if "precedence" in kinds:
        return "precedence"
    return "supports"


def _get_or_create_policy_rule_revision(
    *,
    policy_version: PolicyVersion,
    rule_key: str,
    rule_type: str,
    body: dict[str, Any],
) -> PolicyRule:
    """Return the current identical head or append one immutable correction."""

    lock_key = f"policy-rule:{policy_version.id}:{rule_key}"
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 918273645))", [lock_key])
    revisions = list(
        PolicyRule.objects.select_for_update()
        .filter(policy_version=policy_version, rule_key=rule_key)
        .order_by("created_at", "id")
    )
    predecessor_ids = {
        revision.supersedes_id for revision in revisions if revision.supersedes_id is not None
    }
    heads = [revision for revision in revisions if revision.id not in predecessor_ids]
    if revisions and len(heads) != 1:
        raise ValueError("the logical rule does not have exactly one lineage head")
    if not heads:
        return PolicyRule.objects.create(
            policy_version=policy_version,
            rule_key=rule_key,
            rule_type=rule_type,
            body=body,
            review_status="draft",
        )
    head = heads[0]
    if head.review_status == "superseded":
        raise ValueError("the logical rule lineage head is already marked superseded")
    if head.rule_type == rule_type and head.body == body:
        return head
    return PolicyRule.objects.create(
        policy_version=policy_version,
        rule_key=rule_key,
        rule_type=rule_type,
        body=body,
        review_status="draft",
        supersedes=head,
    )


@transaction.atomic
def run_validate(job: ProcessingJob) -> dict[str, Any]:
    policy_version = _policy_version(job)
    extraction = PolicyRuleExtractionV1.model_validate(read_artifact(_ancestor(job, "extract")))
    review = PolicyRuleReviewV1.model_validate(parent_artifact(job))
    issues: list[dict[str, Any]] = []
    reviewed_categories = set(review.inventory_categories)
    unknown_categories = reviewed_categories - INVENTORY_CATEGORIES
    missing_categories = INVENTORY_CATEGORIES - reviewed_categories
    if unknown_categories or missing_categories:
        issues.append(
            issue(
                "incomplete_independent_inventory",
                "Independent inventory category mismatch; missing="
                + ",".join(sorted(missing_categories))
                + "; unknown="
                + ",".join(sorted(unknown_categories)),
                material=False,
                retry_instruction="Keep missing categories unknown in the alpha release.",
            )
        )
    if extraction.material_issues:
        issues.extend(
            issue(
                "extraction_material_issue",
                value,
                material=False,
                retry_instruction="Exclude the unresolved rule and expose its category as unknown.",
            )
            for value in extraction.material_issues
        )
    if extraction.omitted_inventory_categories:
        issues.append(
            issue(
                "omitted_inventory_categories",
                ", ".join(extraction.omitted_inventory_categories),
                material=False,
                retry_instruction="Keep omitted categories unknown in the alpha release.",
            )
        )
    independent_counts = Counter(item.rule_key for item in review.missing_rules)
    independent: dict[str, ExtractedPolicyRule] = {
        item.rule_key: item
        for item in review.missing_rules
        if independent_counts[item.rule_key] == 1
    }
    duplicate_independent_keys = sorted(
        key for key, count in independent_counts.items() if count > 1
    )
    if duplicate_independent_keys:
        issues.append(
            issue(
                "duplicate_independent_rule_key",
                ", ".join(duplicate_independent_keys),
                material=False,
                retry_instruction="Exclude ambiguous duplicate keys from the alpha release.",
            )
        )
    extracted_by_key = {item.rule_key: item for item in extraction.rules}
    review_counts = Counter(item.rule_key for item in review.reviews)
    for reviewed in review.reviews:
        extracted = extracted_by_key.get(reviewed.rule_key)
        if (
            extracted is None
            or review_counts[reviewed.rule_key] != 1
            or reviewed.verdict != "agree"
            or reviewed.independent_body is None
        ):
            continue
        independent[reviewed.rule_key] = ExtractedPolicyRule(
            rule_key=reviewed.rule_key,
            rule_type=extracted.rule_type,
            inventory_category=extracted.inventory_category,
            body=reviewed.independent_body,
            evidence_span_ids=reviewed.evidence_span_ids,
            table_cells=extracted.table_cells,
            table_footnote_span_ids=extracted.table_footnote_span_ids,
        )
    allowed_span_ids = {str(item["evidence_span_id"]) for item in _bundle_passages(policy_version)}
    validation_savepoint = transaction.savepoint()
    verified: list[PolicyRule] = []
    seen_keys: set[str] = set()
    for extracted in extraction.rules:
        if extracted.rule_key in seen_keys:
            issues.append(
                issue(
                    "duplicate_extracted_rule_key",
                    extracted.rule_key,
                    material=False,
                    retry_instruction="Exclude the duplicated rule key from the alpha release.",
                )
            )
            continue
        seen_keys.add(extracted.rule_key)
        counterpart = independent.get(extracted.rule_key)
        if counterpart is None:
            issues.append(
                issue(
                    "independent_rule_missing",
                    extracted.rule_key,
                    material=False,
                    retry_instruction="Exclude this unconfirmed rule from the alpha release.",
                )
            )
            continue
        try:
            body = validate_contract("RuleV1", extracted.body)
            independent_body = validate_contract("RuleV1", counterpart.body)
        except ValueError as exc:
            issues.append(
                issue(
                    "invalid_rule_contract",
                    f"{extracted.rule_key}: {exc}",
                    material=False,
                    retry_instruction="Exclude the invalid rule from the alpha release.",
                )
            )
            continue
        if not isinstance(body, dict) or not isinstance(independent_body, dict):
            issues.append(
                issue(
                    "invalid_rule_contract",
                    f"{extracted.rule_key}: RuleV1 must be an object.",
                    material=False,
                    retry_instruction="Exclude the invalid rule from the alpha release.",
                )
            )
            continue
        if extracted.rule_type not in RULE_TYPES:
            issues.append(
                issue(
                    "unregistered_rule_type",
                    f"{extracted.rule_key}: {extracted.rule_type}",
                    material=False,
                    retry_instruction="Exclude the unregistered rule from the alpha release.",
                )
            )
            continue
        if extracted.inventory_category not in INVENTORY_CATEGORIES:
            issues.append(
                issue(
                    "unregistered_inventory_category",
                    f"{extracted.rule_key}: {extracted.inventory_category}",
                    material=False,
                    retry_instruction="Exclude the unregistered category from the alpha release.",
                )
            )
            continue
        if _semantic_body(body) != _semantic_body(independent_body):
            issues.append(
                issue(
                    "independent_rule_disagreement",
                    extracted.rule_key,
                    material=False,
                    retry_instruction="Exclude the disputed rule from the alpha release.",
                )
            )
            continue
        if counterpart.inventory_category != extracted.inventory_category:
            issues.append(
                issue(
                    "independent_category_disagreement",
                    extracted.rule_key,
                    material=False,
                    retry_instruction="Exclude the disputed rule from the alpha release.",
                )
            )
            continue
        (
            table_problems,
            normalized_table_cells,
            table_header_span_ids,
            table_footnote_span_ids,
        ) = _table_rule_problems(extracted, body, allowed_span_ids=allowed_span_ids)
        (
            independent_table_problems,
            independent_table_cells,
            independent_table_header_span_ids,
            independent_table_footnote_span_ids,
        ) = _table_rule_problems(counterpart, independent_body, allowed_span_ids=allowed_span_ids)
        if table_problems or independent_table_problems:
            for description in table_problems:
                issues.append(
                    issue(
                        "invalid_rule_table",
                        f"{extracted.rule_key}: {description}",
                        material=False,
                        retry_instruction="Exclude the invalid table rule from the alpha release.",
                    )
                )
            for description in independent_table_problems:
                issues.append(
                    issue(
                        "invalid_independent_rule_table",
                        f"{extracted.rule_key}: {description}",
                        material=False,
                        retry_instruction="Exclude the invalid table rule from the alpha release.",
                    )
                )
            continue
        semantic_problems = rule_semantic_problems(
            body,
            table_cell_values=[value for _selectors, value, _span_id in normalized_table_cells],
        )
        independent_semantic_problems = rule_semantic_problems(
            independent_body,
            table_cell_values=[value for _selectors, value, _span_id in independent_table_cells],
        )
        if semantic_problems or independent_semantic_problems:
            for description in semantic_problems:
                issues.append(
                    issue(
                        "invalid_rule_semantics",
                        f"{extracted.rule_key}: {description}",
                        material=False,
                        retry_instruction="Exclude the invalid rule from the alpha release.",
                    )
                )
            for description in independent_semantic_problems:
                issues.append(
                    issue(
                        "invalid_independent_rule_semantics",
                        f"{extracted.rule_key}: {description}",
                        material=False,
                        retry_instruction="Exclude the invalid rule from the alpha release.",
                    )
                )
            continue
        if _semantic_table_cells(extracted) != _semantic_table_cells(counterpart):
            issues.append(
                issue(
                    "independent_table_disagreement",
                    extracted.rule_key,
                    material=False,
                    retry_instruction="Exclude the disputed table rule from the alpha release.",
                )
            )
            continue
        body_span_ids = body.get("source_span_ids")
        independent_body_span_ids = independent_body.get("source_span_ids")
        if not isinstance(body_span_ids, list) or not all(
            isinstance(item, str) for item in body_span_ids
        ):
            issues.append(
                issue(
                    "invalid_rule_evidence",
                    f"{extracted.rule_key}: source_span_ids must be a string list.",
                    material=False,
                    retry_instruction="Exclude the unsupported rule from the alpha release.",
                )
            )
            continue
        if not isinstance(independent_body_span_ids, list) or not all(
            isinstance(item, str) for item in independent_body_span_ids
        ):
            issues.append(
                issue(
                    "invalid_independent_rule_evidence",
                    f"{extracted.rule_key}: source_span_ids must be a string list.",
                    material=False,
                    retry_instruction="Exclude the unsupported rule from the alpha release.",
                )
            )
            continue
        base_span_ids: set[str] = set(extracted.evidence_span_ids) | {
            str(value) for value in body_span_ids
        }
        table_cell_span_ids = {value[2] for value in normalized_table_cells}
        all_span_ids = (
            base_span_ids | table_header_span_ids | table_footnote_span_ids | table_cell_span_ids
        )
        independent_span_ids = (
            set(counterpart.evidence_span_ids)
            | {str(value) for value in independent_body_span_ids}
            | independent_table_header_span_ids
            | independent_table_footnote_span_ids
            | {cell.evidence_span_id for cell in counterpart.table_cells}
        )
        if not all_span_ids or not all_span_ids.issubset(allowed_span_ids):
            issues.append(
                issue(
                    "invalid_rule_evidence",
                    extracted.rule_key,
                    material=False,
                    retry_instruction="Exclude the unsupported rule from the alpha release.",
                )
            )
            continue
        if not independent_span_ids or not independent_span_ids.issubset(allowed_span_ids):
            issues.append(
                issue(
                    "invalid_independent_rule_evidence",
                    extracted.rule_key,
                    material=False,
                    retry_instruction="Exclude the unsupported rule from the alpha release.",
                )
            )
            continue
        try:
            rule = _get_or_create_policy_rule_revision(
                policy_version=policy_version,
                rule_key=extracted.rule_key,
                rule_type=extracted.rule_type,
                body=body,
            )
        except ValueError as exc:
            issues.append(
                issue(
                    "invalid_rule_lineage",
                    f"{extracted.rule_key}: {exc}",
                    material=False,
                    retry_instruction="Exclude the conflicting rule revision from the alpha release.",
                )
            )
            continue
        evidence_role = _evidence_role(body)
        spans = {str(span.id): span for span in EvidenceSpan.objects.filter(id__in=all_span_ids)}
        for span in spans.values():
            span.verification = "reviewed"
            span.save(update_fields=["verification"])
            if span.page_id:
                DocumentPage.objects.filter(pk=span.page_id).update(review_state="fully_reviewed")
        for span_id in base_span_ids:
            span = spans[span_id]
            PolicyRuleEvidence.objects.get_or_create(
                policy_rule=rule,
                evidence_span=span,
                role=evidence_role,
                defaults={"is_required": True},
            )
        for span_id in table_header_span_ids:
            PolicyRuleEvidence.objects.get_or_create(
                policy_rule=rule,
                evidence_span=spans[span_id],
                role="table_header",
                defaults={"is_required": True},
            )
        for span_id in table_footnote_span_ids:
            PolicyRuleEvidence.objects.get_or_create(
                policy_rule=rule,
                evidence_span=spans[span_id],
                role="footnote",
                defaults={"is_required": True},
            )
        table_conflict = False
        for selectors, value, span_id in normalized_table_cells:
            table_cell, created = PolicyRuleTableCell.objects.get_or_create(
                policy_rule=rule,
                selectors=selectors,
                defaults={"value": value, "evidence_span": spans[span_id]},
            )
            if not created and (
                table_cell.value != value or str(table_cell.evidence_span_id) != span_id
            ):
                table_conflict = True
                issues.append(
                    issue(
                        "immutable_table_cell_conflict",
                        f"{extracted.rule_key}: an existing selector has different content.",
                        material=False,
                        retry_instruction="Exclude the conflicting table rule from the alpha release.",
                    )
                )
                continue
            PolicyRuleEvidence.objects.get_or_create(
                policy_rule=rule,
                evidence_span=spans[span_id],
                role="table_cell",
                defaults={"is_required": True},
            )
        if table_conflict:
            continue
        verified.append(rule)
    extra_independent = set(independent) - seen_keys
    if extra_independent:
        issues.append(
            issue(
                "primary_extraction_missing_rules",
                ", ".join(sorted(extra_independent)),
                material=False,
                retry_instruction="Exclude independently unconfirmed rules from the alpha release.",
            )
        )
    while verified:
        verified_by_key = {item.rule_key: item for item in verified}
        invalid_keys = {
            rule.rule_key
            for rule in verified
            if any(
                dependency not in verified_by_key or dependency == rule.rule_key
                for dependency, _link_type in rule_link_references(rule.body)
            )
        }
        if invalid_keys:
            for rule_key in sorted(invalid_keys):
                issues.append(
                    issue(
                        "invalid_rule_dependency_graph",
                        f"{rule_key}: a required dependency was not independently verified.",
                        material=False,
                        retry_instruction=(
                            "Exclude this dependency-incomplete rule from the alpha release."
                        ),
                    )
                )
            verified = [item for item in verified if item.rule_key not in invalid_keys]
            continue
        graph_problems = rule_graph_problems(
            {item.rule_key: (item.rule_type, item.body) for item in verified}
        )
        cycle_keys = {
            key
            for description in graph_problems
            if description.startswith("executable dependency cycle: ")
            for key in description.removeprefix("executable dependency cycle: ").split(" -> ")
        }
        if cycle_keys:
            for description in graph_problems:
                issues.append(
                    issue(
                        "invalid_rule_dependency_graph",
                        description,
                        material=False,
                        retry_instruction=(
                            "Exclude every rule in the executable dependency cycle."
                        ),
                    )
                )
            verified = [item for item in verified if item.rule_key not in cycle_keys]
            continue
        break
    verified_by_key = {item.rule_key: item for item in verified}
    graph_problems = rule_graph_problems(
        {item.rule_key: (item.rule_type, item.body) for item in verified}
    )
    covered_categories = {extracted_by_key[item.rule_key].inventory_category for item in verified}
    missing_critical = CRITICAL_INVENTORY_CATEGORIES - covered_categories
    coverage = len(covered_categories) / len(INVENTORY_CATEGORIES)
    if missing_critical or coverage < 0.90:
        issues.append(
            issue(
                "rule_inventory_coverage_incomplete",
                f"coverage={coverage:.3f}; missing critical={','.join(sorted(missing_critical))}",
                material=False,
                retry_instruction="Evaluate uncovered categories as unknown.",
            )
        )
    if not verified:
        issues.append(
            issue(
                "verified_rules_missing",
                "Sol and Terra produced no rule that both agreed on and deterministic validation accepted.",
                material=True,
                retry_instruction="Resolve at least one supported rule before publishing this product.",
            )
        )
    if not graph_problems:
        for rule in verified:
            for dependency, link_type in rule_link_references(rule.body):
                target = verified_by_key[dependency]
                PolicyRuleLink.objects.get_or_create(
                    from_policy_rule=rule,
                    to_policy_rule=target,
                    link_type=link_type,
                )
        for rule in verified:
            if rule.review_status != "verified":
                rule.review_status = "verified"
                rule.save(update_fields=["review_status"])
            if rule.supersedes_id is not None:
                PolicyRule.objects.filter(pk=rule.supersedes_id).exclude(
                    review_status="superseded"
                ).update(review_status="superseded")
        # A full-bundle validate run is authoritative over the complete current verified
        # set: any previously-verified rule this run did not reconfirm (dropped, renamed,
        # or failed independent review this pass) must not linger as verified, or the
        # index stage's verified-count reconciliation against this run's rule_ids can
        # never pass again.
        PolicyRule.objects.filter(policy_version=policy_version, review_status="verified").exclude(
            pk__in=[rule.pk for rule in verified]
        ).update(review_status="superseded")
    if graph_problems or not verified:
        transaction.savepoint_rollback(validation_savepoint)
        return {
            "schema_version": 1,
            "rule_prompt_version": RULE_PROMPT_VERSION,
            "rule_review_prompt_version": RULE_REVIEW_PROMPT_VERSION,
            "rule_validator_version": RULE_VALIDATOR_VERSION,
            "policy_version_id": str(policy_version.id),
            "verified_rule_ids": [],
            "inventory_categories": sorted(reviewed_categories),
            "covered_inventory_categories": [],
            "missing_inventory_categories": sorted(INVENTORY_CATEGORIES),
            "coverage": 0.0,
            "issues": issues,
            "indexed_chunks": 0,
        }
    transaction.savepoint_commit(validation_savepoint)
    return {
        "schema_version": 1,
        "rule_prompt_version": RULE_PROMPT_VERSION,
        "rule_review_prompt_version": RULE_REVIEW_PROMPT_VERSION,
        "rule_validator_version": RULE_VALIDATOR_VERSION,
        "policy_version_id": str(policy_version.id),
        "verified_rule_ids": [str(item.id) for item in verified],
        "inventory_categories": sorted(reviewed_categories),
        "covered_inventory_categories": sorted(covered_categories),
        "missing_inventory_categories": sorted(INVENTORY_CATEGORIES - covered_categories),
        "coverage": coverage,
        "critical_inventory_categories": sorted(CRITICAL_INVENTORY_CATEGORIES),
        "issues": issues,
        "index_pending": True,
    }


def run_index(job: ProcessingJob) -> dict[str, Any]:
    policy_version = _policy_version(job)
    validation_job = _ancestor(job, "validate")
    artifact = read_artifact(validation_job)
    if artifact.get("policy_version_id") != str(policy_version.id):
        raise ValueError("Index stage validation artifact belongs to another policy version.")
    if artifact.get("rule_prompt_version") != RULE_PROMPT_VERSION:
        raise ValueError("Index stage received a stale rule-prompt artifact.")
    if artifact.get("rule_review_prompt_version") != RULE_REVIEW_PROMPT_VERSION:
        raise ValueError("Index stage received a stale independent-review artifact.")
    if artifact.get("rule_validator_version") != RULE_VALIDATOR_VERSION:
        raise ValueError("Index stage received a stale semantic-validator artifact.")
    if any(
        isinstance(item, dict) and item.get("material") is True and not item.get("resolved")
        for item in artifact.get("issues", [])
    ):
        raise ValueError("Index stage cannot consume a validation artifact with material issues.")
    raw_rule_ids = artifact.get("verified_rule_ids")
    if (
        not isinstance(raw_rule_ids, list)
        or not raw_rule_ids
        or not all(isinstance(value, str) for value in raw_rule_ids)
        or len(raw_rule_ids) != len(set(raw_rule_ids))
    ):
        raise ValueError("Index stage requires a nonempty unique validated rule set.")
    try:
        rule_ids = [uuid.UUID(value) for value in raw_rule_ids]
    except ValueError as exc:
        raise ValueError("Index stage received an invalid policy-rule identity.") from exc
    verified_count = PolicyRule.objects.filter(
        id__in=rule_ids,
        policy_version=policy_version,
        review_status="verified",
    ).count()
    if verified_count != len(rule_ids):
        raise ValueError("Index stage rule set no longer matches verified policy rules.")
    current_verified_count = PolicyRule.objects.filter(
        policy_version=policy_version,
        review_status="verified",
    ).count()
    if current_verified_count != len(rule_ids):
        raise ValueError("Index stage validation artifact omits current verified policy rules.")
    newly_indexed, indexed, index_version = index_policy_version(policy_version)
    return {
        "schema_version": 1,
        "policy_version_id": str(policy_version.id),
        "validation_job_id": str(validation_job.id),
        "rule_prompt_version": artifact["rule_prompt_version"],
        "rule_review_prompt_version": artifact["rule_review_prompt_version"],
        "rule_validator_version": artifact["rule_validator_version"],
        "verified_rule_ids": raw_rule_ids,
        "index_version": index_version,
        "newly_indexed_chunks": newly_indexed,
        "indexed_chunks": indexed,
        "issues": [],
    }


def index_policy_version(policy_version: PolicyVersion) -> tuple[int, int, str]:
    embedding_ready, reason, qualification = qualified_embedding_status()
    if not embedding_ready or qualification is None:
        raise DependencyUnavailable(reason)
    index_version = policy_index_version(qualification)
    passages = _bundle_passages(policy_version)
    expected: dict[tuple[uuid.UUID, str], dict[str, object]] = {}
    document_by_span: dict[str, uuid.UUID] = {}
    for span in EvidenceSpan.objects.filter(
        id__in=[item["evidence_span_id"] for item in passages]
    ).select_related("source_capture"):
        capture = span.source_capture
        if capture is None or capture.document_version_id is None:
            raise ValueError("A public policy evidence span lost its document identity.")
        document_by_span[str(span.id)] = capture.document_version_id
    for passage in passages:
        text = passage["passage"]
        span_id = passage["evidence_span_id"]
        document_id = document_by_span.get(span_id)
        if document_id is None:
            raise ValueError("An indexed passage lost its exact document identity.")
        digest = hashlib.sha256(text.encode()).hexdigest()
        key = (document_id, digest)
        entry = expected.setdefault(key, {"text": text, "evidence_span_ids": set()})
        if entry["text"] != text:
            raise ValueError("A policy chunk digest resolved to conflicting text.")
        span_ids = entry["evidence_span_ids"]
        assert isinstance(span_ids, set)
        span_ids.add(span_id)
    ordered = sorted(expected.items(), key=lambda item: (str(item[0][0]), item[0][1]))
    existing = {
        (chunk.document_version_id, chunk.chunk_sha256): chunk
        for chunk in PolicySearchChunk.objects.filter(
            document_version_id__in={key[0] for key, _entry in ordered},
            chunk_sha256__in={key[1] for key, _entry in ordered},
            index_version=index_version,
        )
    }
    missing = [(key, entry) for key, entry in ordered if key not in existing]
    new_vectors = embed_texts([str(entry["text"]) for _key, entry in missing]) if missing else []
    vectors = {
        **{key: chunk.embedding for key, chunk in existing.items()},
        **{key: vector for (key, _entry), vector in zip(missing, new_vectors, strict=True)},
    }
    created = 0
    expected_digests: defaultdict[uuid.UUID, set[str]] = defaultdict(set)
    with transaction.atomic():
        for (document_id, digest), entry in ordered:
            vector = vectors[(document_id, digest)]
            text = str(entry["text"])
            raw_span_ids = entry["evidence_span_ids"]
            assert isinstance(raw_span_ids, set)
            span_ids = sorted(str(value) for value in raw_span_ids)
            expected_digests[document_id].add(digest)
            chunk, was_created = PolicySearchChunk.objects.get_or_create(
                document_version_id=document_id,
                index_version=index_version,
                chunk_sha256=digest,
                defaults={
                    "evidence_span_ids": span_ids,
                    "text": text,
                    "lexical_vector": SearchVector(Value(text), config="english"),
                    "embedding": vector,
                },
            )
            if not was_created:
                if chunk.text != text:
                    raise ValueError("An existing policy chunk failed its text digest invariant.")
                if chunk.evidence_span_ids != span_ids:
                    chunk.evidence_span_ids = span_ids
                    chunk.save(update_fields=["evidence_span_ids"])
            created += int(was_created)
        for document_id, digests in expected_digests.items():
            PolicySearchChunk.objects.filter(
                document_version_id=document_id,
                index_version=index_version,
            ).exclude(chunk_sha256__in=digests).delete()
    return created, len(ordered), index_version


STAGE_RUNNERS = {
    "classify": run_classify,
    "read": run_read,
    "ocr": run_ocr,
    "reconcile": run_reconcile,
    "extract": run_extract,
    "independent_review": run_independent_review,
    "validate": run_validate,
    "index": run_index,
}
