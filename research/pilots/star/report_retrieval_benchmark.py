"""Publish all frozen-query measurements and actual PageIndex relay usage."""

import json
from pathlib import Path

from django.conf import settings

ROOT = Path(settings.BASE_DIR).parent
STATE = Path(settings.COVERGUIDE_REPORT_ROOT) / "retrieval-benchmark"
result = json.loads((STATE / "results.json").read_text())
corpus = json.loads((STATE / "corpus.json").read_text())
metadata = json.loads((STATE / "metadata.json").read_text())
calls = [json.loads(line) for line in (STATE / "pageindex-calls.jsonl").read_text().splitlines()]
usage = {}
for phase in ("index", "search"):
    subset = [c for c in calls if c["phase"] == phase]
    usage[phase] = {
        "calls": len(subset),
        "failures": sum(c.get("status") != "completed" for c in subset),
        "input_tokens": sum((c.get("usage") or {}).get("input_tokens", 0) for c in subset),
        "cached_input_tokens": sum(
            (c.get("usage") or {}).get("input_tokens_details", {}).get("cached_tokens", 0)
            for c in subset
        ),
        "reasoning_tokens": sum(
            (c.get("usage") or {}).get("output_tokens_details", {}).get("reasoning_tokens", 0)
            for c in subset
        ),
        "output_tokens": sum((c.get("usage") or {}).get("output_tokens", 0) for c in subset),
        "summed_call_wall_ms": sum(c.get("wall_ms", 0) for c in subset),
    }
result["pageindex_usage"] = usage
result["metadata"] = metadata
output = ROOT / "output"
(output / "star-retrieval-benchmark.json").write_text(json.dumps(result, indent=2))
refs = {
    r["id"]: (p["plan"], r)
    for p in corpus["plans"]
    for rows in p["references"].values()
    for r in rows
}
lines = [
    "# Star plan retrieval benchmark",
    "",
    f"Winner under the frozen rule: **{result['winner']}**. Plain prepared facts remain the source of the comparison table; this benchmark selects retrieval for other questions.",
    "",
    f"Reference set: 39 reviewed cells; {len(refs)} distinct stored clause spans, not the brief's older count of 231. There are 273 cell-span memberships (some spans support multiple criteria), evaluated against 78 questions frozen in `research/pilots/star/retrieval-queries.json` before measurements.",
    "",
    "Caveat: the reference spans came from whole-bundle extraction. This measures retrieval against our own reviewed facts, not an independent gold set.",
    "",
    "## Method and decision",
    "",
    "Every arm searches each exact applicable plan bundle separately. Excluded optional covers and the reference-only Assure expense sheet are absent. Original Poppler `-raw` text, physical page numbers and character spans are preserved. No OCR, layout text or generated chunk prefix is used. Prospectuses are in the retrieval corpus.",
    "",
    "BM25 is genuine Okapi (k1=1.5, b=.75, positive Robertson IDF), with o200k_base 1,024-token chunks and 128-token overlap. Packets keep whole chunks in rank order, skip any that do not fit, and report every omitted chunk. PageIndex keeps whole returned raw pages. No source text is silently shortened.",
    "",
    f"Current arm: {metadata['current_arm']}. It uses the qualified BGE-M3 model, positive-rank Postgres FTS and RRF (k=60). The same native raw chunks are used for an equal-source comparison. Local dense vectors were built before timing queries. Qualification identity: `{metadata.get('dense_index_version')}`.",
    "",
    "MiniLM uses the locally pinned `cross-encoder/ms-marco-MiniLM-L6-v2` (revision `233902d25c440f23af6f7d6e94d2946bac0bee0a`). Only the BM25 top 20 are reordered; its remaining tail stays unchanged. Its 512-token model scoring window truncates the scoring input, not the original source chunk placed in the packet.",
    "",
    "PageIndex uses its MIT local classic tree builder at revision `6d23caf416858f2ca136840305d1f479a86f6ef7` in a separate research venv. Trees are cached by PDF SHA-256, with raw-text SHA and SDK revision checked. Its local page-list interface receives preserved Poppler pages; reasoning search selects ranked node IDs and maps them back to the physical raw pages. Relay: loopback CLIProxyAPI, `gpt-5.6-sol`, low reasoning, 8,192 output tokens, at most two concurrent calls. No PageIndex Cloud or paid API key.",
    "",
    "The primary decision counts a cell only when **both** its fixed and customer query contain **every** reference span. The most complete cells at 16k wins; a gain under two cells, or PageIndex, must not lose at 8k. Ties use the frozen simplicity order: BM25, current FTS+dense, MiniLM, PageIndex. All 78 query results are also shown separately.",
    "",
    "Latency is ranking/search wall time: BM25 scoring; FTS+dense query embedding and DB search; BM25 plus MiniLM scoring; or PageIndex reasoning search. Corpus loading/index construction and common packet packing are excluded from query latency. PageIndex indexing calls are included in the cost table below. Measurements are warm local runs, not a production latency guarantee.",
    "",
    "## Aggregate results",
    "",
    "| Arm | Budget | Span recall | Complete queries / 78 | Complete cells / 39 | Wrong-plan hits | p50 ms | p95 ms | Table queries complete / 18 |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
]
for arm, budgets in result["summaries"].items():
    for budget, s in budgets.items():
        recall = (
            f"{s['recalled']}/{s['reference_count']} ({s['recalled'] / s['reference_count']:.1%})"
            if s["reference_count"]
            else "Not completed"
        )

        def number(n):
            return f"{n:.1f}" if n is not None else "—"

        lines.append(
            f"| {arm} | {budget} | {recall} | {s['complete_queries']} | {s['complete_cells']} | {s['wrong_plan_hits']} | {number(s['p50_ms'])} | {number(s['p95_ms'])} | {s['table_complete_queries']} |"
        )
