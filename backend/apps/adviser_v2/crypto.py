"""Versioned AES-256-GCM encryption and keyed commitments.

Keys are supplied only through server settings. Ciphertexts contain a non-secret key
identifier so old records remain readable during rotation; HMAC verification tries the
configured ring because the approved commitment columns contain only a 64-character
digest.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from functools import lru_cache
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_MAGIC = b"CG2\x00"
_NONCE_BYTES = 12


def _fallback_key(label: str) -> bytes:
    if not settings.DEBUG:
        raise ImproperlyConfigured(
            f"{label} must be configured with an explicit 32-byte server-only key."
        )
    return hashlib.sha256(f"{label}:{settings.SECRET_KEY}".encode()).digest()


def _decode_ring(raw: str, setting_name: str) -> tuple[str, dict[str, bytes]]:
    if not raw.strip():
        return "local-v1", {"local-v1": _fallback_key(setting_name)}
    ring: dict[str, bytes] = {}
    for entry in raw.split(","):
        try:
            key_id, encoded = entry.strip().split(":", 1)
            padding = "=" * (-len(encoded) % 4)
            key = base64.urlsafe_b64decode(encoded + padding)
        except (ValueError, TypeError) as exc:
            raise ImproperlyConfigured(f"{setting_name} contains an invalid key entry.") from exc
        if not key_id or len(key_id.encode()) > 64 or len(key) != 32 or key_id in ring:
            raise ImproperlyConfigured(
                f"{setting_name} key IDs must be unique and every decoded key must be 32 bytes."
            )
        ring[key_id] = key
    return next(iter(ring)), ring


@lru_cache(maxsize=1)
def encryption_key_ring() -> tuple[str, dict[str, bytes]]:
    return _decode_ring(settings.COVERGUIDE_ENCRYPTION_KEYS, "COVERGUIDE_ENCRYPTION_KEYS")


@lru_cache(maxsize=1)
def commitment_key_ring() -> tuple[str, dict[str, bytes]]:
    return _decode_ring(settings.COVERGUIDE_COMMITMENT_KEYS, "COVERGUIDE_COMMITMENT_KEYS")


def encrypt_bytes(value: bytes, *, associated_data: bytes) -> bytes:
    key_id, ring = encryption_key_ring()
    encoded_id = key_id.encode()
    nonce = os.urandom(_NONCE_BYTES)
    ciphertext = AESGCM(ring[key_id]).encrypt(nonce, value, associated_data)
    return _MAGIC + bytes([len(encoded_id)]) + encoded_id + nonce + ciphertext


def decrypt_bytes(value: bytes, *, associated_data: bytes) -> bytes:
    if not value.startswith(_MAGIC) or len(value) < len(_MAGIC) + 1 + _NONCE_BYTES + 16:
        raise ValueError("The encrypted value has an invalid envelope.")
    id_length = value[len(_MAGIC)]
    id_start = len(_MAGIC) + 1
    id_end = id_start + id_length
    key_id = value[id_start:id_end].decode()
    nonce = value[id_end : id_end + _NONCE_BYTES]
    ciphertext = value[id_end + _NONCE_BYTES :]
    _, ring = encryption_key_ring()
    key = ring.get(key_id)
    if key is None:
        raise ValueError("The encrypted value references an unavailable key version.")
    return AESGCM(key).decrypt(nonce, ciphertext, associated_data)


def encrypt_text(value: str, *, associated_data: bytes) -> str:
    payload = encrypt_bytes(value.encode("utf-8"), associated_data=associated_data)
    return "cg2$" + base64.urlsafe_b64encode(payload).decode()


def decrypt_text(value: str, *, associated_data: bytes) -> str:
    if not value.startswith("cg2$"):
        raise ValueError("The encrypted text has an invalid envelope.")
    payload = base64.urlsafe_b64decode(value[4:].encode())
    return decrypt_bytes(payload, associated_data=associated_data).decode("utf-8")


def canonical_bytes(value: str | bytes | Any) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def commitment(value: str | bytes | Any) -> str:
    key_id, ring = commitment_key_ring()
    return hmac.new(ring[key_id], canonical_bytes(value), hashlib.sha256).hexdigest()


def commitment_matches(expected: str, value: str | bytes | Any) -> bool:
    payload = canonical_bytes(value)
    _, ring = commitment_key_ring()
    return any(
        hmac.compare_digest(expected, hmac.new(key, payload, hashlib.sha256).hexdigest())
        for key in ring.values()
    )
