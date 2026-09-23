"""Directly capture only entries in a reviewed five-product manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from apps.adviser_v2.manifest import (
    POLICY_MEMBERSHIP_ROLE_BY_DOCUMENT_ROLE,
    ManifestDocument,
    ManifestProduct,
    download_manifest_entry,
    load_manifest,
    manifest_sha256,
)
from apps.adviser_v2.models import (
    DiscoveryRun,
    DocumentSeries,
    DocumentVersion,
    EvidenceSpan,
    Insurer,
    OriginalFile,
    PolicyVersion,
    PolicyVersionDocument,
    Product,
    ProductVariant,
    SourceCapture,
    SourceObservation,
    SourceURL,
)
from apps.adviser_v2.processing.identity import reconcile_capture_identity
from apps.adviser_v2.storage import store_public

TRUE_APPLICABILITY = {
    "schema_version": 1,
    "predicate": {"node": "constant", "value": "true"},
    "event_basis": ["issue"],
    "source_span_ids": [],
    "unresolved": [],
}

KIND_MAP = {
    "base_wording": "policy_wording",
    "customer_information_sheet": "customer_information_sheet",
    "prospectus": "prospectus",
    "premium_table": "premium_table",
    "proposal_form": "other",
    "endorsement": "endorsement",
    "addon_wording": "endorsement",
    "addon_cis": "customer_information_sheet",
    "revision_notice": "notice",
    "product_page": "web_page",
    "provider_network": "provider_list",
}


class Command(BaseCommand):
    help = "Capture only a closed, reviewed five-product official-source manifest."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("manifest", type=Path)
        parser.add_argument("--output", type=Path)

    def handle(self, *args: Any, **options: Any) -> None:
        manifest_path: Path = options["manifest"].resolve()
        try:
            manifest = load_manifest(manifest_path)
        except (OSError, ValueError) as exc:
            raise CommandError(f"Manifest validation failed: {exc}") from exc
        reviewed_hosts = {host.lower() for host in manifest.official_hosts}
        input_hash = manifest_sha256(manifest.model_dump(mode="json"))
        captured_products: list[dict[str, Any]] = []
        with httpx.Client(
            timeout=httpx.Timeout(60.0, connect=10.0),
            headers={"User-Agent": "CoverGuide-curated-corpus/2"},
        ) as client:
            for product in manifest.products:
                insurer, _ = Insurer.objects.get_or_create(name=product.insurer)
                run, _ = DiscoveryRun.objects.get_or_create(
                    session_id=f"fixed-manifest:{input_hash}:{product.product_key}",
                    defaults={
                        "insurer": insurer,
                        "instructions": (
                            "Direct acquisition of reviewed manifest entries; no traversal."
                        ),
                        "model_name": "none",
                    },
                )
                run.status = "running"
                run.completed_at = None
                run.error_summary = None
                run.save(
                    update_fields=[
                        "status",
                        "completed_at",
                        "error_summary",
                        "updated_at",
                    ]
                )
                try:
                    captured_products.append(
                        self._capture_product(run, product, reviewed_hosts, client)
                    )
                except (httpx.HTTPError, OSError, ValueError) as exc:
                    run.status = "failed"
                    run.error_summary = type(exc).__name__
                    run.completed_at = timezone.now()
                    run.save(
                        update_fields=[
                            "status",
                            "error_summary",
                            "completed_at",
                            "updated_at",
                        ]
                    )
                    raise CommandError(
                        f"Manifest capture stopped safely for {product.product_key}: {exc}"
                    ) from exc
                run.status = "completed"
                run.completed_at = timezone.now()
                run.save(update_fields=["status", "completed_at", "updated_at"])
        frozen = {
            "schema_version": 1,
            "manifest_id": manifest.manifest_id,
            "freeze_date": manifest.freeze_date,
            "input_manifest_sha256": input_hash,
            "products": captured_products,
        }
        frozen["manifest_sha256"] = manifest_sha256(frozen)
        output = options.get("output") or (
            Path(settings.COVERGUIDE_MANIFEST_ROOT) / f"{manifest.manifest_id}-captured.json"
        )
        output = output.resolve()
        allowed_root = Path(settings.COVERGUIDE_MANIFEST_ROOT).resolve()
        if output.parent != allowed_root:
            raise CommandError(
                "Captured manifest output must be directly inside the manifest root."
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.stdout.write(
            self.style.SUCCESS(
                f"Captured {sum(len(item['documents']) for item in captured_products)} exact entries; "
                f"frozen manifest {frozen['manifest_sha256']} written to {output}."
            )
        )

    def _capture_product(
        self,
        run: DiscoveryRun,
        product: ManifestProduct,
        hosts: set[str],
        client: httpx.Client,
    ) -> dict[str, Any]:
        insurer, _ = Insurer.objects.get_or_create(name=product.insurer)
        captured: list[tuple[ManifestDocument, SourceCapture, EvidenceSpan, dict[str, Any]]] = []
        for entry in product.documents:
            try:
                payload, acquisition = download_manifest_entry(entry, hosts, client)
            except (httpx.HTTPError, OSError, ValueError) as exc:
                raise ValueError(f"{entry.document_key}: {exc}") from exc
            captured.append(
                (
                    entry,
                    *self._record_capture(run, insurer, product, entry, payload, acquisition),
                    acquisition,
                )
            )
        contractual = next((item for item in captured if item[0].role == "base_wording"), None)
        if contractual is None or product.uin.lower() not in contractual[2].quote.lower():
            raise ValueError(
                f"{product.name} base wording does not visibly establish expected UIN {product.uin}."
            )
        identity_span = contractual[2]
        with transaction.atomic():
            catalogue_product = Product.objects.filter(insurer=insurer, name=product.name).first()
            if catalogue_product is None:
                catalogue_product = Product.objects.create(
                    insurer=insurer,
                    name=product.name,
                    benefit_type="medical_indemnity",
                    lifecycle_status="open",
                    comparison_role="primary_policy",
                    identity_evidence=identity_span,
                )
            version = PolicyVersion.objects.filter(
                product=catalogue_product, uin=product.uin
            ).first()
            if version is None:
                version = PolicyVersion.objects.create(
                    product=catalogue_product,
                    uin=product.uin,
                    version_label=manifest_label(product),
                    applicability=TRUE_APPLICABILITY,
                )
            ProductVariant.objects.get_or_create(
                policy_version=version,
                name=product.variant,
                defaults={
                    "choices": {"other_selectors": []},
                    "availability": TRUE_APPLICABILITY,
                    "identity_evidence": identity_span,
                },
            )
            captured_document_ids = {
                capture.document_version_id for _entry, capture, _span, _meta in captured
            }
            PolicyVersionDocument.objects.filter(policy_version=version).exclude(
                document_version_id__in=captured_document_ids
            ).delete()
            for entry, capture, _span, _acquisition in captured:
                PolicyVersionDocument.objects.get_or_create(
                    policy_version=version,
                    document_version=capture.document_version,
                    role=POLICY_MEMBERSHIP_ROLE_BY_DOCUMENT_ROLE[entry.role],
                    defaults={
                        "required_for_policy": entry.required,
                        "applicability": TRUE_APPLICABILITY,
                    },
                )
        return {
            "product_key": product.product_key,
            "insurer": product.insurer,
            "name": product.name,
            "uin": product.uin,
            "variant": product.variant,
            "role_decisions": [item.model_dump(mode="json") for item in product.role_decisions],
            "policy_version_id": str(version.id),
            "documents": [
                {
                    "document_key": entry.document_key,
                    "role": entry.role,
                    "official_url": str(entry.url),
                    "capture_id": str(capture.id),
                    "document_version_id": str(capture.document_version_id),
                    "required": entry.required,
                    "expected_applicability": entry.applicability,
                    "applicability_reason": entry.applicability_reason,
                    **acquisition,
                }
                for entry, capture, _span, acquisition in captured
            ],
        }

    @transaction.atomic
    def _record_capture(
        self,
        run: DiscoveryRun,
        insurer: Insurer,
        product: ManifestProduct,
        entry: ManifestDocument,
        payload: bytes,
        acquisition: dict[str, Any],
    ) -> tuple[SourceCapture, EvidenceSpan]:
        stored = store_public(payload)
        original, _ = OriginalFile.objects.get_or_create(
            owner=None,
            sha256=stored.plaintext_sha256,
            defaults={
                "storage_key": stored.storage_key,
                "byte_size": stored.plaintext_size,
                "media_type": entry.expected_media_type,
            },
        )
        source_url, _ = SourceURL.objects.get_or_create(
            url=str(entry.url), defaults={"source_type": "insurer_site"}
        )
        series, _ = DocumentSeries.objects.get_or_create(
            issuer=insurer,
            name=f"{product.name} — {entry.document_key}",
            kind=KIND_MAP[entry.role],
            authority=entry.authority,
            defaults={"relevance": "relevant"},
        )
        version = DocumentVersion.objects.filter(
            document_series=series,
            version_label=str(acquisition["sha256"]),
        ).first()
        if version is None:
            version = DocumentVersion.objects.create(
                document_series=series,
                version_label=str(acquisition["sha256"]),
                identifiers=[
                    {
                        "issuer": product.insurer,
                        "kind": "expected_uin",
                        "value": product.uin,
                        "status": "unresolved",
                    }
                ],
                language="en",
                review_status="identified",
            )
        capture = SourceCapture.objects.filter(
            discovery_run=run,
            source_url=source_url,
            original_file=original,
            document_version=version,
            status="captured",
        ).first()
        if capture is None:
            capture = SourceCapture.objects.create(
                discovery_run=run,
                source_url=source_url,
                completed_at=timezone.now(),
                status="captured",
                http_status=int(str(acquisition["http_status"])),
                original_file=original,
                document_version=version,
            )
            SourceObservation.objects.create(
                discovery_run=run,
                source_url=source_url,
                found_in_capture=capture,
                observation_type="known_url",
                label_or_context=entry.document_key,
                disposition="relevant",
            )
        span, _uin_observed = reconcile_capture_identity(
            capture,
            payload,
            uin=product.uin,
            issuer=product.insurer,
            notes=[entry.applicability_reason],
            record_audit=False,
        )
        return capture, span


def manifest_label(product: ManifestProduct) -> str:
    return f"{product.uin} frozen current-new-business edition"
