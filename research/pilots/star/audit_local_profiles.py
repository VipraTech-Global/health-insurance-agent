"""Read-only audit of the four synthetic conversations exercised through the UI.

Run with scripts/star_slice.sh manage shell after all four browser runs finish.
Original PDF/text objects stay in local storage; this report contains synthetic data.
"""

import hashlib
import json
from collections import Counter
from pathlib import Path

from apps.adviser_v2.models import (
    Comparison,
    ComparisonStatement,
    EvidenceSpan,
    KnowledgeReleaseFact,
    KnowledgeReleaseRule,
    Message,
    ModelAttempt,
    PolicyComparisonAssessment,
    Turn,
)
from apps.adviser_v2.processing.clause_citations import RECTANGLES_PREFIX
from apps.adviser_v2.processing.manifest_v2 import ANCHOR_PREFIX, raw_bundle_passages
from apps.adviser_v2.selectors.comparisons import comparison_payload
from apps.adviser_v2.selectors.customer import current_profile_payload
from django.conf import settings
from django.utils import timezone

ROOT = Path(settings.BASE_DIR).parent
assert settings.DATABASES["default"]["NAME"] == "coverguide_star_slice"
seeds = json.loads((ROOT / "research/pilots/star/synthetic-profiles.json").read_text())
messages = list(
    Message.objects.filter(owner__email="star-fact-review@example.test", role="customer")
)
rows = []
all_checked = set()
search_log = Path(settings.COVERGUIDE_REPORT_ROOT) / "pageindex-live-calls.jsonl"
search_calls = (
    [json.loads(line) for line in search_log.read_text().splitlines()] if search_log.exists() else []
)
for seed in seeds:
    first = next(
        m for m in messages if m.content.startswith("Synthetic profile " + seed["id"] + ":")
    )
    comparison = Comparison.objects.filter(turn__conversation=first.conversation).latest(
        "created_at"
    )
    assert comparison.turn.state == "completed"
    payload = comparison_payload(comparison.owner_id, comparison.id)
    for statement in payload["statements"]:
        ComparisonStatement._meta.get_field("support_status").validate(
            statement["support_status"], None
        )
    profile = current_profile_payload(comparison.owner_id, first.conversation_id)
    expected = seed["facts"]
    ages = sorted(float(f["value"]["value"]) for f in profile["facts"] if f["fact_type"] == "age")
    assert ages == sorted(expected["ages"]), (seed["id"], ages)
    amounts = [f["value"] for f in profile["facts"] if f["fact_type"] == "sum_insured"]
    amounts += [
        r["target_value"] for r in profile["requirements"] if r["criterion"] == "sum_insured"
    ]
    assert any(float(v["value"]) == expected["requested_sum_insured_inr"] for v in amounts)
    for key in ("city", "budget"):
        assert any(
            f["fact_type"] == key and f["value"]["state"] == "unknown" for f in profile["facts"]
        )
    assert len(payload["products"]) == 3
    assessments = {
        str(a.id): a
        for a in PolicyComparisonAssessment.objects.filter(comparison=comparison).select_related(
            "product_variant__policy_version"
        )
    }
    products = []
    checked = set()
    for product in payload["products"]:
        assert product["quote_id"] is None
        assert product["evaluated_selection"]["options"] == []
        assert len(product["prepared_facts"]) == 13
        assert all(
            f["status"] == "supported"
            and f["value"]
            and f["citations"]
            and not f["unknown_reasons"]
            for f in product["prepared_facts"]
        )
        assessment = assessments[product["id"]]
        pages = {
            p["evidence_span_id"]: p
            for p in raw_bundle_passages(
                assessment.product_variant.policy_version, include_prospectus=True
            )
        }
        statements = [
            s for s in payload["statements"] if s["comparison_assessment_id"] == product["id"]
        ]
        assert len(statements) == 1, (seed["id"], product["product"], statements)
        assert statements[0]["citations"] or statements[0]["statement_type"] == "limitation"
        citations = [c for f in product["prepared_facts"] for c in f["citations"]]
        citations += [c for s in statements for c in s["citations"]]
        for citation in citations:
            span = EvidenceSpan.objects.select_related("source_capture", "page").get(
                pk=citation["evidence_span_id"]
            )
            parent = pages[
                span.context["span_ids"][0]
            ]  # Fails on any other-plan or excluded source.
            anchor = json.loads(
                next(
                    n[len(ANCHOR_PREFIX) :]
                    for n in span.context["notes"]
                    if n.startswith(ANCHOR_PREFIX)
                )
            )
            boxes = json.loads(
                next(
                    n[len(RECTANGLES_PREFIX) :]
                    for n in span.context["notes"]
                    if n.startswith(RECTANGLES_PREFIX)
                )
            )
            assert boxes and span.locator["bbox"]
            assert (
                parent["passage"][anchor["start"] : anchor["end"]]
                == span.quote
                == citation["quote"]
            )
            assert (
                anchor["page_text_sha256"] == hashlib.sha256(parent["passage"].encode()).hexdigest()
            )
            assert span.page.page_number == anchor["page"] == parent["physical_page"]
            assert anchor["document_start"] == parent["document_char_start"] + anchor["start"]
            assert anchor["document_end"] == parent["document_char_start"] + anchor["end"]
            checked.add(str(span.id))
        # Descriptive facts never become computed personal requirement matches.
        non_executable = {
            f["criterion"] for f in product["prepared_facts"] if f["rule_status"] != "executable"
        }
        assert all(
            c["outcome"] in {"unknown", "not_applicable"}
            for c in product["criteria"]
            if c["criterion"] in non_executable
        )
        products.append(
            {
                "product": product["product"],
                "prepared_supported": 13,
                "non_executable_facts": len(non_executable),
                "quote": "unavailable",
                "selected_options": [],
                "source_answer": statements[0],
            }
        )
    all_checked.update(checked)
    turns = list(Turn.objects.filter(conversation=first.conversation).order_by("created_at"))
    attempts = list(ModelAttempt.objects.filter(turn__in=turns).order_by("created_at"))
    final_searches = [c for c in search_calls if c["turn_id"] == str(comparison.turn_id)]
    if settings.COVERGUIDE_EVIDENCE_RETRIEVAL == "pageindex":
        completed_searches = [c for c in final_searches if c["status"] == "completed"]
        expected_plans = {str(a.product_variant.policy_version_id) for a in assessments.values()}
        assert {c["policy_version_id"] for c in completed_searches} == expected_plans
        assert len(completed_searches) == 3
    rows.append(
        {
            "profile": seed["id"],
            "conversation_id": str(first.conversation_id),
            "comparison_id": str(comparison.id),
            "final_turn_id": str(comparison.turn_id),
            "final_question": comparison.turn.input_message.content,
            "final_turn_wall_seconds": round(
                (comparison.turn.updated_at - comparison.turn.created_at).total_seconds(), 3
            ),
            "pageindex_search_calls": final_searches,
            "earlier_unknown_statements": list(
                ComparisonStatement.objects.filter(
                    comparison__turn__conversation=first.conversation,
                    support_status="unknown",
                )
                .exclude(comparison=comparison)
                .values("comparison_id", "comparison__turn_id", "text")
            ),
            "profile_snapshot": profile,
            "products": products,
            "distinct_native_anchors_checked": len(checked),
            "turns": [{"id": str(t.id), "state": t.state, "error": t.error_code} for t in turns],
            "model_attempts": [
                {
                    "id": str(a.id),
                    "turn_id": str(a.turn_id),
                    "stage": a.qualification.schema_name,
                    "status": a.status,
                    "usage": a.usage,
                    "error": a.error_code,
                    "wall_ms": round((a.completed_at - a.started_at).total_seconds() * 1000)
                    if a.completed_at
                    else None,
                }
                for a in attempts
            ],
            "attempt_status_counts": dict(Counter(a.status for a in attempts)),
        }
    )
