"""Attempt pg_textsearch only on the isolated v2 database and record the fallback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import connection


class Command(BaseCommand):
    help = "Qualify pg_textsearch availability without changing the approved GIN schema."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--output", type=Path)

    def handle(self, *args: Any, **options: Any) -> None:
        database = connection.settings_dict
        port = str(database.get("PORT", ""))
        if port != "55449":
            raise CommandError(
                "pg_textsearch qualification is restricted to the isolated PostgreSQL 18 port 55449."
            )
        with connection.cursor() as cursor:
            cursor.execute("SHOW server_version")
            server_version = str(cursor.fetchone()[0])
            cursor.execute(
                "SELECT default_version, installed_version "
                "FROM pg_available_extensions WHERE name = 'pg_textsearch'"
            )
            extension_row = cursor.fetchone()
            cursor.execute("SHOW shared_preload_libraries")
            shared_preloads = {
                item.strip() for item in str(cursor.fetchone()[0]).split(",") if item.strip()
            }
            cursor.execute(
                "SELECT indexdef FROM pg_indexes "
                "WHERE schemaname = 'public' AND indexname = 'v2_policy_search_chunk_ix_1'"
            )
            gin_row = cursor.fetchone()
        available = extension_row is not None
        preloaded = "pg_textsearch" in shared_preloads
        blockers: list[str] = []
        if not available:
            blockers.append("pg_textsearch_not_available_in_pg18_image")
        elif not preloaded:
            blockers.append("pg_textsearch_not_preloaded")
        # The extension is not activated unless every invasive qualification can
        # subsequently be run. Availability/preload alone must never select BM25.
        phases = {
            "availability": "passed" if available else "failed",
            "shared_preload": "passed" if preloaded else "not_run",
            "concurrent_write": "not_run",
            "restart": "not_run",
            "restore": "not_run",
            "index_integrity": "not_run",
        }
        if available and preloaded:
            blockers.append("full_bm25_lifecycle_qualification_not_implemented_for_this_image")
        gin_preserved = bool(gin_row and "using gin" in str(gin_row[0]).lower())
        if not gin_preserved:
            blockers.append("approved_gin_index_not_detected")
        report = {
            "schema_version": 1,
            "database_port": port,
            "server_version": server_version,
            "extension": "pg_textsearch",
            "available": available,
            "default_version": str(extension_row[0]) if extension_row else None,
            "installed_version": str(extension_row[1]) if extension_row else None,
            "preloaded": preloaded,
            "phases": phases,
            "qualified": False,
            "selected_lexical_backend": "postgresql_gin",
            "approved_tsvector_schema_unchanged": gin_preserved,
            "blockers": blockers,
        }
        output: Path = options.get("output") or (
            Path(settings.COVERGUIDE_REPORT_ROOT) / "pg-textsearch-qualification.json"
        )
        output = output.resolve()
        report_root = Path(settings.COVERGUIDE_REPORT_ROOT).resolve()
        if output.parent != report_root:
            raise CommandError(
                "pg_textsearch report must be directly inside COVERGUIDE_REPORT_ROOT."
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.stdout.write(
            self.style.WARNING(
                "pg_textsearch is unavailable or unqualified; PostgreSQL GIN remains selected."
            )
        )
        self.stdout.write(f"Qualification report: {output}")
