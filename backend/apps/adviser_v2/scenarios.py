"""Fail-closed inventory and durable execution helpers for adviser scenarios."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from pathlib import Path
from typing import Any, cast

from django.db import transaction

from apps.accounts.models import User

from .engine import process_turn
from .models import (
    Conversation,
    CustomerProfileRevision,
    KnowledgeChannel,
    KnowledgeRelease,
    KnowledgeReleaseRule,
    Recommendation,
    Turn,
)
from .readiness import find_captured_manifest, load_captured_manifest
from .services.customer import submit_message

SCENARIO_NAMESPACE = uuid.UUID("17d49af8-1438-40fd-965a-59b757ebef08")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def load_scenarios(paths: list[Path]) -> tuple[list[dict[str, Any]], str]:
    records: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    identifiers: set[str] = set()
    for path in paths:
        payload = path.read_bytes()
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
        for line_number, line in enumerate(payload.decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number} is invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object.")
            record = cast(dict[str, Any], value)
            case_id = record.get("case_id")
            if not isinstance(case_id, str) or not case_id:
                raise ValueError(f"{path}:{line_number} has no case_id.")
            if case_id in identifiers:
                raise ValueError(f"Duplicate scenario case_id: {case_id}")
            identifiers.add(case_id)
            records.append(record)
    return records, digest.hexdigest()


def load_subset(path: Path | None, known_case_ids: set[str]) -> tuple[set[str], list[str]]:
    if path is None or not path.exists():
        return set(), ["independent_five_product_subset_missing"]
    records, _digest = load_scenarios([path])
    identifiers = {str(item["case_id"]) for item in records}
    blockers: list[str] = []
    if len(identifiers) != 50:
        blockers.append("independent_subset_must_contain_exactly_50_cases")
    unknown = identifiers - known_case_ids
    if unknown:
        blockers.append("independent_subset_contains_unknown_case_ids")
    return identifiers, blockers


def _walk(value: object) -> list[tuple[str, object]]:
    found: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            found.append((str(key), item))
            found.extend(_walk(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_walk(item))
    return found


def case_dependencies(record: dict[str, Any], release_uins: set[str]) -> tuple[set[str], set[str]]:
    source_hashes: set[str] = set()
    uins: set[str] = set()
    for key, value in _walk(record):
        if key in {"source_sha256", "original_sha256"} and isinstance(value, str):
            lowered = value.lower()
            if SHA256_RE.fullmatch(lowered):
                source_hashes.add(lowered)
        if isinstance(value, str) and value in release_uins:
            uins.add(value)
    return source_hashes, uins


def release_inventory() -> tuple[KnowledgeRelease | None, set[str], set[str], list[str]]:
    channel = KnowledgeChannel.objects.select_related("current_release").filter(name="live").first()
    release = channel.current_release if channel else None
    if release is None or release.state != "published":
        return None, set(), set(), ["five_product_release_not_published"]
    release_uins = {
        value
        for value in KnowledgeReleaseRule.objects.filter(knowledge_release=release).values_list(
            "policy_rule__policy_version__uin", flat=True
        )
        if isinstance(value, str)
    }
    blockers: list[str] = []
    if len(release_uins) != 5:
        blockers.append("published_release_does_not_resolve_to_five_uins")
    manifest_path = find_captured_manifest(release.manifest_sha256)
    if manifest_path is None:
        blockers.append("captured_release_manifest_missing")
        return release, release_uins, set(), blockers
    manifest = load_captured_manifest(manifest_path)
    hashes = {
        str(document["sha256"])
        for product in manifest["products"]
        for document in product["documents"]
        if isinstance(document, dict) and isinstance(document.get("sha256"), str)
    }
    return release, release_uins, hashes, blockers


def classify_scenarios(
    records: list[dict[str, Any]], release_uins: set[str], release_hashes: set[str]
) -> tuple[list[dict[str, object]], dict[str, int]]:
    classified: list[dict[str, object]] = []
    counts = {
        "answerable_from_five_product_release": 0,
        "requires_future_wider_corpus": 0,
        "unmapped_dependency": 0,
    }
    for record in records:
        source_hashes, uins = case_dependencies(record, release_uins)
        if release_hashes and source_hashes and source_hashes.issubset(release_hashes):
            classification = "answerable_from_five_product_release"
        elif not source_hashes and uins:
            classification = "answerable_from_five_product_release"
        elif source_hashes or uins:
            classification = "requires_future_wider_corpus"
        else:
            classification = "unmapped_dependency"
        counts[classification] += 1
        classified.append(
            {
                "case_id": str(record["case_id"]),
                "classification": classification,
                "matched_release_uins": sorted(uins),
                "dependency_hash_count": len(source_hashes),
            }
        )
    return classified, counts


def _scenario_user(case_id: str, attempt: int) -> User:
    user_id = uuid.uuid5(SCENARIO_NAMESPACE, f"user:{case_id}:{attempt}")
    user = User.objects.filter(pk=user_id).first()
    if user is not None:
        return user
    user = User(
        id=user_id,
        email=f"scenario-{user_id.hex}@invalid.coverguide.local",
        is_active=False,
    )
    user.set_unusable_password()
    user.save()
    return user


@transaction.atomic
def _scenario_conversation(user: User, case_id: str, attempt: int) -> Conversation:
    conversation_id = uuid.uuid5(SCENARIO_NAMESPACE, f"conversation:{case_id}:{attempt}")
    existing = Conversation.objects.select_for_update().filter(pk=conversation_id).first()
    if existing is not None:
        if existing.owner_id != user.id:
            raise ValueError("Deterministic scenario conversation belongs to another owner.")
        return existing
    conversation = Conversation.objects.create(
        id=conversation_id,
        owner=user,
        title=f"Scenario {case_id}, attempt {attempt}",
    )
    revision = CustomerProfileRevision.objects.create(
        owner=user, conversation=conversation, revision=1
    )
    conversation.current_profile_revision = revision
    conversation.save(update_fields=["current_profile_revision", "updated_at"])
    return conversation


def run_scenario_attempt(record: dict[str, Any], attempt: int) -> dict[str, object]:
    case_id = str(record["case_id"])
    user = _scenario_user(case_id, attempt)
    conversation = _scenario_conversation(user, case_id, attempt)
    raw_conversation = record.get("conversation", [])
    conversation_items = raw_conversation if isinstance(raw_conversation, list) else []
    customer_messages = [
        cast(dict[str, Any], item)
        for item in conversation_items
        if isinstance(item, dict)
        and item.get("role") == "customer"
        and isinstance(item.get("text"), str)
        and item["text"].strip()
    ]
    if not customer_messages:
        return {
            "case_id": case_id,
            "attempt": attempt,
            "turn_id": None,
            "state": "not_executable",
            "error_code": "customer_conversation_missing",
            "raised_error_type": None,
            "recommendation_id": None,
            "outcome": "insufficient_evidence",
            "semantic_assessment": "not_assessable",
        }
    last_turn: Turn | None = None
    raised_error: str | None = None
    for ordinal, item in enumerate(customer_messages, 1):
        text = str(item["text"])
        request_id = uuid.uuid5(
            SCENARIO_NAMESPACE,
            f"request:{case_id}:{attempt}:{ordinal}:{hashlib.sha256(text.encode()).hexdigest()}",
        )
        last_turn = Turn.objects.filter(owner=user, request_id=request_id).first()
        if last_turn is None:
            conversation.refresh_from_db(fields=["current_profile_revision"])
            revision = conversation.current_profile_revision
            if revision is None:
                raise ValueError("Scenario conversation lost its profile revision.")
            submitted = submit_message(
                user.id,
                conversation.id,
                request_id=request_id,
                text=text,
                expected_profile_revision=revision.revision,
            )
            last_turn = submitted.turn
        if last_turn.state == "queued":
            try:
                process_turn(last_turn.id)
            except Exception as exc:  # noqa: BLE001 - durable turn records the safe error code.
                raised_error = type(exc).__name__
            last_turn.refresh_from_db()
        if last_turn.state != "completed":
            break
    if last_turn is None:
        raise AssertionError("An executable scenario did not produce a turn.")
    recommendation = Recommendation.objects.filter(turn=last_turn).first()
    return {
        "case_id": case_id,
        "attempt": attempt,
        "turn_id": str(last_turn.id),
        "state": last_turn.state,
        "error_code": last_turn.error_code,
        "raised_error_type": raised_error,
        "recommendation_id": str(recommendation.id) if recommendation else None,
        "outcome": recommendation.outcome if recommendation else None,
        "semantic_assessment": "pending_independent_assessment",
    }


def load_assessments(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{number} must contain an object.")
        records.append(cast(dict[str, Any], value))
    return records


def acceptance_summary(
    subset_ids: set[str], assessments: list[dict[str, Any]]
) -> dict[str, object]:
    blockers: list[str] = []
    if len(subset_ids) != 50:
        blockers.append("frozen_independent_50_case_subset_unavailable")
    rows_by_case: dict[str, list[dict[str, Any]]] = {}
    for row in assessments:
        case_id = str(row.get("case_id", ""))
        if case_id in subset_ids:
            rows_by_case.setdefault(case_id, []).append(row)
    if subset_ids and any(len(rows_by_case.get(case_id, [])) != 3 for case_id in subset_ids):
        blockers.append("every_subset_case_requires_three_independently_scored_attempts")
    passing_cases = 0
    product_passes: dict[str, int] = {}
    critical_failures = 0
    for case_id in subset_ids:
        rows = rows_by_case.get(case_id, [])
        case_passed = len(rows) == 3 and all(row.get("passed") is True for row in rows)
        if any(row.get("critical_failures") for row in rows):
            critical_failures += 1
            case_passed = False
        if case_passed:
            passing_cases += 1
            product = str(rows[0].get("product_uin", "unmapped"))
            product_passes[product] = product_passes.get(product, 0) + 1
    accepted = (
        not blockers
        and passing_cases >= 45
        and len(product_passes) == 5
        and all(value >= 9 for value in product_passes.values())
        and critical_failures == 0
    )
    return {
        "assessable": not blockers,
        "accepted": accepted,
        "passing_cases": passing_cases,
        "required_passing_cases": 45,
        "product_passes": product_passes,
        "critical_failure_cases": critical_failures,
        "blockers": blockers,
    }
