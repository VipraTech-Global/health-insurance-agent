from datetime import date, timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.adviser.corpus import lock_corpus_publication
from apps.adviser.evidence import create_evidence_bundle_from_ranges
from apps.adviser.models import (
    CatalogueListing,
    CorpusRelease,
    DocumentPage,
    DocumentVersion,
    ExtractionRevision,
    Insurer,
    PlanDocumentAssociation,
    PlanVersion,
    ReviewEvent,
    SourceObservation,
    VerifiedFact,
)
from apps.adviser.source_maps import DocumentValidationError, verified_source_path

SOURCE_SHA256 = "1b1eea97989a76090767482093e663af04f8cadbd122b5f845b0b7144c6083d2"
UIN = "CHIHLIP27061V032627"
OFFICIAL_URL = (
    "https://cms.careinsurance.com/cms/public/uploads/download_center/"
    "care-supreme---policy-terms-%26-conditions-%28effective-from-29-april-2026%29.pdf"
    "?rv=0.39631700+1788960674"
)


class Command(BaseCommand):
    help = "Activate the hash-pinned Care Supreme document as the one-plan local pilot corpus."

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            document = DocumentVersion.objects.select_related("blob").get(
                blob__sha256=SOURCE_SHA256,
                document_type="policy_wording",
                identity="Care Supreme policy wording (Ditto-hosted)",
            )
        except DocumentVersion.DoesNotExist as exc:
            raise CommandError("The expected preserved document is absent.") from exc
        revision = (
            ExtractionRevision.objects.filter(document_version=document)
            .order_by("-revision")
            .first()
        )
        if revision is None:
            raise CommandError("Extract the preserved document before activation.")
        if document.blob.sha256 != SOURCE_SHA256:
            raise CommandError(
                "The preserved Care Supreme source hash does not match the approved file."
            )
        try:
            verified_source_path(document.blob)
        except DocumentValidationError as exc:
            raise CommandError(str(exc)) from exc

        if not SourceObservation.objects.filter(
            locator__url=OFFICIAL_URL,
            status_code=200,
            available=True,
            content_sha256=SOURCE_SHA256,
            fetched_at__gte=timezone.now() - timedelta(days=7),
        ).exists():
            raise CommandError(
                "Acquire the official URL with ingest_document before activation; a real "
                "hash-matching source observation is required."
            )

        existing = CorpusRelease.objects.filter(name="local-pilot-care-supreme-v1").first()
        if existing and existing.activated_at:
            self._reactivate_existing(existing, revision)
            self.stdout.write(
                self.style.SUCCESS(f"Pilot corpus is active and valid: {existing.id}")
            )
            return

        pages = {
            number: DocumentPage.objects.get(
                extraction_revision=revision, physical_index=number - 1
            )
            for number in (2, 26, 34, 36)
        }
        with transaction.atomic():
            lock_corpus_publication()
            insurer, _ = Insurer.objects.update_or_create(
                name="Care Health Insurance Limited",
                defaults={"aliases": ["Care"], "official_domains": ["careinsurance.com"]},
            )
            plan, _ = PlanVersion.objects.update_or_create(
                insurer=insurer,
                uin=UIN,
                variant="Base policy wording",
                effective_from=date(2026, 4, 29),
                defaults={
                    "name": "Care Supreme",
                    "available_for_new_purchase": None,
                    "review_state": "verified",
                },
            )
            association, _ = PlanDocumentAssociation.objects.update_or_create(
                plan_version=plan,
                document_version=document,
                role="base_policy_wording",
                defaults={
                    "applicability": {"effective_from": "2026-04-29", "uin": UIN},
                    "reviewed": True,
                },
            )
            fact_specs = [
                (
                    "pre_existing_disease_waiting_period",
                    "duration",
                    {"months": "36"},
                    "Care Supreme pre-existing disease waiting period and conditions",
                    [
                        (pages[34], 14, 14, "context"),
                        (pages[34], 15, 17, "primary"),
                        (pages[34], 18, 18, "primary"),
                        (pages[34], 21, 23, "condition"),
                        (pages[34], 24, 24, "condition"),
                        (pages[34], 25, 26, "condition"),
                        (pages[34], 27, 27, "condition"),
                    ],
                    {"portability_credit": True, "declaration_and_acceptance_required": True},
                ),
                (
                    "named_ailment_waiting_period",
                    "duration",
                    {"months": "24"},
                    "Care Supreme named ailment waiting period",
                    [(pages[34], 28, 33, "primary")],
                    {"accident_exception": True},
                ),
                (
                    "initial_waiting_period",
                    "duration",
                    {"days": "30"},
                    "Care Supreme initial waiting period",
                    [
                        (pages[36], 3, 3, "context"),
                        (pages[36], 5, 7, "primary"),
                        (pages[36], 8, 8, "primary"),
                        (pages[36], 9, 9, "condition"),
                        (pages[36], 10, 10, "condition"),
                    ],
                    {"accident_exception": True, "continuous_coverage_condition": True},
                ),
                (
                    "optional_copayment",
                    "structured_text",
                    {"optional": True, "amount_source": "policy_schedule"},
                    "Care Supreme optional co-payment",
                    [
                        (pages[26], 10, 10, "context"),
                        (pages[26], 14, 17, "primary"),
                        (pages[26], 18, 18, "primary"),
                    ],
                    {"only_if_selected": True},
                ),
            ]
            facts = []
            required_terms = {
                "pre_existing_disease_waiting_period": (
                    "36 months",
                    "portability",
                    "declared",
                    "accepted by insurer",
                ),
                "named_ailment_waiting_period": ("24 months", "accident"),
                "initial_waiting_period": ("30 days", "continuous coverage"),
                "optional_copayment": ("co-payment", "policy schedule", "each and every claim"),
            }
            if VerifiedFact.objects.filter(
                plan_version=plan, category__in=[spec[0] for spec in fact_specs]
            ).exists():
                raise CommandError(
                    "Fact rows already exist without the expected active release; manual review is required."
                )
            for category, value_type, value, label, ranges, applicability in fact_specs:
                bundle = create_evidence_bundle_from_ranges(ranges, label)
                evidence_text = " ".join(bundle.spans.values_list("quote", flat=True)).casefold()
                if any(term not in evidence_text for term in required_terms[category]):
                    raise CommandError(
                        f"The latest extraction no longer supports the pinned {category} fact."
                    )
                bundle.review_state = "verified"
                bundle.save(update_fields=["review_state"])
                fact = VerifiedFact.objects.create(
                    plan_version=plan,
                    category=category,
                    value_type=value_type,
                    value=value,
                    applicability=applicability,
                    evidence_bundle=bundle,
                    verification_state="verified",
                )
                ReviewEvent.objects.create(
                    object_type="VerifiedFact",
                    object_id=fact.id,
                    expected_revision=revision.artifact_sha256,
                    decision="pilot_activate",
                    reason="Exact lines checked against the hash-pinned official policy wording.",
                )
                facts.append(fact)

            revision.published = True
            revision.save(update_fields=["published"])
            listing = CatalogueListing.objects.get(
                ditto_path="/health-insurance/care/care-supreme/"
            )
            listing.insurer = insurer
            listing.status = CatalogueListing.Status.AWAITING_REVIEW
            listing.status_reason = (
                "Enabled for one-plan evidence-delivery testing. Four facts are verified, but the "
                "plan is not recommendable until remaining decision-critical evidence is reviewed."
            )
            listing.save(update_fields=["insurer", "status", "status_reason"])
            CorpusRelease.objects.select_for_update().filter(is_current=True).update(
                is_current=False
            )
            release, _ = CorpusRelease.objects.update_or_create(
                name="local-pilot-care-supreme-v1",
                defaults={
                    "manifest": {
                        "test_only": True,
                        "plan_version_id": str(plan.id),
                        "document_id": str(document.id),
                        "source_sha256": SOURCE_SHA256,
                        "extraction_revision_id": str(revision.id),
                        "extraction_artifact_sha256": revision.artifact_sha256,
                        "fact_ids": [str(fact.id) for fact in facts],
                        "official_source": OFFICIAL_URL,
                    },
                    "activated_at": timezone.now(),
                    "is_current": True,
                },
            )
            ReviewEvent.objects.create(
                object_type="PlanDocumentAssociation",
                object_id=association.id,
                expected_revision=SOURCE_SHA256,
                decision="pilot_activate",
                reason="Ditto-hosted bytes match the insurer's official current download exactly.",
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Activated Care Supreme local pilot corpus {release.id} with {len(facts)} facts."
            )
        )

    def _reactivate_existing(self, release: CorpusRelease, revision: ExtractionRevision) -> None:
        with transaction.atomic():
            lock_corpus_publication()
            locked = CorpusRelease.objects.select_for_update().get(id=release.id)
            self._validate_active_release(locked, revision)
            CorpusRelease.objects.exclude(id=locked.id).update(is_current=False)
            locked.is_current = True
            locked.save(update_fields=["is_current"])
            CatalogueListing.objects.filter(
                ditto_path="/health-insurance/care/care-supreme/"
            ).update(
                status=CatalogueListing.Status.AWAITING_REVIEW,
                status_reason=(
                    "Enabled for one-plan evidence-delivery testing. Four facts are verified, "
                    "but the plan is not recommendable until remaining decision-critical evidence "
                    "is reviewed."
                ),
            )

    def _validate_active_release(
        self, release: CorpusRelease, revision: ExtractionRevision
    ) -> None:
        expected_values = {
            "pre_existing_disease_waiting_period": {"months": "36"},
            "named_ailment_waiting_period": {"months": "24"},
            "initial_waiting_period": {"days": "30"},
            "optional_copayment": {"optional": True, "amount_source": "policy_schedule"},
        }
        expected_value_types = {
            "pre_existing_disease_waiting_period": "duration",
            "named_ailment_waiting_period": "duration",
            "initial_waiting_period": "duration",
            "optional_copayment": "structured_text",
        }
        expected_applicability = {
            "pre_existing_disease_waiting_period": {
                "portability_credit": True,
                "declaration_and_acceptance_required": True,
            },
            "named_ailment_waiting_period": {"accident_exception": True},
            "initial_waiting_period": {
                "accident_exception": True,
                "continuous_coverage_condition": True,
            },
            "optional_copayment": {"only_if_selected": True},
        }
        required_terms = {
            "pre_existing_disease_waiting_period": (
                "36 months",
                "portability",
                "declared",
                "accepted by insurer",
            ),
            "named_ailment_waiting_period": ("24 months", "accident"),
            "initial_waiting_period": ("30 days", "continuous coverage"),
            "optional_copayment": ("co-payment", "policy schedule", "each and every claim"),
        }
        manifest = release.manifest
        if (
            manifest.get("source_sha256") != SOURCE_SHA256
            or manifest.get("extraction_revision_id") != str(revision.id)
            or manifest.get("extraction_artifact_sha256") != revision.artifact_sha256
            or manifest.get("official_source") != OFFICIAL_URL
        ):
            raise CommandError(
                "The active release manifest does not match the pinned pilot inputs."
            )
        fact_ids = manifest.get("fact_ids")
        if not isinstance(fact_ids, list) or len(fact_ids) != len(expected_values):
            raise CommandError("The active release fact manifest is incomplete.")
        facts = list(
            VerifiedFact.objects.filter(id__in=fact_ids)
            .select_related("evidence_bundle")
            .prefetch_related("evidence_bundle__evidencebundlespan_set__span__page")
        )
        if len(facts) != len(expected_values):
            raise CommandError("One or more active release facts no longer exist.")
        for fact in facts:
            if (
                fact.category not in expected_values
                or fact.value != expected_values[fact.category]
                or fact.value_type != expected_value_types[fact.category]
                or fact.applicability != expected_applicability[fact.category]
                or fact.verification_state != "verified"
                or fact.conflict
                or fact.evidence_bundle.review_state != "verified"
            ):
                raise CommandError(f"Active fact {fact.id} no longer matches the pinned release.")
            links = list(fact.evidence_bundle.evidencebundlespan_set.all())
            if not links or any(
                link.span.page.extraction_revision_id != revision.id for link in links
            ):
                raise CommandError(f"Active fact {fact.id} has an invalid evidence chain.")
            evidence_text = " ".join(link.span.quote for link in links).casefold()
            if any(term not in evidence_text for term in required_terms[fact.category]):
                raise CommandError(f"Active fact {fact.id} evidence no longer supports its value.")
