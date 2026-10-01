"""Release gates and immutable membership for independently reviewed source facts."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .evidence_retrieval import RAW_INDEX_VERSION, index_raw_chunks, plan_chunks
from .models import EvidenceSpan, KnowledgeReleaseFact, PolicyRule, ProcessingJob
from .processing.artifacts import read_artifact
from .processing.cited_facts import (
    FACT_PROTOCOL,
    carrier_fact,
    fact_problems,
    review_disposition,
)
from .processing.criterion_evidence import CRITERIA, PROGRESS_KEY
from .processing.manifest_v2 import raw_bundle_passages, validate_raw_quote
from .schemas import PolicyRuleExtractionV1, PolicyRuleReviewV1

FACT_RELEASE_VERSION = "prepared-source-facts/1"


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def verify_fact_artifact(version, job):
    artifact = read_artifact(job)
    if (
        job.state != "succeeded"
        or job.stage != "validate"
        or artifact.get("manifest_processing_version") != FACT_PROTOCOL
    ):
        raise ValueError("A succeeded cited-fact validation is required.")
    if artifact.get("policy_version_id") != str(version.id):
        raise ValueError("Fact policy-version identity differs.")
    rows = artifact.get("criteria", [])
    if len(rows) != 13 or {r["criterion"] for r in rows} != {c.key for c in CRITERIA}:
        raise ValueError("The release must account for all 13 criteria exactly once.")
    pages = raw_bundle_passages(version, include_prospectus=True)
    by_id = {p["evidence_span_id"]: p for p in pages}
    executable_ids = set()
    for criterion in CRITERIA:
        row = next(r for r in rows if r["criterion"] == criterion.key)
        state = artifact[PROGRESS_KEY]["criteria"][criterion.key]
        result = PolicyRuleExtractionV1.model_validate(state["result"])
        problems = fact_problems(str(version.id), criterion, result, pages)
        problems.extend(result.material_issues)
        if row["status"] != "supported" or row["unknown_reasons"] or not row["citations"]:
            problems.append("Cited fact lacks complete source support.")
        if state.get("reused_validation_id"):
            if row["rule_status"] != "executable":
                problems.append("Retained executable fact identity differs.")
            verified = PolicyRule.objects.filter(
                pk__in=row["rule_ids"], policy_version=version, review_status="verified"
            )
            if not row["rule_ids"] or verified.count() != len(row["rule_ids"]):
                problems.append("Retained executable fact has an unverified rule.")
            executable_ids.update(row["rule_ids"])
        elif not state.get("review_complete") or not state.get("review"):
            problems.append("Independent fact review is missing.")
        else:
            reviewed = PolicyRuleExtractionV1.model_validate(
                state.get("reviewed_result", state["result"])
            )
            problems.extend(
                review_disposition(
                    PolicyRuleReviewV1.model_validate(state["review"]), reviewed, criterion
                )[0]
            )
        fact = carrier_fact(result.rules[0])
        expected_value = " ".join([fact.value, *(s.text for s in fact.secondary_statements)])
        if row["value"] != expected_value or len(row["citations"]) != len(fact.citations):
            problems.append("Published value or quote count differs from the validated candidate.")
        expected_conditions = [
            c.model_dump()
            for c in [
                *fact.conditions,
                *(c for secondary in fact.secondary_statements for c in secondary.conditions),
            ]
        ]
        if (
            row["conditions"] != expected_conditions
            or row["value_kind"] != fact.value_kind
            or row["quantities"] != [q.model_dump() for q in fact.quantities]
            or row.get("table_regions", []) != [r.model_dump() for r in fact.table_regions]
        ):
            problems.append(
                "Published conditions, quantities or table association differ from validation."
            )
        for cited, clause in zip(row["citations"], fact.citations, strict=True):
            span = EvidenceSpan.objects.select_related("page__original_file").get(
                pk=cited["evidence_span_id"]
            )
            parent = span.context["span_ids"][0]
            if parent != clause.page_span_id or parent not in by_id or cited["quote"] != span.quote:
                problems.append("Fact citation lies outside its exact applicable bundle.")
                continue
            page = by_id[parent]
            # The approved raw anchor remains authoritative. Whitespace-only
            # matching can add an earlier occurrence after a matcher revision;
            # it must not move an already reviewed clause to that occurrence.
            if (
                "".join(span.quote.split()) != "".join(clause.quote.split())
                or cited["page"] != page["physical_page"]
                or cited["document_version_id"] != page["document_version_id"]
                or cited["document_key"] != page["document_key"]
                or cited["locator"] != span.locator
                or cited["context"] != span.context
            ):
                problems.append(
                    "Published clause, page, offsets or highlight geometry differ from validation."
                )
            validate_raw_quote(
                span,
                {
                    "text": page["passage"],
                    "page_number": page["physical_page"],
                    "document_char_start": page["document_char_start"],
                },
                blob_sha256=page["document_sha256"],
            )
        if problems:
            raise ValueError(f"{criterion.key}: " + "; ".join(problems))
    from .readiness import _persisted_rule_blockers

    rule_problems = _persisted_rule_blockers(list(PolicyRule.objects.filter(pk__in=executable_ids)))
    if rule_problems:
        raise ValueError("; ".join(rule_problems))
    return artifact, sorted(executable_ids)


def run_fact_index(job):
    from .processing.stages import _policy_version

    version = _policy_version(job)
    _artifact, rules = verify_fact_artifact(version, job.parent_job)
    chunks = plan_chunks(str(version.id))
    index_raw_chunks(chunks)
    return {
        "schema_version": 1,
        "policy_version_id": str(version.id),
        "validation_job_id": str(job.parent_job_id),
        "validation_sha256": job.parent_job.result_storage_sha256,
        "fact_release_version": FACT_RELEASE_VERSION,
        "index_version": RAW_INDEX_VERSION,
        "indexed_chunks": len(chunks),
        "verified_rule_ids": rules,
        "issues": [],
    }


def fact_product_report(version, job, blockers, warnings, *, runtime):
    from .models import PolicySearchChunk
    from .readiness import INVENTORY_CATEGORIES, _model_gate

    rules = []
    try:
        _artifact, rules = verify_fact_artifact(version, job)
        index = (
            ProcessingJob.objects.filter(stage="index", parent_job=job)
            .order_by("-created_at")
            .first()
        )
        if index is None or index.state != "succeeded":
            raise ValueError("Prepared-fact raw index stage is missing or incomplete.")
        artifact = read_artifact(index)
        chunks = plan_chunks(str(version.id))
        if (
            artifact.get("validation_sha256") != job.result_storage_sha256
            or artifact.get("index_version") != RAW_INDEX_VERSION
            or artifact.get("indexed_chunks") != len(chunks)
        ):
            raise ValueError("Prepared index identity or coverage differs.")
        stored = {
            str(c.id): c
            for c in PolicySearchChunk.objects.filter(
                id__in=[c.id for c in chunks], index_version=RAW_INDEX_VERSION
            )
        }
        for chunk in chunks:
            row = stored.get(chunk.id)
            if (
                row is None
                or row.text != chunk.text
                or row.evidence_span_ids != chunk.evidence_span_ids
            ):
                raise ValueError("Raw index does not preserve every original text chunk and page.")
    except (ValueError, KeyError, OSError) as exc:
        blockers.append("prepared_facts:" + str(exc))
    if runtime:
        blockers.extend(_model_gate())
    covered = {c.category for c in CRITERIA}
    return {
        "policy_version_id": str(version.id),
        "product": version.product.name,
        "insurer": version.product.insurer.name,
        "uin": version.uin,
        "ready": not blockers,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "verified_rule_ids": rules,
        "verified_rule_count": len(rules),
        "validation_job_id": str(job.id),
        "validation_sha256": job.result_storage_sha256,
        "fact_release_version": FACT_RELEASE_VERSION,
        "supported_fact_count": 13,
        "covered_inventory_categories": sorted(covered),
        "missing_inventory_categories": sorted(INVENTORY_CATEGORIES - covered),
        "inventory_category_count": len(INVENTORY_CATEGORIES),
        "coverage": len(covered) / len(INVENTORY_CATEGORIES),
    }


def facts_for_release(release) -> dict[str, list[dict[str, Any]]]:
    facts: dict[str, list[dict[str, Any]]] = {}
    for member in KnowledgeReleaseFact.objects.filter(knowledge_release=release).order_by(
        "criterion"
    ):
        if member.fact_sha256 != digest(member.fact):
            raise ValueError("Published fact snapshot failed its hash check.")
        facts.setdefault(str(member.policy_version_id), []).append(member.fact)
    order = {c.key: i for i, c in enumerate(CRITERIA)}
    return {key: sorted(rows, key=lambda f: order[f["criterion"]]) for key, rows in facts.items()}


def display_fact(fact):
    spans = {
        str(s.id): s
        for s in EvidenceSpan.objects.filter(
            pk__in=[c["evidence_span_id"] for c in fact["citations"]]
        )
    }
    return {
        key: fact[key]
        for key in ("criterion", "status", "value", "conditions", "rule_status", "unknown_reasons")
    } | {
        "citations": [
            {
                **c,
                "id": c["evidence_span_id"],
                "policy_rule_id": None,
                "role": "supports",
                "section_label": spans[c["evidence_span_id"]].section_label,
            }
            for c in fact["citations"]
        ]
    }


def prepare_fact_indexes(manifest_path):
    from .pipeline import enqueue_stage, process_job
    from .readiness import load_captured_manifest

    manifest = load_captured_manifest(manifest_path)
    if manifest["schema_version"] != 2:
        return
    for product in manifest["products"]:
        base = next(d for d in product["documents"] if d["role"] == "base_wording")
        validation = (
            ProcessingJob.objects.filter(source_capture_id=base["capture_id"], stage="validate")
            .order_by("-created_at")
            .first()
        )
        if validation is None or validation.state != "succeeded":
            raise ValueError("Every product needs a completed validation before indexing.")
        if read_artifact(validation).get("manifest_processing_version") != FACT_PROTOCOL:
            continue
        job = enqueue_stage(
            stage="index", source_capture=validation.source_capture, parent_job=validation
        )
        if job.state == "queued":
            process_job(job.id)
        job.refresh_from_db()
        if job.state != "succeeded":
            raise ValueError("Prepared-fact raw indexing failed: " + str(job.issues))
