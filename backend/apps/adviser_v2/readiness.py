"""Evidence-backed bundle and release gates; counts never imply completion."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from django.conf import settings

from apps.adviser.ai import RelayFailure

from .embedding import policy_index_version, qualified_embedding_status
from .manifest import (
    ALL_DOCUMENT_ROLES,
    POLICY_MEMBERSHIP_ROLE_BY_DOCUMENT_ROLE,
)
from .model_gateway import qualified_route
from .models import (
    DocumentPage,
    EvidenceSpan,
    ModelQualification,
    PolicyRule,
    PolicyRuleEvidence,
    PolicyRuleLink,
    PolicyRuleTableCell,
    PolicySearchChunk,
    PolicyVersion,
    PolicyVersionDocument,
    ProcessingJob,
    SourceCapture,
)
from .pipeline import ADAPTER_VERSION
from .processing.artifacts import read_artifact
from .processing.stages import (
    INVENTORY_CATEGORIES,
    RECONCILIATION_VERSION,
    RULE_PROMPT_VERSION,
    RULE_REVIEW_PROMPT_VERSION,
    RULE_VALIDATOR_VERSION,
    _table_rule_problems,
)
from .role_routes import ROLE_SETTINGS, configured_route
from .rule_validation import (
    rule_graph_problems,
    rule_link_references,
    rule_semantic_problems,
)
from .schemas import (
    ComparisonDraftV1,
    CustomerInterpretationV1,
    ExtractedPolicyRule,
    PolicyRuleExtractionV1,
    PolicyRuleReviewV1,
)

REQUIRED_STAGES = ("classify", "read", "ocr", "reconcile")
VERIFIED_EVIDENCE_STATES = {"text_verified", "visually_verified", "reviewed"}


def _persisted_rule_blockers(rules: list[PolicyRule]) -> list[str]:
    if not rules:
        return []
    blockers: list[str] = []
    rule_ids = [rule.id for rule in rules]
    evidence_by_rule: dict[uuid.UUID, list[PolicyRuleEvidence]] = {rule.id: [] for rule in rules}
    for row in PolicyRuleEvidence.objects.filter(policy_rule_id__in=rule_ids):
        evidence_by_rule[row.policy_rule_id].append(row)
    cells_by_rule: dict[uuid.UUID, list[PolicyRuleTableCell]] = {rule.id: [] for rule in rules}
    for cell in PolicyRuleTableCell.objects.filter(policy_rule_id__in=rule_ids):
        cells_by_rule[cell.policy_rule_id].append(cell)
    rule_by_key: dict[str, PolicyRule] = {}
    for rule in rules:
        if rule.rule_key in rule_by_key:
            blockers.append(f"duplicate_verified_rule_key:{rule.rule_key}")
        rule_by_key[rule.rule_key] = rule
    actual_links = set(
        PolicyRuleLink.objects.filter(
            from_policy_rule_id__in=rule_ids,
            to_policy_rule_id__in=rule_ids,
        ).values_list("from_policy_rule_id", "to_policy_rule_id", "link_type")
    )
    for rule in rules:
        rows = evidence_by_rule[rule.id]
        linked_span_ids = {str(row.evidence_span_id) for row in rows}
        if not any(row.is_required for row in rows):
            blockers.append(f"required_rule_evidence_missing:{rule.rule_key}")
        body_span_ids = rule.body.get("source_span_ids")
        if not isinstance(body_span_ids, list) or not {
            str(value) for value in body_span_ids
        }.issubset(linked_span_ids):
            blockers.append(f"rule_source_evidence_incomplete:{rule.rule_key}")
        cells = cells_by_rule[rule.id]
        footnote_ids = [str(row.evidence_span_id) for row in rows if row.role == "footnote"]
        try:
            extracted = ExtractedPolicyRule.model_validate(
                {
                    "rule_key": rule.rule_key,
                    "rule_type": rule.rule_type,
                    "inventory_category": "readiness",
                    "body": rule.body,
                    "evidence_span_ids": sorted(linked_span_ids),
                    "table_cells": [
                        {
                            "selectors": cell.selectors,
                            "value": cell.value,
                            "evidence_span_id": str(cell.evidence_span_id),
                        }
                        for cell in cells
                    ],
                    "table_footnote_span_ids": footnote_ids,
                }
            )
        except ValueError:
            blockers.append(f"persisted_rule_contract_invalid:{rule.rule_key}")
        else:
            table_problems, _normalized, header_ids, _footnote_ids = _table_rule_problems(
                extracted,
                rule.body,
            )
            blockers.extend(
                f"persisted_rule_table_invalid:{rule.rule_key}:{problem}"
                for problem in table_problems
            )
            required_headers = {
                str(row.evidence_span_id)
                for row in rows
                if row.role == "table_header" and row.is_required
            }
            if required_headers != header_ids:
                blockers.append(f"table_header_evidence_incomplete:{rule.rule_key}")
            required_cells = {
                str(row.evidence_span_id)
                for row in rows
                if row.role == "table_cell" and row.is_required
            }
            expected_cells = {str(cell.evidence_span_id) for cell in cells}
            if required_cells != expected_cells:
                blockers.append(f"table_cell_evidence_incomplete:{rule.rule_key}")
            if any(row.role == "footnote" and not row.is_required for row in rows):
                blockers.append(f"table_footnote_not_required:{rule.rule_key}")
            semantic_problems = rule_semantic_problems(
                rule.body,
                table_cell_values=[cell.value for cell in cells],
            )
            blockers.extend(
                f"persisted_rule_semantics_invalid:{rule.rule_key}:{problem}"
                for problem in semantic_problems
            )
        for target_key, link_type in rule_link_references(rule.body):
            target = rule_by_key.get(target_key)
            if target is None or (rule.id, target.id, link_type) not in actual_links:
                blockers.append(f"rule_dependency_missing:{rule.rule_key}:{target_key}:{link_type}")
        if PolicyRule.objects.filter(supersedes_id=rule.id).exists():
            blockers.append(f"validated_rule_is_superseded:{rule.rule_key}")
    blockers.extend(
        f"persisted_rule_graph_invalid:{problem}"
        for problem in rule_graph_problems(
            {rule.rule_key: (rule.rule_type, rule.body) for rule in rules}
        )
    )
    return blockers


def role_inventory_blockers(product_entry: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    raw_decisions = product_entry.get("role_decisions")
    raw_documents = product_entry.get("documents")
    if not isinstance(raw_decisions, list):
        return ["document_role_decisions_missing"]
    documents = [item for item in raw_documents or [] if isinstance(item, dict)]
    decisions: dict[str, dict[str, Any]] = {}
    for item in raw_decisions:
        if not isinstance(item, dict) or not isinstance(item.get("role"), str):
            blockers.append("invalid_document_role_decision")
            continue
        role = str(item["role"])
        if role in decisions:
            blockers.append(f"duplicate_document_role_decision:{role}")
        decisions[role] = item
    missing = ALL_DOCUMENT_ROLES - decisions.keys()
    unknown = decisions.keys() - ALL_DOCUMENT_ROLES
    blockers.extend(f"document_role_decision_missing:{role}" for role in sorted(missing))
    blockers.extend(f"document_role_decision_unknown:{role}" for role in sorted(unknown))
    for role in sorted(ALL_DOCUMENT_ROLES & decisions.keys()):
        decision = decisions[role]
        applicability = decision.get("applicability")
        if applicability not in {"applicable", "conditional", "not_applicable"}:
            blockers.append(f"document_role_applicability_invalid:{role}")
            continue
        role_documents = [item for item in documents if item.get("role") == role]
        if applicability == "not_applicable" and role_documents:
            blockers.append(f"not_applicable_role_has_documents:{role}")
        if applicability != "not_applicable" and not role_documents:
            blockers.append(f"applicable_role_has_no_documents:{role}")
        for document in role_documents:
            if document.get("expected_applicability") != applicability:
                blockers.append(
                    f"document_role_applicability_mismatch:{document.get('document_key', role)}"
                )
            if applicability != "not_applicable" and document.get("required") is not True:
                blockers.append(
                    f"applicable_document_not_required:{document.get('document_key', role)}"
                )
    unknown_document_roles = {
        str(item.get("role")) for item in documents if item.get("role") not in ALL_DOCUMENT_ROLES
    }
    blockers.extend(
        f"captured_document_role_unknown:{role}" for role in sorted(unknown_document_roles)
    )
    return blockers


def load_captured_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Captured manifest is unreadable: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("Captured manifest must be a schema-version 1 object.")
    claimed = value.get("manifest_sha256")
    unsigned = dict(value)
    unsigned.pop("manifest_sha256", None)
    from .manifest import manifest_sha256

    if not isinstance(claimed, str) or manifest_sha256(unsigned) != claimed:
        raise ValueError("Captured manifest integrity hash is invalid.")
    products = value.get("products")
    if not isinstance(products, list) or len(products) != 5:
        raise ValueError("Captured manifest must contain exactly five products.")
    return value


def _latest_job(capture_id: uuid.UUID, stage: str) -> ProcessingJob | None:
    return (
        ProcessingJob.objects.filter(
            source_capture_id=capture_id,
            adapter_version=ADAPTER_VERSION,
            stage=stage,
        )
        .order_by("-created_at", "-attempt_number")
        .first()
    )


def _document_identity_blockers(
    capture: SourceCapture,
    *,
    uin: str,
    require_observed: bool,
) -> list[str]:
    if capture.document_version is None:
        return ["document_identity_missing"]
    matching = [
        item
        for item in capture.document_version.identifiers
        if isinstance(item, dict) and item.get("value") == uin
    ]
    if len(matching) != 1:
        return ["document_exact_uin_missing"]
    identifier = matching[0]
    if identifier.get("kind") == "expected_uin" and identifier.get("status") == "unresolved":
        return ["authoritative_uin_not_observed"] if require_observed else []
    if identifier.get("kind") != "uin" or identifier.get("status") != "observed":
        return ["document_uin_state_invalid"]
    span_id = identifier.get("span_id")
    if not isinstance(span_id, str):
        return ["document_uin_evidence_missing"]
    try:
        span = EvidenceSpan.objects.get(
            pk=span_id,
            source_capture=capture,
            section_label="manifest identity",
        )
    except (ValueError, EvidenceSpan.DoesNotExist, InvalidTag):
        return ["document_uin_evidence_missing"]
    if uin.casefold() not in span.quote.casefold():
        return ["document_uin_evidence_mismatch"]
    if span.verification not in VERIFIED_EVIDENCE_STATES:
        return ["document_uin_evidence_not_verified"]
    return []


def _model_gate() -> list[str]:
    requirements = (
        ("fact_interpretation", CustomerInterpretationV1),
        ("policy_extraction", PolicyRuleExtractionV1),
        ("policy_review", PolicyRuleReviewV1),
        ("comparison_answer", ComparisonDraftV1),
    )
    blockers: list[str] = []
    for schema_name, output_type in requirements:
        # Each role is checked against the route the operator configured; no fallback route.
        label = getattr(settings, ROLE_SETTINGS[schema_name][0])
        try:
            route = configured_route(schema_name)
            label = route.requested_model
            qualified_route(route, schema_name, output_type)
        except RelayFailure as exc:
            blockers.append(f"model:{label}:{schema_name}:{exc.code}")
    return blockers


def validate_bundle(
    product_entry: dict[str, Any], *, include_runtime_gates: bool = True
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    try:
        policy_version_id = uuid.UUID(str(product_entry["policy_version_id"]))
        policy_version = PolicyVersion.objects.select_related("product__insurer").get(
            pk=policy_version_id
        )
    except (KeyError, ValueError, PolicyVersion.DoesNotExist):
        return {
            "policy_version_id": product_entry.get("policy_version_id"),
            "uin": product_entry.get("uin"),
            "ready": False,
            "blockers": ["policy_version_missing"],
        }
    if policy_version.uin != product_entry.get("uin"):
        blockers.append("uin_mismatch")
    if policy_version.product.name != product_entry.get("name"):
        blockers.append("product_identity_mismatch")
    blockers.extend(role_inventory_blockers(product_entry))
    documents = product_entry.get("documents")
    if not isinstance(documents, list) or not documents:
        blockers.append("captured_document_inventory_missing")
        documents = []
    memberships = {
        str(item.document_version_id): item
        for item in PolicyVersionDocument.objects.filter(
            policy_version=policy_version
        ).select_related("document_version")
    }
    manifest_document_ids = {
        str(item.get("document_version_id")) for item in documents if isinstance(item, dict)
    }
    if set(memberships) != manifest_document_ids:
        blockers.append("policy_bundle_membership_mismatch")
    capture_ids: list[uuid.UUID] = []
    captured_hashes: list[str] = []
    for document in documents:
        if not isinstance(document, dict):
            blockers.append("invalid_captured_document_entry")
            continue
        try:
            capture = SourceCapture.objects.select_related("original_file", "document_version").get(
                pk=uuid.UUID(str(document["capture_id"])), status="captured"
            )
        except (KeyError, ValueError, SourceCapture.DoesNotExist):
            blockers.append(f"capture_missing:{document.get('document_key', 'unknown')}")
            continue
        capture_ids.append(capture.id)
        if capture.original_file is None:
            blockers.append(f"original_missing:{document.get('document_key')}")
            continue
        captured_hashes.append(capture.original_file.sha256)
        if capture.original_file.sha256 != document.get(
            "sha256"
        ) or capture.original_file.byte_size != document.get("byte_count"):
            blockers.append(f"capture_integrity_mismatch:{document.get('document_key')}")
        if capture.document_version_id != uuid.UUID(str(document["document_version_id"])):
            blockers.append(f"capture_version_mismatch:{document.get('document_key')}")
        membership = memberships.get(str(capture.document_version_id))
        document_role = document.get("role")
        expected_membership_role = POLICY_MEMBERSHIP_ROLE_BY_DOCUMENT_ROLE.get(str(document_role))
        if (
            membership is None
            or expected_membership_role is None
            or membership.role != expected_membership_role
        ):
            blockers.append(f"membership_role_mismatch:{document.get('document_key')}")
        elif membership.required_for_policy is not (document.get("required") is True):
            blockers.append(f"membership_required_mismatch:{document.get('document_key')}")
        for identity_blocker in _document_identity_blockers(
            capture,
            uin=str(product_entry.get("uin") or ""),
            require_observed=document_role in {"base_wording", "customer_information_sheet"},
        ):
            blockers.append(f"{identity_blocker}:{document.get('document_key')}")
        if capture.document_version and capture.document_version.review_status != "verified":
            blockers.append(f"document_not_verified:{document.get('document_key')}")
        verified_policy_evidence = EvidenceSpan.objects.filter(
            source_capture=capture,
            verification__in=VERIFIED_EVIDENCE_STATES,
        ).exclude(section_label="manifest identity")
        for stage in REQUIRED_STAGES:
            latest = _latest_job(capture.id, stage)
            if latest is None or latest.state != "succeeded":
                state = latest.state if latest else "missing"
                issue_code = f"stage:{document.get('document_key')}:{stage}:{state}"
                if stage == "reconcile" and verified_policy_evidence.exists():
                    warnings.append(issue_code)
                else:
                    blockers.append(issue_code)
        reconciliation = (
            ProcessingJob.objects.filter(
                source_capture_id=capture.id,
                adapter_version=ADAPTER_VERSION,
                stage="reconcile",
                state="succeeded",
            )
            .order_by("-created_at", "-attempt_number")
            .first()
        )
        if reconciliation is not None:
            try:
                reconciliation_result = read_artifact(reconciliation)
            except (InvalidTag, OSError, ValueError):
                warnings.append(
                    f"reconciliation_artifact_unreadable:{document.get('document_key')}"
                )
            else:
                if reconciliation_result.get("reconciliation_version") != RECONCILIATION_VERSION:
                    warnings.append(f"reconciliation_version_stale:{document.get('document_key')}")
                active_span_ids = {
                    str(item.get("id"))
                    for item in reconciliation_result.get("evidence_spans", [])
                    if isinstance(item, dict) and item.get("id")
                }
                active_spans = EvidenceSpan.objects.filter(
                    id__in=active_span_ids,
                    source_capture=capture,
                )
                if not active_span_ids or active_spans.count() != len(active_span_ids):
                    warnings.append(f"reconciled_evidence_missing:{document.get('document_key')}")
                elif active_spans.exclude(
                    verification__in=["text_verified", "visually_verified", "reviewed"]
                ).exists():
                    warnings.append(
                        f"reconciled_evidence_not_verified:{document.get('document_key')}"
                    )
        if not verified_policy_evidence.exists():
            blockers.append(f"verified_policy_evidence_missing:{document.get('document_key')}")
        if (
            capture.original_file.media_type == "application/pdf"
            and not DocumentPage.objects.filter(original_file=capture.original_file).exists()
        ):
            blockers.append(f"pages_missing:{document.get('document_key')}")
    validation_jobs = ProcessingJob.objects.filter(
        source_capture_id__in=capture_ids,
        adapter_version=ADAPTER_VERSION,
        stage="validate",
        state="succeeded",
    ).order_by("-created_at")
    validation = validation_jobs.first()
    index_artifact: dict[str, Any] | None = None
    coverage = 0.0
    covered: set[str] = set()
    validated_rule_ids: set[uuid.UUID] = set()
    if validation is None:
        blockers.append("validated_rule_inventory_missing")
    else:
        try:
            artifact = read_artifact(validation)
        except (InvalidTag, OSError, ValueError):
            blockers.append("validated_rule_inventory_unreadable")
        else:
            if artifact.get("policy_version_id") != str(policy_version.id):
                blockers.append("validated_rule_policy_version_mismatch")
            if artifact.get("rule_prompt_version") != RULE_PROMPT_VERSION:
                blockers.append("validated_rule_prompt_version_stale")
            if artifact.get("rule_review_prompt_version") != RULE_REVIEW_PROMPT_VERSION:
                blockers.append("validated_rule_review_prompt_version_stale")
            if artifact.get("rule_validator_version") != RULE_VALIDATOR_VERSION:
                blockers.append("validated_rule_validator_version_stale")
            coverage = float(artifact.get("coverage", 0))
            covered = set(artifact.get("covered_inventory_categories", []))
            raw_rule_ids = artifact.get("verified_rule_ids")
            if not isinstance(raw_rule_ids, list) or not raw_rule_ids:
                blockers.append("validated_rule_ids_missing")
            else:
                try:
                    validated_rule_ids = {uuid.UUID(str(value)) for value in raw_rule_ids}
                except ValueError:
                    blockers.append("validated_rule_ids_invalid")
                if len(validated_rule_ids) != len(raw_rule_ids):
                    blockers.append("validated_rule_ids_duplicated")
        index_job = (
            ProcessingJob.objects.filter(
                source_capture_id__in=capture_ids,
                adapter_version=ADAPTER_VERSION,
                stage="index",
                parent_job=validation,
            )
            .order_by("-attempt_number", "-created_at")
            .first()
        )
        if index_job is None:
            blockers.append("policy_index_stage_missing")
        elif index_job.state != "succeeded":
            blockers.append(f"policy_index_stage_{index_job.state}")
        else:
            try:
                index_artifact = read_artifact(index_job)
            except (InvalidTag, OSError, ValueError):
                blockers.append("policy_index_artifact_unreadable")
            else:
                if index_artifact.get("policy_version_id") != str(policy_version.id):
                    blockers.append("policy_index_version_mismatch")
                if index_artifact.get("validation_job_id") != str(validation.id):
                    blockers.append("policy_index_validation_mismatch")
                if index_artifact.get("rule_prompt_version") != RULE_PROMPT_VERSION:
                    blockers.append("policy_index_prompt_version_stale")
                if index_artifact.get("rule_review_prompt_version") != RULE_REVIEW_PROMPT_VERSION:
                    blockers.append("policy_index_review_prompt_version_stale")
                if index_artifact.get("rule_validator_version") != RULE_VALIDATOR_VERSION:
                    blockers.append("policy_index_validator_version_stale")
                indexed_rule_ids = index_artifact.get("verified_rule_ids")
                if not isinstance(indexed_rule_ids, list) or {
                    str(value) for value in indexed_rule_ids
                } != {str(value) for value in validated_rule_ids}:
                    blockers.append("policy_index_rule_set_mismatch")
                if (
                    not isinstance(index_artifact.get("indexed_chunks"), int)
                    or int(index_artifact["indexed_chunks"]) <= 0
                ):
                    blockers.append("policy_index_chunk_count_invalid")
    current_verified_rule_ids = set(
        PolicyRule.objects.filter(
            policy_version=policy_version,
            review_status="verified",
        ).values_list("id", flat=True)
    )
    if current_verified_rule_ids != validated_rule_ids:
        blockers.append("validated_rule_set_not_current")
    rules = list(
        PolicyRule.objects.filter(
            id__in=validated_rule_ids,
            policy_version=policy_version,
            review_status="verified",
        ).order_by("rule_key", "id")
    )
    if len(rules) != len(validated_rule_ids):
        blockers.append("validated_rule_set_mismatch")
    if not rules:
        blockers.append("verified_rules_missing")
    bad_evidence = PolicyRuleEvidence.objects.filter(policy_rule__in=rules).exclude(
        evidence_span__verification__in=["text_verified", "visually_verified", "reviewed"]
    )
    if bad_evidence.exists():
        blockers.append("rule_evidence_not_verified")
    blockers.extend(_persisted_rule_blockers(rules))
    embedding_ok, embedding_reason, qualification = qualified_embedding_status()
    current_index_version = (
        policy_index_version(qualification) if embedding_ok and qualification is not None else None
    )
    if (
        index_artifact is not None
        and current_index_version is not None
        and index_artifact.get("index_version") != current_index_version
    ):
        blockers.append("policy_index_embedding_version_stale")
    indexed_chunks = (
        list(
            PolicySearchChunk.objects.filter(
                document_version_id__in=manifest_document_ids,
                index_version=current_index_version,
            ).values_list("document_version_id", "evidence_span_ids")
        )
        if current_index_version is not None
        else []
    )
    indexed_documents = {document_id for document_id, _span_ids in indexed_chunks}
    indexed_span_ids = {
        str(span_id) for _document_id, span_ids in indexed_chunks for span_id in span_ids
    }
    evidence = EvidenceSpan.objects.filter(
        source_capture_id__in=capture_ids,
        verification__in=VERIFIED_EVIDENCE_STATES,
    )
    evidence_documents = set(evidence.values_list("source_capture__document_version_id", flat=True))
    expected_span_ids = {str(item) for item in evidence.values_list("id", flat=True)}
    if evidence_documents - indexed_documents:
        blockers.append("policy_chunks_missing")
    if expected_span_ids - indexed_span_ids:
        blockers.append("policy_chunk_evidence_incomplete")
    if (
        index_artifact is not None
        and current_index_version is not None
        and index_artifact.get("indexed_chunks") != len(indexed_chunks)
    ):
        blockers.append("policy_index_chunk_count_mismatch")
    if include_runtime_gates:
        blockers.extend(_model_gate())
        if not embedding_ok:
            blockers.append(f"embedding:{embedding_reason}")
    return {
        "policy_version_id": str(policy_version.id),
        "product": policy_version.product.name,
        "insurer": policy_version.product.insurer.name,
        "uin": policy_version.uin,
        "ready": not blockers,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "document_count": len(documents),
        "document_sha256": sorted(captured_hashes),
        "verified_rule_count": len(rules),
        "verified_rule_ids": [str(rule.id) for rule in rules],
        "covered_inventory_categories": sorted(covered),
        "missing_inventory_categories": sorted(INVENTORY_CATEGORIES - covered),
        "inventory_category_count": len(INVENTORY_CATEGORIES),
        "coverage": coverage,
    }


def validate_five_product_manifest(path: Path) -> dict[str, Any]:
    manifest = load_captured_manifest(path)
    products = [validate_bundle(item) for item in manifest["products"]]
    product_ids = {item["policy_version_id"] for item in products}
    uins = {item["uin"] for item in products}
    blockers = [
        blocker
        for index, product in enumerate(products)
        for blocker in [f"product-{index + 1}:{item}" for item in product["blockers"]]
    ]
    warnings = [
        warning
        for index, product in enumerate(products)
        for warning in [f"product-{index + 1}:{item}" for item in product.get("warnings", [])]
    ]
    if len(product_ids) != 5:
        blockers.append("release_policy_versions_not_distinct")
    if len(uins) != 5:
        blockers.append("release_uins_not_distinct")
    return {
        "manifest_sha256": manifest["manifest_sha256"],
        "ready": not blockers and all(item["ready"] for item in products),
        "blockers": blockers,
        "warnings": warnings,
        "products": products,
        "model_qualification_count": ModelQualification.objects.filter(result="passed").count(),
    }


def find_captured_manifest(manifest_sha256: str) -> Path | None:
    root = Path(settings.COVERGUIDE_MANIFEST_ROOT).resolve()
    if not root.is_dir():
        return None
    for path in sorted(root.glob("*-captured.json")):
        try:
            if load_captured_manifest(path).get("manifest_sha256") == manifest_sha256:
                return path
        except ValueError:
            continue
    return None
