"""Content-addressed public storage and owner-scoped encrypted private storage."""

from __future__ import annotations

import hashlib
import os
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

from .crypto import decrypt_bytes, encrypt_bytes


@dataclass(frozen=True)
class StoredObject:
    storage_key: str
    plaintext_sha256: str
    stored_sha256: str
    plaintext_size: int


def _root() -> Path:
    root = Path(settings.COVERGUIDE_V2_STORAGE_ROOT).resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    return root


def _path(storage_key: str) -> Path:
    candidate = (_root() / storage_key).resolve()
    if _root() not in candidate.parents:
        raise ValueError("Invalid storage key.")
    return candidate


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".coverguide-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def store_public(payload: bytes) -> StoredObject:
    digest = hashlib.sha256(payload).hexdigest()
    key = f"public/{digest[:2]}/{digest}"
    path = _path(key)
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise OSError("A public content-addressed object failed its integrity check.")
    if not path.exists():
        _atomic_write(path, payload)
    return StoredObject(key, digest, digest, len(payload))


def store_private(owner_id: uuid.UUID, purpose: str, payload: bytes) -> StoredObject:
    plaintext_digest = hashlib.sha256(payload).hexdigest()
    associated_data = f"{owner_id}:{purpose}".encode()
    encrypted = encrypt_bytes(payload, associated_data=associated_data)
    stored_digest = hashlib.sha256(encrypted).hexdigest()
    key = f"private/{owner_id}/{purpose}/{stored_digest[:2]}/{stored_digest}.cg2"
    path = _path(key)
    if not path.exists():
        _atomic_write(path, encrypted)
    return StoredObject(key, plaintext_digest, stored_digest, len(payload))


def store_model_result(owner_id: uuid.UUID | None, purpose: str, payload: bytes) -> StoredObject:
    """Encrypt a retained model result, including non-customer processing output."""

    namespace = owner_id or uuid.UUID(int=0)
    return store_private(namespace, f"model-result-{purpose}", payload)


def read_public(storage_key: str, expected_sha256: str) -> bytes:
    payload = _path(storage_key).read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise OSError("The public object failed its integrity check.")
    return payload


def read_private(owner_id: uuid.UUID, purpose: str, storage_key: str, stored_sha256: str) -> bytes:
    encrypted = _path(storage_key).read_bytes()
    if hashlib.sha256(encrypted).hexdigest() != stored_sha256:
        raise OSError("The encrypted object failed its integrity check.")
    return decrypt_bytes(encrypted, associated_data=f"{owner_id}:{purpose}".encode())


def delete_private(owner_id: uuid.UUID, storage_key: str) -> bool:
    """Delete one exact owner-scoped ciphertext without accepting broader paths."""

    prefix = f"private/{owner_id}/"
    if not storage_key.startswith(prefix) or not storage_key.endswith(".cg2"):
        raise ValueError("Refusing to delete a storage key outside the exact owner namespace.")
    path = _path(storage_key)
    existed = path.exists()
    path.unlink(missing_ok=True)
    return existed
