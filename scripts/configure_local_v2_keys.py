#!/usr/bin/env python3
"""Create missing local CoverGuide v2 key rings without printing key material."""

from __future__ import annotations

import argparse
import base64
import os
import secrets
from pathlib import Path

KEY_NAMES = ("COVERGUIDE_ENCRYPTION_KEYS", "COVERGUIDE_COMMITMENT_KEYS")


def _new_ring() -> str:
    encoded = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    return f"local-v1:{encoded}"


def configure(
    path: Path,
    *,
    docling_artifacts: Path | None = None,
    tesseract_path: Path | None = None,
    embedding_model: Path | None = None,
    embedding_qualification: Path | None = None,
) -> list[str]:
    source = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = source.splitlines()
    positions: dict[str, int] = {}
    values: dict[str, str] = {}
    for index, line in enumerate(lines):
        name, separator, value = line.partition("=")
        if separator:
            positions[name] = index
            if name in KEY_NAMES:
                values[name] = value.strip()

    changed: list[str] = []
    for name in KEY_NAMES:
        existing = values.get(name, "")
        if existing and "replace-with" not in existing:
            continue
        replacement = f"{name}={_new_ring()}"
        if name in positions:
            lines[positions[name]] = replacement
        else:
            lines.append(replacement)
        changed.append(name)

    if docling_artifacts is not None:
        name = "COVERGUIDE_DOCLING_ARTIFACTS_PATH"
        replacement = f"{name}={docling_artifacts.resolve()}"
        if name in positions:
            if lines[positions[name]] != replacement:
                lines[positions[name]] = replacement
                changed.append(name)
        else:
            lines.append(replacement)
            changed.append(name)

    if tesseract_path is not None:
        name = "COVERGUIDE_TESSERACT_PATH"
        replacement = f"{name}={tesseract_path.resolve()}"
        if name in positions:
            if lines[positions[name]] != replacement:
                lines[positions[name]] = replacement
                changed.append(name)
        else:
            lines.append(replacement)
            changed.append(name)

    if embedding_model is not None:
        name = "COVERGUIDE_EMBEDDING_MODEL_PATH"
        replacement = f"{name}={embedding_model.resolve()}"
        if name in positions:
            if lines[positions[name]] != replacement:
                lines[positions[name]] = replacement
                changed.append(name)
        else:
            lines.append(replacement)
            changed.append(name)

    if embedding_qualification is not None:
        name = "COVERGUIDE_EMBEDDING_QUALIFICATION_PATH"
        replacement = f"{name}={embedding_qualification.resolve()}"
        if name in positions:
            if lines[positions[name]] != replacement:
                lines[positions[name]] = replacement
                changed.append(name)
        else:
            lines.append(replacement)
            changed.append(name)

    if changed:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--docling-artifacts", type=Path)
    parser.add_argument("--tesseract-path", type=Path)
    parser.add_argument("--embedding-model", type=Path)
    parser.add_argument("--embedding-qualification", type=Path)
    args = parser.parse_args()
    changed = configure(
        args.env_file.resolve(),
        docling_artifacts=args.docling_artifacts,
        tesseract_path=args.tesseract_path,
        embedding_model=args.embedding_model,
        embedding_qualification=args.embedding_qualification,
    )
    if changed:
        print("Configured local v2 settings: " + ", ".join(changed))
    else:
        print("Local v2 key rings were already configured; no changes made.")


if __name__ == "__main__":
    main()
