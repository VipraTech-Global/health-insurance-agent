"""Save the durable state of one recently submitted CoverGuide browser case."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import django  # noqa: E402

django.setup()

from apps.adviser_v2.models import (  # noqa: E402
    EvidenceSpan,
    Message,
    Recommendation,
    Turn,
    TurnEvent,
)
from apps.adviser_v2.selectors.customer import current_profile_payload  # noqa: E402
from apps.adviser_v2.selectors.recommendations import recommendation_payload  # noqa: E402


def main() -> None:
    case = sys.argv[1]
    turns = Turn.objects.select_related("input_message")
    turn = (
        turns.get(pk=sys.argv[2])
        if len(sys.argv) > 2
        else turns.order_by("-created_at").first()
    )
    if turn is None:
        raise RuntimeError("No turn exists")
    recommendation = Recommendation.objects.filter(turn=turn).first()
    payload = (
        recommendation_payload(turn.owner_id, recommendation.id) if recommendation else None
    )
    citation_ids = {
        citation["evidence_span_id"]
        for statement in (payload or {}).get("statements", [])
        for citation in statement["citations"]
    }
    sources = {
        str(span.id): {
            "url": span.source_capture.source_url.url if span.source_capture else None,
            "document_version_id": (
                str(span.source_capture.document_version_id)
                if span.source_capture and span.source_capture.document_version_id
                else None
            ),
            "verification": span.verification,
            "page_review_state": span.page.review_state if span.page else None,
        }
        for span in EvidenceSpan.objects.filter(id__in=citation_ids).select_related(
            "source_capture__source_url", "page"
        )
    }
    for statement in (payload or {}).get("statements", []):
        for citation in statement["citations"]:
            citation["source"] = sources.get(citation["evidence_span_id"])
    messages = list(
        Message.objects.filter(conversation_id=turn.conversation_id)
        .order_by("sequence")
        .values("id", "role", "sequence", "content", "recommendation_id")
    )
    record = {
        "case": case,
        "turn_id": str(turn.id),
        "conversation_id": str(turn.conversation_id),
        "turn_state": turn.state,
        "error_code": turn.error_code,
        "prompt": turn.input_message.content,
        "profile": current_profile_payload(turn.owner_id, turn.conversation_id),
        "recommendation": payload,
        "messages": messages,
        "events": list(
            TurnEvent.objects.filter(turn=turn)
            .order_by("sequence")
            .values("sequence", "event_type", "payload")
        ),
    }
    output = Path(__file__).resolve().parents[1] / "data" / "reports" / "ten-live-cases"
    output.mkdir(parents=True, exist_ok=True)
    destination = output / f"case-{case}.json"
    destination.write_text(json.dumps(record, indent=2, default=str) + "\n")
    candidates = (payload or {}).get("candidates", [])
    print(destination)
    print(
        json.dumps(
            {
                "turn": record["turn_id"],
                "state": turn.state,
                "release": (payload or {}).get("knowledge_release_id"),
                "requirements": [
                    (item["criterion"], item["operator"], item["target_value"])
                    for item in record["profile"]["requirements"]
                ],
                "candidates": [
                    (
                        item["product"],
                        item["disposition"],
                        item["rank"],
                        [
                            (match["criterion"], match["outcome"])
                            for match in item["requirement_matches"]
                        ],
                    )
                    for item in candidates
                ],
            },
            default=str,
        )
    )


if __name__ == "__main__":
    main()
