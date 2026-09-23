#!/usr/bin/env python3
"""Run the synthetic CoverGuide gateway rotation and no-log acceptance check."""

from __future__ import annotations

import os
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "http://127.0.0.1:20128"
MODEL = "gemini/gemini-3.5-flash-lite"
DATABASE = Path("/home/akhilesh/.local/share/omniroute/storage.sqlite")
ARTIFACTS = Path("/home/akhilesh/.local/share/omniroute/call_logs")


def _database_state() -> tuple[set[str], int, int, set[tuple[str, int, int]]]:
    with sqlite3.connect(f"file:{DATABASE}?mode=ro", uri=True) as connection:
        gemini_ids = {
            row[0]
            for row in connection.execute(
                "SELECT id FROM provider_connections WHERE provider = 'gemini' AND is_active = 1"
            )
        }
        latest_call_rowid = connection.execute(
            "SELECT COALESCE(MAX(rowid), 0) FROM call_logs"
        ).fetchone()[0]
        details = connection.execute(
            "SELECT COUNT(*) FROM request_detail_logs details "
            "JOIN call_logs calls ON calls.id = details.call_log_id "
            "WHERE calls.api_key_name = 'CoverGuide'"
        ).fetchone()[0]
    artifacts = (
        {
            (str(path.relative_to(ARTIFACTS)), path.stat().st_size, path.stat().st_mtime_ns)
            for path in ARTIFACTS.rglob("*")
            if path.is_file()
        }
        if ARTIFACTS.exists()
        else set()
    )
    return gemini_ids, latest_call_rowid, details, artifacts


def _new_logs_are_metadata_only(after_rowid: int) -> bool:
    with sqlite3.connect(f"file:{DATABASE}?mode=ro", uri=True) as connection:
        rows = connection.execute(
            "SELECT has_request_body, has_response_body, detail_state, artifact_relpath "
            "FROM call_logs WHERE rowid > ? AND api_key_name = 'CoverGuide'",
            (after_rowid,),
        ).fetchall()
    return bool(rows) and all(
        request_body == 0 and response_body == 0 and detail_state == "none" and not artifact_path
        for request_body, response_body, detail_state, artifact_path in rows
    )


def _has_output(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if (
                isinstance(content, dict)
                and content.get("type") == "output_text"
                and str(content.get("text", "")).strip()
            ):
                return True
    return False


def _selected_connection(response: httpx.Response) -> str:
    connection_id = response.headers.get("X-OmniRoute-Selected-Connection-Id", "")
    if connection_id:
        return connection_id

    correlation_id = response.headers.get("X-Correlation-Id", "")
    if not correlation_id:
        return ""
    with sqlite3.connect(f"file:{DATABASE}?mode=ro", uri=True) as connection:
        row = connection.execute(
            "SELECT connection_id FROM call_logs "
            "WHERE correlation_id = ? AND api_key_name = 'CoverGuide' "
            "ORDER BY rowid DESC LIMIT 1",
            (correlation_id,),
        ).fetchone()
    return str(row[0]) if row and row[0] else ""


def main() -> int:
    api_key = os.environ.get("OMNIROUTE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OMNIROUTE_API_KEY is required in the process environment")

    expected_ids, before_rowid, before_details, before_artifacts = _database_state()
    if len(expected_ids) != 5:
        raise RuntimeError(f"Expected five active Gemini connections; found {len(expected_ids)}")

    selected: list[str] = []
    with httpx.Client(base_url=BASE_URL, timeout=120, trust_env=False) as client:
        for sequence in range(10):
            response = client.post(
                "/v1/responses",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": MODEL,
                    "input": f"Synthetic gateway canary {sequence + 1}: reply with OK.",
                    "temperature": 0,
                    "max_output_tokens": 128,
                },
            )
            if response.is_error:
                raise RuntimeError(
                    f"Synthetic call {sequence + 1} returned HTTP {response.status_code}"
                )
            if not _has_output(response.json()):
                raise RuntimeError(f"Synthetic call {sequence + 1} returned no model output")
            connection_id = _selected_connection(response)
            if connection_id not in expected_ids:
                raise RuntimeError(
                    f"Synthetic call {sequence + 1} did not report an allowed connection"
                )
            selected.append(connection_id)

    after_ids, _after_rowid, after_details, after_artifacts = _database_state()
    if after_ids != expected_ids:
        raise RuntimeError("Gemini connection set changed during the acceptance run")
    distribution = Counter(selected)
    if set(distribution) != expected_ids or set(distribution.values()) != {2}:
        safe_counts = {connection_id[:8]: count for connection_id, count in distribution.items()}
        raise RuntimeError(f"Round-robin distribution was not exactly two each: {safe_counts}")
    if after_details != before_details or not _new_logs_are_metadata_only(before_rowid):
        raise RuntimeError("The no-log key stored more than administrative call metadata")
    if after_artifacts != before_artifacts:
        raise RuntimeError("The no-log canary changed a request-artifact file")

    print("Ten synthetic calls succeeded; each of five Gemini connections handled exactly two.")
    print(
        "Only administrative call metadata was stored; request/response bodies and artifacts were not."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
