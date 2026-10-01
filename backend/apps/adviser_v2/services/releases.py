"""Build and atomically select a normal or restricted demo knowledge release."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from django.db import connection, transaction
from django.db.models import Max
from django.utils import timezone

from ..models import (
    KnowledgeChannel,
    KnowledgeRelease,
    KnowledgeReleaseFact,
    KnowledgeReleaseRule,
    Outbox,
    PolicyRule,
    PolicyVersion,
    ProcessingJob,
)
from ..readiness import (
    find_captured_manifest,
    load_captured_manifest,
    validate_five_product_manifest,
)
from ..release_scope import (
    FIVE_PRODUCT_COUNT,
    STANDARD_RELEASE_LABEL,
    THREE_PRODUCT_DEMO_COUNT,
    THREE_PRODUCT_DEMO_LABEL,
    comparison_product_count,
)


def _release_report(
    manifest: dict[str, Any],
    full_report: dict[str, Any],
    requested_count: int,
) -> dict[str, Any]:
    if manifest.get("schema_version") == 2:
        if requested_count != THREE_PRODUCT_DEMO_COUNT:
            raise ValueError("A three-product manifest requires the explicit three-product demo.")
        return full_report
    if requested_count == FIVE_PRODUCT_COUNT:
        if len(manifest["products"]) != FIVE_PRODUCT_COUNT:
            raise ValueError("A three-product manifest requires the explicit three-product demo.")
        return full_report
    if requested_count != THREE_PRODUCT_DEMO_COUNT:
        raise ValueError("Only five-product releases or the three-product demo are supported.")
    selected_manifest = manifest["products"][:THREE_PRODUCT_DEMO_COUNT]
    selected_ids = [str(item["policy_version_id"]) for item in selected_manifest]
    if len(set(selected_ids)) != THREE_PRODUCT_DEMO_COUNT:
        raise ValueError("The three-product demo requires distinct policy versions.")
    reports_by_id = {
        str(item.get("policy_version_id")): item for item in full_report.get("products", [])
    }
    selected_products = [reports_by_id.get(policy_id) for policy_id in selected_ids]
    if any(item is None for item in selected_products):
        raise ValueError("The three-product demo does not resolve to its manifest prefix.")
    products = [item for item in selected_products if item is not None]
    blockers = [
        f"product-{index}:{blocker}"
        for index, product in enumerate(products, start=1)
        for blocker in product.get("blockers", [])
    ]
    warnings = [
        f"product-{index}:{warning}"
        for index, product in enumerate(products, start=1)
        for warning in product.get("warnings", [])
    ]
    return {
        **full_report,
        "ready": not blockers and all(product.get("ready") is True for product in products),
        "blockers": blockers,
        "warnings": warnings,
        "products": products,
    }


@transaction.atomic
def build_release(
    manifest_path: Path,
    *,
    comparison_product_count: int = FIVE_PRODUCT_COUNT,
) -> tuple[KnowledgeRelease, dict[str, Any]]:
    manifest = load_captured_manifest(manifest_path)
    report = _release_report(
        manifest,
        validate_five_product_manifest(manifest_path),
        comparison_product_count,
    )
    release_label = (
        THREE_PRODUCT_DEMO_LABEL
        if comparison_product_count == THREE_PRODUCT_DEMO_COUNT
        else STANDARD_RELEASE_LABEL
    )
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(284651982)")
    release = (
        KnowledgeRelease.objects.select_for_update()
        .filter(
            manifest_sha256=manifest["manifest_sha256"],
            release_label=release_label,
        )
        .exclude(state="retired")
        .order_by("-release_number")
        .first()
    )
    policy_version_ids = [item["policy_version_id"] for item in report["products"]]
    validated_rule_ids = [
        rule_id
        for product in report["products"]
        for rule_id in product.get("verified_rule_ids", [])
    ]
    rules = PolicyRule.objects.filter(
        id__in=validated_rule_ids,
        policy_version_id__in=policy_version_ids,
        review_status="verified",
    ).order_by("policy_version_id", "rule_key", "id")
    unresolved = list(report["blockers"])
    readiness: dict[str, Any] = {
        "label": release_label,
        "incomplete_comparison": True,
        "demo_subset": comparison_product_count == THREE_PRODUCT_DEMO_COUNT,
        "catalogue_product_count": len(manifest["products"]),
        "comparison_product_count": comparison_product_count,
        "products": [
            {
                "policy_version_id": product["policy_version_id"],
                "covered_inventory_categories": product.get("covered_inventory_categories", []),
                "missing_inventory_categories": product.get("missing_inventory_categories", []),
                "coverage": product.get("coverage", 0.0),
                "warnings": product.get("warnings", []),
            }
            for product in report["products"]
        ],
    }
    from ..prepared_facts import FACT_RELEASE_VERSION, digest, verify_fact_artifact
    prepared = all(p.get('fact_release_version') == FACT_RELEASE_VERSION for p in report['products'])
    if prepared:
        readiness['fact_release_version'] = FACT_RELEASE_VERSION
    partial = any(product["missing_inventory_categories"] for product in readiness["products"])
    scope = {
        "intent_kinds": ["product_comparison", "coverage_question"],
        "insurer_ids": sorted(
            {
                str(item)
                for item in PolicyVersion.objects.filter(id__in=policy_version_ids).values_list(
                    "product__insurer_id", flat=True
                )
            }
        ),
        "rule_keys": list(rules.values_list("rule_key", flat=True)),
        "state": "conditional"
        if report["ready"] and partial
        else ("supported" if report["ready"] else "blocked"),
        "unresolved": unresolved,
    }
    if release is None:
        release_number = (
            KnowledgeRelease.objects.aggregate(value=Max("release_number"))["value"] or 0
        ) + 1
        current = (
            KnowledgeChannel.objects.select_related("current_release").filter(name="live").first()
        )
        release = KnowledgeRelease.objects.create(
            release_number=release_number,
            state="ready" if report["ready"] else "blocked",
            supported_scope=scope,
            release_label=release_label,
            readiness=readiness,
            manifest_sha256=manifest["manifest_sha256"],
            previous_release=current.current_release if current else None,
        )
    elif release.state not in {"published", "retired"}:
        release.state = "ready" if report["ready"] else "blocked"
        release.supported_scope = scope
        release.release_label = release_label
        release.readiness = readiness
        release.save(update_fields=["state", "supported_scope", "release_label", "readiness"])
        KnowledgeReleaseRule.objects.filter(knowledge_release=release).delete()
        KnowledgeReleaseFact.objects.filter(knowledge_release=release).delete()
    if release.state not in {"published", "retired"}:
        if prepared and report['ready']:
            for product in report['products']:
                version = PolicyVersion.objects.get(pk=product['policy_version_id'])
                job = ProcessingJob.objects.get(pk=product['validation_job_id'])
                artifact, _rule_ids = verify_fact_artifact(version, job)
                KnowledgeReleaseFact.objects.bulk_create([
                    KnowledgeReleaseFact(knowledge_release=release, policy_version=version,
                        validation_job=job, validation_sha256=job.result_storage_sha256,
                        criterion=fact['criterion'], fact=fact, fact_sha256=digest(fact))
                    for fact in artifact['criteria']])
        KnowledgeReleaseRule.objects.bulk_create(
            [KnowledgeReleaseRule(knowledge_release=release, policy_rule=rule) for rule in rules],
            ignore_conflicts=True,
        )
        if report["ready"]:
            PolicyVersion.objects.filter(id__in=policy_version_ids).update(
                publication_status="reviewed"
            )
    return release, report


@transaction.atomic
def publish_release(release_id: uuid.UUID | str) -> KnowledgeRelease:
    release = KnowledgeRelease.objects.select_for_update().get(pk=release_id)
    if release.state == "published":
        return release
    if release.state != "ready":
        raise ValueError("Only a ready release can be published.")
    manifest_path = find_captured_manifest(release.manifest_sha256)
    if manifest_path is None:
        raise ValueError("The exact captured manifest for this release is unavailable.")
    manifest = load_captured_manifest(manifest_path)
    expected_count = comparison_product_count(release)
    if release.readiness.get("catalogue_product_count") != len(manifest["products"]):
        raise ValueError("Release catalogue count differs from its captured manifest.")
    report = _release_report(
        manifest,
        validate_five_product_manifest(manifest_path),
        expected_count,
    )
    if not report["ready"]:
        raise ValueError("Release gates changed: " + "; ".join(report["blockers"]))
    memberships = KnowledgeReleaseRule.objects.filter(knowledge_release=release)
    policy_version_ids = list(
        memberships.values_list("policy_rule__policy_version_id", flat=True).distinct()
    )
    from ..prepared_facts import FACT_RELEASE_VERSION, digest
    from ..processing.artifacts import read_artifact
    if release.readiness.get('fact_release_version') == FACT_RELEASE_VERSION:
        facts = list(KnowledgeReleaseFact.objects.filter(knowledge_release=release))
        expected = {p['policy_version_id']: p for p in report['products']}
        if len(facts) != expected_count * 13:
            raise ValueError('Publication requires every reviewed criterion for every product.')
        approved_rows = {p['policy_version_id']: {f['criterion']: f for f in read_artifact(
            ProcessingJob.objects.get(pk=p['validation_job_id']))['criteria']} for p in report['products']}
        for fact in facts:
            product = expected.get(str(fact.policy_version_id))
            if (not product or product['validation_job_id'] != str(fact.validation_job_id)
                    or product['validation_sha256'] != fact.validation_sha256
                    or digest(fact.fact) != fact.fact_sha256
                    or fact.fact != approved_rows.get(str(fact.policy_version_id), {}).get(fact.criterion)):
                raise ValueError('Published fact membership differs from current reviewed validation.')
        policy_version_ids = list({f.policy_version_id for f in facts})
    if len(policy_version_ids) != expected_count:
        raise ValueError(
            f"Publication requires rules from exactly {expected_count} policy versions."
        )
    PolicyVersion.objects.filter(id__in=policy_version_ids).update(publication_status="published")
    now = timezone.now()
    release.state = "published"
    release.published_at = now
    release.save(update_fields=["state", "published_at"])
    channel = KnowledgeChannel.objects.select_for_update().filter(name="live").first()
    previous = channel.current_release if channel else None
    if channel is None:
        channel = KnowledgeChannel.objects.create(
            name="live", current_release=release, generation=1
        )
    else:
        channel.current_release = release
        channel.generation += 1
        channel.save(update_fields=["current_release", "generation", "updated_at"])
    if previous is not None and previous.id != release.id and previous.state == "published":
        previous.state = "retired"
        previous.save(update_fields=["state"])
    Outbox.objects.get_or_create(
        event_type="knowledge_publication",
        knowledge_release=release,
        idempotency_key=f"knowledge:{release.id}",
        defaults={"state": "delivered", "attempt_count": 1},
    )
    return release
