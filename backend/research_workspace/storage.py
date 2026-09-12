"""Immutable, content-addressed research artifacts, independent of Django storage."""

import csv
import hashlib
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def put_object(root: Path, data: bytes) -> str:
    sha = digest(data)
    path = root / "objects" / sha[:2] / sha
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        try:
            os.link(temporary, path)
        except FileExistsError:
            if digest(path.read_bytes()) != sha:
                raise ValueError(f"Corrupt existing object: {sha}") from None
    finally:
        temporary.unlink()
    return sha


def read_object(root: Path, sha: str) -> bytes:
    if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        raise ValueError("Invalid SHA-256")
    content = (root / "objects" / sha[:2] / sha).read_bytes()
    if digest(content) != sha:
        raise ValueError(f"Corrupt object: {sha}")
    return content


def write_json(path: Path, value: Any) -> None:
    """Atomic replace for derived reports, never for preserved originals."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    """Review export; neutralise spreadsheet formulas in externally supplied labels/URLs."""
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        safe = {}
        for field in fields:
            value = row.get(field)
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                value = "'" + value
            safe[field] = value
        writer.writerow(safe)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stream.getvalue())
