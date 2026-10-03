"""Budget original selected-variant table proof alongside H-retrieved prose."""

import json
import re
from dataclasses import replace

from .answer_scope import TOPICS, canon, question_topic
from .evidence import pack_sections
from .text import token_count


def scoped_packet(packet, scope, question):
    topics = question_topic(question)
    selected = {s.id for s in packet.sections}
    tables, required = [], set()
    for table in scope.table_map.values():
        cells = table["cells"]
        if not any(c["citation"]["section_id"] in selected for c in cells.values()):
            continue
        rows = {
            c["row"]
            for c in cells.values()
            if any(re.search(TOPICS[t], c["text"], re.I) for t in topics)
        }
        if not rows:
            continue
        matrix = table["id"] in scope.matrices
        columns = {
            c["column"]
            for c in cells.values()
            if c["row"] <= 2 and canon(c["text"]) in scope.aliases
        }
        if matrix and not columns:
            continue  # Never manufacture a missing or merged variant header.
        label_columns = [
            c["column"]
            for c in cells.values()
            if c["row"] in rows and any(re.search(TOPICS[t], c["text"], re.I) for t in topics)
        ]
        row_axes = min(label_columns) if label_columns else -1
        kept = {
            k: c
            for k, c in cells.items()
            if (c["row"] in rows or c["row"] <= 2)
            and (not matrix or c["column"] in columns or c["column"] <= row_axes)
        }
        # The source page retains introductions, conditions and footnotes. This
        # projection exposes only the queried rows, never an exhaustive table.
        candidate = {
            **table,
            "cells": kept,
            "projection": "queried rows and original axes; not exhaustive",
        }
        if token_count(json.dumps([*tables, candidate], ensure_ascii=False)) > 5500:
            continue
        tables.append(candidate)
        required.update(c["citation"]["section_id"] for c in kept.values())
        if len(tables) == 2:
            break
    if not tables:
        return packet
    # This is deterministic scope completion within the H packet, not another
    # search/ranking arm. Every added section shares the pinned index edition.
    sections = [scope.sections[k] for k in scope.sections if k in required]
    reserve = token_count(json.dumps(tables, ensure_ascii=False)) + 1000
    text_packet = pack_sections(
        packet.plan_id, [*sections, *packet.sections], budget=14000 - reserve
    )
    result = pack_sections(packet.plan_id, list(text_packet.sections), budget=14000, tables=tables)
    included = {s.id for s in result.sections} | {"table:" + t["id"] for t in result.tables}
    omissions = tuple(
        dict.fromkeys(
            x for p in (packet, text_packet, result) for x in p.omitted_ids if x not in included
        )
    )
    result = replace(result, omitted_ids=omissions)
    actual = token_count(json.dumps(result.evidence(), ensure_ascii=False))
    if actual > 16000:
        return packet  # Keep the prior bounded packet; no invented scope proof.
    return replace(result, tokens=actual, budget=16000)