release = comparison.knowledge_release
assert KnowledgeReleaseFact.objects.filter(knowledge_release=release).count() == 39
report = {
    "checked_at": timezone.now().isoformat(),
    "database": "coverguide_star_slice",
    "retrieval_method_at_audit": settings.COVERGUIDE_EVIDENCE_RETRIEVAL,
    "release_id": str(release.id),
    "release_state": release.state,
    "prepared_facts": 39,
    "executable_rule_records": KnowledgeReleaseRule.objects.filter(
        knowledge_release=release
    ).count(),
    "distinct_native_anchors_checked": len(all_checked),
    "pageindex_live_cost_including_superseded_runs": {
        "calls": len(search_calls),
        "failures": sum(c["status"] != "completed" for c in search_calls),
        "wall_ms_sum": sum(c["wall_ms"] for c in search_calls),
        "input_tokens": sum(c.get("usage", {}).get("input_tokens", 0) for c in search_calls),
        "cached_input_tokens": sum(
            c.get("usage", {}).get("input_tokens_details", {}).get("cached_tokens", 0)
            for c in search_calls
        ),
        "output_tokens": sum(c.get("usage", {}).get("output_tokens", 0) for c in search_calls),
        "reasoning_tokens": sum(
            c.get("usage", {}).get("output_tokens_details", {}).get("reasoning_tokens", 0)
            for c in search_calls
        ),
    },
    "profiles": rows,
    "ui_cell_citation_audit": "output/star-ui-citation-audit.json",
}
(ROOT / "output/star-e2e-review.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
print(json.dumps({"profiles": len(rows), "anchors": len(all_checked), "release": str(release.id)}))