lines += [
    "",
    "Table-heavy cells are room category, maternity and newborn, across all three plans and both query styles. Low complete-cell rates are visible retrieval limitations; they do not invalidate the separately reviewed 39 prepared facts.",
    "",
    "## PageIndex call cost and failures",
    "",
    "| Phase | Actual calls | Relay failures | Input tokens | Cached input | Reasoning | Output tokens | Summed call seconds |",
    "|---|---:|---:|---:|---:|---:|---:|---:|",
]
for phase, s in usage.items():
    lines.append(
        "| "
        + phase
        + " | "
        + " | ".join(
            str(s[k])
            for k in (
                "calls",
                "failures",
                "input_tokens",
                "cached_input_tokens",
                "reasoning_tokens",
                "output_tokens",
            )
        )
        + f" | {s['summed_call_wall_ms'] / 1000:.1f} |"
    )
lines += [
    "",
    "The first indexing run stopped because the local adapter returned `stop` while PageIndex expects `finished`. The adapter was corrected and successful calls cached before resuming. All actual calls from that failed run remain included above. Token usage is the relay-reported amount; no dollar estimate is invented. Other arms make zero LLM calls per query (dense and MiniLM run locally).",
    "",
    "## Every cell",
    "",
    "Each entry is recalled spans / reference spans for **fixed; customer** queries. An incomplete fraction is a failure. PageIndex absent measurements are explicitly marked.",
    "",
    "| Plan | Criterion | Current 8k | Current 16k | BM25 8k | BM25 16k | MiniLM 8k | MiniLM 16k | PageIndex 8k | PageIndex 16k |",
    "|---|---|---|---|---|---|---|---|---|---|",
]
lookup = {
    (r["plan"], r["criterion"], r["arm"], r["budget"], r["query_kind"]): r for r in result["rows"]
}
for plan in corpus["plans"]:
    for criterion in plan["references"]:
        cells = []
        for arm in ("current", "bm25", "minilm", "pageindex"):
            for budget in (8000, 16000):
                values = []
                for kind in ("fixed", "customer"):
                    row = lookup.get((plan["plan"], criterion, arm, budget, kind))
                    values.append(
                        f"{row['recalled']}/{row['reference_count']}" if row else "not completed"
                    )
                cells.append("; ".join(values))
        lines.append("| " + plan["plan"] + " | " + criterion + " | " + " | ".join(cells) + " |")
lines += [
    "",
    "## Every failed query/packet",
    "",
    "Missing span IDs below resolve to the full IDs and exact source positions in the reference map. The adjacent JSON preserves all packet chunk IDs, budgets, omission counts and per-query latencies, including successes.",
    "",
    "| Plan / criterion | Arm | Budget | Query | Missing span IDs |",
    "|---|---|---:|---|---|",
]
for row in sorted(
    result["rows"],
    key=lambda r: (r["plan"], r["criterion"], r["arm"], r["budget"], r["query_kind"]),
):
    if row["missing"]:
        lines.append(
            f"| {row['plan']} / {row['criterion']} | {row['arm']} | {row['budget']} | {row['query_kind']} | {', '.join(i[:8] for i in row['missing'])} |"
        )
lines += [
    "",
    "## Reference map",
    "",
    "| Span ID | Plan | Document / physical page | Raw page span | Characters [start, end) |",
    "|---|---|---|---|---|",
]
assert len({i[:8] for i in refs}) == len(refs)
pages = {p["evidence_span_id"]: p for plan in corpus["plans"] for p in plan["pages"]}
for identifier, (plan, ref) in sorted(refs.items()):
    page = pages[ref["page_span_id"]]
    lines.append(
        f"| {identifier} | {plan} | {page['document_key']} / {page['physical_page']} | {ref['page_span_id']} | [{ref['start']}, {ref['end']}) |"
    )
(output / "star-retrieval-benchmark.md").write_text("\n".join(lines) + "\n")
print(json.dumps({"winner": result["winner"], "pageindex_usage": usage}, indent=2))
