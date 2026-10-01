"""Measure frozen queries against exact raw spans; no reference-guided ranking."""

import hashlib
import json
import math
import os
import shutil
import statistics
import time
from collections import Counter
from pathlib import Path

import numpy as np
import onnxruntime as ort
from apps.adviser_v2.embedding import embed_texts, policy_index_version, qualified_embedding_status
from apps.adviser_v2.evidence_retrieval import BM25, RawChunk, fts_rank, pack, token_count
from apps.adviser_v2.models import PolicySearchChunk
from django.conf import settings
from pgvector.django import CosineDistance
from tokenizers import Tokenizer

ROOT = Path(settings.BASE_DIR).parent
STATE = Path(settings.COVERGUIDE_REPORT_ROOT) / "retrieval-benchmark"
CORPUS = json.loads((STATE / "corpus.json").read_text())
QUERIES = json.loads((ROOT / "research/pilots/star/retrieval-queries.json").read_text())["queries"]
MINILM = Path("/home/akhilesh/.local/state/coverguide-research/20260925/models/minilm")


def resource_check():
    if shutil.disk_usage(STATE).free < 3 * 1024**3:
        raise RuntimeError("Hard stop: disk free space below 3 GB")


def reranker():
    manifest = json.loads((MINILM / "manifest.json").read_text())
    for name, metadata in manifest["files"].items():
        assert hashlib.sha256((MINILM / name).read_bytes()).hexdigest() == metadata["sha256"]
    tokenizer = Tokenizer.from_file(str(MINILM / "tokenizer.json"))
    tokenizer.enable_truncation(max_length=512, strategy="only_second")
    tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
    options = ort.SessionOptions()
    options.intra_op_num_threads, options.inter_op_num_threads = 4, 1
    session = ort.InferenceSession(
        str(MINILM / "model.onnx"), options, providers=["CPUExecutionProvider"]
    )
    return tokenizer, session


def minilm_rank(query, ranked, tokenizer, session):
    head = ranked[:20]
    names = {i.name for i in session.get_inputs()}
    scores = []
    for i in range(0, len(head), 4):
        batch = head[i : i + 4]
        encoded = tokenizer.encode_batch([(query, c.text) for c in batch])
        feeds = {
            "input_ids": np.asarray([e.ids for e in encoded], dtype=np.int64),
            "attention_mask": np.asarray([e.attention_mask for e in encoded], dtype=np.int64),
            "token_type_ids": np.asarray([e.type_ids for e in encoded], dtype=np.int64),
        }
        logits = session.run(None, {k: v for k, v in feeds.items() if k in names})[0].reshape(-1)
        scores.extend(zip(logits.tolist(), batch, strict=True))
    return [c for _score, c in sorted(scores, key=lambda pair: (-pair[0], pair[1].id))] + ranked[
        20:
    ]


def covered(reference, packet):
    intervals = sorted(
        (s["start"], s["end"])
        for c in packet.chunks
        for s in c.segments
        if s["page_span_id"] == reference["page_span_id"]
    )
    cursor = reference["start"]
    for start, end in intervals:
        if start <= cursor < end:
            cursor = end
    return cursor >= reference["end"]


def pageindex_ranking(plan, query, kind):
    key = plan["plan"] + ":" + query["criterion"] + ":" + kind
    path = STATE / "pageindex-search" / (hashlib.sha256(key.encode()).hexdigest() + ".json")
    if not path.exists():
        return None, None
    result = json.loads(path.read_text())
    assert result["query"] == query[kind]
    pages = {p["evidence_span_id"]: p for p in plan["pages"]}
    chunks = []
    for key in result["page_span_ids"]:
        p = pages[key]
        segment = {
            "page_span_id": key,
            "document_key": p["document_key"],
            "page": p["physical_page"],
            "start": 0,
            "end": len(p["passage"]),
            "text": p["passage"],
            "document_start": p["document_char_start"],
            "document_end": p["document_char_start"] + len(p["passage"]),
        }
        chunks.append(
            RawChunk(
                key,
                plan["policy_version_id"],
                p["document_version_id"],
                p["passage"],
                token_count(p["passage"]),
                (segment,),
            )
        )
    return chunks, result["wall_ms"]


