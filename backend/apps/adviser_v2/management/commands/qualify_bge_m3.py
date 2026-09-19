"""Qualify the pinned full BGE-M3 runtime against its frozen rankings."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.adviser_v2.embedding import (
    FullModelReferenceV1,
    embed_texts_for_qualification,
    qualification_document,
)


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


class Command(BaseCommand):
    help = "Verify the pinned full ONNX BGE-M3 hashes, normalization and frozen rankings."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("reference", type=Path)
        parser.add_argument("--output", type=Path)

    def handle(self, *args: Any, **options: Any) -> None:
        reference_path: Path = options["reference"].resolve()
        try:
            payload = reference_path.read_bytes()
            reference = FullModelReferenceV1.model_validate_json(payload)
        except (OSError, ValueError) as exc:
            raise CommandError(f"Full-model reference is invalid: {exc}") from exc
        if reference.schema_version != 1 or reference.model_name != "BAAI/bge-m3":
            raise CommandError("The reference must be a BAAI/bge-m3 schema-version 1 corpus.")
        identifiers = [item.id for item in reference.passages]
        if len(identifiers) != len(set(identifiers)):
            raise CommandError("Reference passage IDs must be unique.")
        known_ids = set(identifiers)
        for case in reference.cases:
            if len(case.full_model_ranking) != len(set(case.full_model_ranking)):
                raise CommandError("Each full-model ranking must contain unique passage IDs.")
            if not set(case.full_model_ranking).issubset(known_ids):
                raise CommandError("A full-model ranking references an unknown passage ID.")
        try:
            passage_vectors = embed_texts_for_qualification(
                [item.text for item in reference.passages]
            )
            query_vectors = embed_texts_for_qualification([item.query for item in reference.cases])
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc
        cases: list[tuple[str, list[str], list[str]]] = []
        for case, query_vector in zip(reference.cases, query_vectors, strict=True):
            observed = [
                identifier
                for _score, identifier in sorted(
                    (
                        (_dot(query_vector, vector), identifier)
                        for identifier, vector in zip(identifiers, passage_vectors, strict=True)
                    ),
                    key=lambda item: (-item[0], item[1]),
                )
            ]
            cases.append((case.query, case.full_model_ranking, observed))
        result = qualification_document(
            reference_sha256=hashlib.sha256(payload).hexdigest(),
            cases=cases,
            normalization_max_error=max(
                abs(math.sqrt(sum(value * value for value in vector)) - 1.0)
                for vector in [*passage_vectors, *query_vectors]
            ),
        )
        output = options.get("output")
        if output is None:
            configured = settings.COVERGUIDE_EMBEDDING_QUALIFICATION_PATH
            if not configured:
                raise CommandError("Set COVERGUIDE_EMBEDDING_QUALIFICATION_PATH or pass --output.")
            output = Path(configured)
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
        if not result.passed:
            raise CommandError("Full BGE-M3 failed an exact hash, normalization, or ranking gate.")
        self.stdout.write(
            self.style.SUCCESS(
                f"BGE-M3 passed {len(result.case_results)} cases; qualification written to {output}."
            )
        )
