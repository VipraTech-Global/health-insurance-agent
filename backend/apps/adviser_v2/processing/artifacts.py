"""Encrypted, integrity-checked processing artifacts and source-byte access."""

from __future__ import annotations

import json
import uuid
from typing import Any

from ..models import ProcessingJob
from ..storage import read_private, read_public, store_model_result

SYSTEM_NAMESPACE = uuid.UUID(int=0)


def _namespace(job: ProcessingJob) -> uuid.UUID:
    return job.owner_id or SYSTEM_NAMESPACE


def source_bytes(job: ProcessingJob) -> bytes:
    if job.source_capture_id:
        capture = job.source_capture
        if capture is None:
            raise ValueError("Processing job references a missing public capture.")
        if capture.original_file is None:
            raise ValueError("Captured source has no preserved original bytes.")
        original = capture.original_file
        return read_public(original.storage_key, original.sha256)
    if job.customer_uploaded_document_id:
        upload = job.customer_uploaded_document
        if upload is None:
            raise ValueError("Processing job references a missing customer document.")
        original = upload.original_file
        stored_sha256 = original.storage_key.rsplit("/", 1)[-1].removesuffix(".cg2")
        return read_private(
            _namespace(job),
            "customer-document",
            original.storage_key,
            stored_sha256,
        )
    raise ValueError("Processing job has no source.")


def write_artifact(job: ProcessingJob, value: dict[str, Any]) -> tuple[str, str]:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    stored = store_model_result(_namespace(job), f"processing-{job.id}", encoded)
    return stored.storage_key, stored.stored_sha256


def read_artifact(job: ProcessingJob) -> dict[str, Any]:
    if not job.result_storage_key or not job.result_storage_sha256:
        raise ValueError("Processing job has no completed result artifact.")
    payload = read_private(
        _namespace(job),
        f"model-result-processing-{job.id}",
        job.result_storage_key,
        job.result_storage_sha256,
    )
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError("Processing result must be a JSON object.")
    return value


def parent_artifact(job: ProcessingJob) -> dict[str, Any]:
    if job.parent_job is None or job.parent_job.state != "succeeded":
        raise ValueError("Processing stage requires a successful parent artifact.")
    return read_artifact(job.parent_job)