def measure():
    # Limit CPU concurrency, not the model, tokenizer, vector contract or qualification.
    if hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    dense_ok, reason, qualification = qualified_embedding_status()
    metadata = {
        "current_arm": "FTS + qualified BGE-M3 dense RRF" if dense_ok else "FTS only",
        "dense_reason": reason,
        "dense_index_version": policy_index_version(qualification) if qualification else None,
        "tokenizer": "o200k_base",
        "chunk_size": 1024,
        "overlap": 128,
        "decision_metric": "39 cells complete for BOTH fixed and customer queries",
        "minilm_note": "Top 20 only, 512-token scoring window; original chunks and untouched tail enter packets.",
    }
    previous_metadata = STATE / "metadata.json"
    if previous_metadata.exists():
        previous = json.loads(previous_metadata.read_text())
        if previous.get("dense_index_version") != metadata["dense_index_version"]:
            raise ValueError("Cannot resume measurements with a different dense qualification.")
        metadata["dense_index_ms"] = previous.get("dense_index_ms", {})
    tokenizer, session = reranker()
    for plan in CORPUS["plans"]:
        chunks = [RawChunk(**{**c, "segments": tuple(c["segments"])}) for c in plan["chunks"]]
        bm25 = BM25(chunks)
        if dense_ok:
            print("Indexing qualified dense control:", plan["plan"], flush=True)
            started = time.perf_counter()
            for c in chunks:
                row = PolicySearchChunk.objects.get(pk=c.id)
                if row.embedding is None:
                    row.embedding = embed_texts([c.text])[0]
                    row.save(update_fields=["embedding"])
                resource_check()
            metadata.setdefault("dense_index_ms", {}).setdefault(
                plan["plan"], round((time.perf_counter() - started) * 1000)
            )
        for query in (q for q in QUERIES if q["plan"] == plan["plan"]):
            for kind in ("fixed", "customer"):
                key = plan["plan"] + ":" + query["criterion"] + ":" + kind
                path = STATE / "measurements" / (hashlib.sha256(key.encode()).hexdigest() + ".json")
                existing = json.loads(path.read_text()) if path.exists() else {}
                question = query[kind]
                arms = {}
                if "bm25" not in existing:
                    started = time.perf_counter()
                    ranked = bm25.rank(question)
                    elapsed = (time.perf_counter() - started) * 1000
                    arms["bm25"] = (ranked, elapsed)
                    arms["minilm"] = (
                        minilm_rank(question, ranked, tokenizer, session),
                        (time.perf_counter() - started) * 1000,
                    )
                    started = time.perf_counter()
                    lexical = fts_rank(question, chunks)[:96]
                    if dense_ok:
                        vector = embed_texts([question])[0]
                        by_id = {c.id: c for c in chunks}
                        rows = (
                            PolicySearchChunk.objects.filter(id__in=by_id)
                            .annotate(distance=CosineDistance("embedding", vector))
                            .order_by("distance", "id")[:96]
                        )
                        semantic = [by_id[str(r.id)] for r in rows]
                        scores = Counter()
                        for ranking in (lexical, semantic):
                            for rank, c in enumerate(ranking, 1):
                                scores[c.id] += 1 / (60 + rank)
                        current = [by_id[i] for i in sorted(scores, key=lambda i: (-scores[i], i))]
                    else:
                        current = lexical
                    arms["current"] = (current, (time.perf_counter() - started) * 1000)
                if "pageindex" not in existing:
                    pi, elapsed = pageindex_ranking(plan, query, kind)
                    if pi is not None:
                        arms["pageindex"] = (pi, elapsed)
                for arm, (ranking, latency) in arms.items():
                    rows = []
                    references = {r["id"]: r for r in plan["references"][query["criterion"]]}
                    for budget in (8000, 16000):
                        packet = pack(plan["policy_version_id"], ranking, budget=budget, method=arm)
                        missed = [r["id"] for r in references.values() if not covered(r, packet)]
                        rows.append(
                            {
                                "plan": plan["plan"],
                                "criterion": query["criterion"],
                                "query_kind": kind,
                                "query": question,
                                "table_heavy": query["table_heavy"],
                                "arm": arm,
                                "budget": budget,
                                "reference_count": len(references),
                                "recalled": len(references) - len(missed),
                                "missing": missed,
                                "complete": not missed,
                                "wrong_plan_hits": sum(
                                    c.policy_version_id != plan["policy_version_id"]
                                    for c in packet.chunks
                                ),
                                "latency_ms": latency,
                                "packet_tokens": packet.tokens,
                                "omitted_chunks": packet.omitted_chunks,
                                "chunk_ids": [c.id for c in packet.chunks],
                            }
                        )
                    existing[arm] = rows
                path.parent.mkdir(exist_ok=True)
                path.write_text(json.dumps(existing))
                print("Measured", key, ",".join(existing), flush=True)
    (STATE / "metadata.json").write_text(json.dumps(metadata, indent=2))


def summarize():
    rows = [
        row
        for p in sorted((STATE / "measurements").glob("*.json"))
        for arm in json.loads(p.read_text()).values()
        for row in arm
    ]
    summaries = {}
    for arm in ("current", "bm25", "minilm", "pageindex"):
        summaries[arm] = {}
        for budget in (8000, 16000):
            subset = [r for r in rows if r["arm"] == arm and r["budget"] == budget]
            cells = {}
            for r in subset:
                cells.setdefault((r["plan"], r["criterion"]), []).append(r)
            timings = sorted(r["latency_ms"] for r in subset)
            summaries[arm][budget] = {
                "query_count": len(subset),
                "recalled": sum(r["recalled"] for r in subset),
                "reference_count": sum(r["reference_count"] for r in subset),
                "complete_queries": sum(r["complete"] for r in subset),
                "complete_cells": sum(
                    len(v) == 2 and all(r["complete"] for r in v) for v in cells.values()
                ),
                "wrong_plan_hits": sum(r["wrong_plan_hits"] for r in subset),
                "p50_ms": statistics.median(timings) if timings else None,
                "p95_ms": timings[math.ceil(0.95 * len(timings)) - 1] if timings else None,
                "table_complete_queries": sum(r["complete"] for r in subset if r["table_heavy"]),
                "table_queries": sum(r["table_heavy"] for r in subset),
            }
    # Simplicity order is frozen: BM25, current FTS/dense, MiniLM, PageIndex.
    eligible = [
        a
        for a in ("bm25", "current", "minilm", "pageindex")
        if summaries[a][16000]["query_count"] == 78
    ]
    winner = eligible[0] if eligible else None
    for arm in eligible[1:]:
        gain = summaries[arm][16000]["complete_cells"] - summaries[winner][16000]["complete_cells"]
        if gain > 0 and (
            (gain >= 2 and arm != "pageindex")
            or summaries[arm][8000]["complete_cells"] >= summaries[winner][8000]["complete_cells"]
        ):
            winner = arm
    result = {"winner": winner, "summaries": summaries, "rows": rows}
    (STATE / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"winner": winner, "summaries": summaries}, indent=2))


measure()
summarize()
