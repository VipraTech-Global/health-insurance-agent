# Star plan retrieval benchmark

Winner under the frozen rule: **pageindex**. Plain prepared facts remain the source of the comparison table; this benchmark selects retrieval for other questions.

Reference set: 39 reviewed cells; 236 distinct stored clause spans, not the brief's older count of 231. There are 273 cell-span memberships (some spans support multiple criteria), evaluated against 78 questions frozen in `research/pilots/star/retrieval-queries.json` before measurements.

Caveat: the reference spans came from whole-bundle extraction. This measures retrieval against our own reviewed facts, not an independent gold set.

## Method and decision

Every arm searches each exact applicable plan bundle separately. Excluded optional covers and the reference-only Assure expense sheet are absent. Original Poppler `-raw` text, physical page numbers and character spans are preserved. No OCR, layout text or generated chunk prefix is used. Prospectuses are in the retrieval corpus.

BM25 is genuine Okapi (k1=1.5, b=.75, positive Robertson IDF), with o200k_base 1,024-token chunks and 128-token overlap. Packets keep whole chunks in rank order, skip any that do not fit, and report every omitted chunk. PageIndex keeps whole returned raw pages. No source text is silently shortened.

Current arm: FTS + qualified BGE-M3 dense RRF. It uses the qualified BGE-M3 model, positive-rank Postgres FTS and RRF (k=60). The same native raw chunks are used for an equal-source comparison. Local dense vectors were built before timing queries. Qualification identity: `bge-m3-fp32-onnx-1024+postgres-gin/1:1dc736180fd8e5894c98f74d057fc15ca0edf20a3491d2ce0a080c516b60a89e`.

MiniLM uses the locally pinned `cross-encoder/ms-marco-MiniLM-L6-v2` (revision `233902d25c440f23af6f7d6e94d2946bac0bee0a`). Only the BM25 top 20 are reordered; its remaining tail stays unchanged. Its 512-token model scoring window truncates the scoring input, not the original source chunk placed in the packet.

PageIndex uses its MIT local classic tree builder at revision `6d23caf416858f2ca136840305d1f479a86f6ef7` in a separate research venv. Trees are cached by PDF SHA-256, with raw-text SHA and SDK revision checked. Its local page-list interface receives preserved Poppler pages; reasoning search selects ranked node IDs and maps them back to the physical raw pages. Relay: loopback CLIProxyAPI, `gpt-5.6-sol`, low reasoning, 8,192 output tokens, at most two concurrent calls. No PageIndex Cloud or paid API key.

The primary decision counts a cell only when **both** its fixed and customer query contain **every** reference span. The most complete cells at 16k wins; a gain under two cells, or PageIndex, must not lose at 8k. Ties use the frozen simplicity order: BM25, current FTS+dense, MiniLM, PageIndex. All 78 query results are also shown separately.

Latency is ranking/search wall time: BM25 scoring; FTS+dense query embedding and DB search; BM25 plus MiniLM scoring; or PageIndex reasoning search. Corpus loading/index construction and common packet packing are excluded from query latency. PageIndex indexing calls are included in the cost table below. Measurements are warm local runs, not a production latency guarantee.

## Aggregate results

| Arm | Budget | Span recall | Complete queries / 78 | Complete cells / 39 | Wrong-plan hits | p50 ms | p95 ms | Table queries complete / 18 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| current | 8000 | 298/546 (54.6%) | 14 | 3 | 0 | 293.8 | 511.6 | 5 |
| current | 16000 | 362/546 (66.3%) | 23 | 6 | 0 | 293.8 | 511.6 | 7 |
| bm25 | 8000 | 312/546 (57.1%) | 19 | 3 | 0 | 1.8 | 5.5 | 3 |
| bm25 | 16000 | 402/546 (73.6%) | 33 | 10 | 0 | 1.8 | 5.5 | 7 |
| minilm | 8000 | 256/546 (46.9%) | 13 | 3 | 0 | 2785.2 | 3960.4 | 4 |
| minilm | 16000 | 370/546 (67.8%) | 23 | 4 | 0 | 2785.2 | 3960.4 | 6 |
| pageindex | 8000 | 417/546 (76.4%) | 35 | 15 | 0 | 9555.0 | 15987.0 | 7 |
| pageindex | 16000 | 424/546 (77.7%) | 37 | 16 | 0 | 9555.0 | 15987.0 | 8 |

Table-heavy cells are room category, maternity and newborn, across all three plans and both query styles. Low complete-cell rates are visible retrieval limitations; they do not invalidate the separately reviewed 39 prepared facts.

## PageIndex call cost and failures

| Phase | Actual calls | Relay failures | Input tokens | Cached input | Reasoning | Output tokens | Summed call seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| index | 2918 | 0 | 4372069 | 84352 | 17044 | 327109 | 12264.4 |
| search | 78 | 0 | 5820634 | 2378880 | 18418 | 27188 | 759.6 |

The first indexing run stopped because the local adapter returned `stop` while PageIndex expects `finished`. The adapter was corrected and successful calls cached before resuming. All actual calls from that failed run remain included above. Token usage is the relay-reported amount; no dollar estimate is invented. Other arms make zero LLM calls per query (dense and MiniLM run locally).

## Every cell

Each entry is recalled spans / reference spans for **fixed; customer** queries. An incomplete fraction is a failure. PageIndex absent measurements are explicitly marked.

| Plan | Criterion | Current 8k | Current 16k | BM25 8k | BM25 16k | MiniLM 8k | MiniLM 16k | PageIndex 8k | PageIndex 16k |
|---|---|---|---|---|---|---|---|---|---|
| star-comprehensive | sum_insured | 0/4; 3/4 | 0/4; 3/4 | 0/4; 0/4 | 0/4; 0/4 | 0/4; 0/4 | 0/4; 0/4 | 3/4; 0/4 | 3/4; 2/4 |
| star-comprehensive | room_category | 6/6; 6/6 | 6/6; 6/6 | 6/6; 4/6 | 6/6; 6/6 | 6/6; 6/6 | 6/6; 6/6 | 6/6; 6/6 | 6/6; 6/6 |
| star-comprehensive | copay | 0/4; 0/4 | 0/4; 0/4 | 3/4; 4/4 | 4/4; 4/4 | 0/4; 0/4 | 3/4; 4/4 | 3/4; 4/4 | 4/4; 4/4 |
| star-comprehensive | deductible | 0/1; 1/1 | 0/1; 1/1 | 1/1; 0/1 | 1/1; 1/1 | 0/1; 1/1 | 0/1; 1/1 | 1/1; 1/1 | 1/1; 1/1 |
| star-comprehensive | ped_waiting_period | 9/9; 0/9 | 9/9; 9/9 | 9/9; 0/9 | 9/9; 0/9 | 1/9; 0/9 | 9/9; 0/9 | 8/9; 8/9 | 8/9; 8/9 |
| star-comprehensive | initial_specific_waiting_periods | 8/9; 8/9 | 8/9; 8/9 | 8/9; 8/9 | 8/9; 8/9 | 8/9; 8/9 | 8/9; 8/9 | 8/9; 8/9 | 8/9; 8/9 |
| star-comprehensive | maternity | 2/13; 11/13 | 2/13; 11/13 | 0/13; 11/13 | 11/13; 13/13 | 0/13; 13/13 | 11/13; 13/13 | 13/13; 11/13 | 13/13; 11/13 |
| star-comprehensive | newborn | 17/24; 16/24 | 19/24; 16/24 | 16/24; 18/24 | 16/24; 18/24 | 16/24; 16/24 | 16/24; 18/24 | 17/24; 16/24 | 20/24; 16/24 |
| star-comprehensive | restoration | 5/5; 5/5 | 5/5; 5/5 | 5/5; 5/5 | 5/5; 5/5 | 5/5; 5/5 | 5/5; 5/5 | 5/5; 5/5 | 5/5; 5/5 |
| star-comprehensive | family_floater | 2/12; 6/12 | 2/12; 6/12 | 6/12; 4/12 | 7/12; 4/12 | 5/12; 5/12 | 6/12; 6/12 | 5/12; 11/12 | 5/12; 11/12 |
| star-comprehensive | portability | 0/2; 0/2 | 0/2; 0/2 | 2/2; 2/2 | 2/2; 2/2 | 0/2; 0/2 | 2/2; 0/2 | 2/2; 2/2 | 2/2; 2/2 |
| star-comprehensive | geography | 0/2; 0/2 | 0/2; 0/2 | 1/2; 0/2 | 1/2; 2/2 | 0/2; 1/2 | 1/2; 1/2 | 2/2; 2/2 | 2/2; 2/2 |
| star-comprehensive | eligibility | 5/9; 2/9 | 5/9; 2/9 | 6/9; 0/9 | 6/9; 0/9 | 5/9; 2/9 | 6/9; 3/9 | 5/9; 6/9 | 5/9; 6/9 |
| star-family-health-optima | sum_insured | 0/4; 4/4 | 0/4; 4/4 | 0/4; 0/4 | 0/4; 0/4 | 0/4; 0/4 | 4/4; 0/4 | 4/4; 4/4 | 4/4; 4/4 |
| star-family-health-optima | room_category | 5/5; 4/5 | 5/5; 4/5 | 5/5; 4/5 | 5/5; 4/5 | 4/5; 4/5 | 4/5; 4/5 | 4/5; 4/5 | 5/5; 4/5 |
| star-family-health-optima | copay | 1/2; 0/2 | 2/2; 1/2 | 2/2; 1/2 | 2/2; 1/2 | 2/2; 1/2 | 2/2; 1/2 | 2/2; 2/2 | 2/2; 2/2 |
| star-family-health-optima | deductible | 0/2; 2/2 | 0/2; 2/2 | 2/2; 0/2 | 2/2; 2/2 | 0/2; 2/2 | 0/2; 2/2 | 2/2; 2/2 | 2/2; 2/2 |
| star-family-health-optima | ped_waiting_period | 4/4; 0/4 | 4/4; 0/4 | 0/4; 0/4 | 4/4; 0/4 | 0/4; 0/4 | 4/4; 0/4 | 4/4; 0/4 | 4/4; 0/4 |
| star-family-health-optima | initial_specific_waiting_periods | 7/12; 7/12 | 7/12; 7/12 | 7/12; 7/12 | 12/12; 12/12 | 7/12; 7/12 | 7/12; 7/12 | 12/12; 12/12 | 12/12; 12/12 |
| star-family-health-optima | maternity | 2/2; 0/2 | 2/2; 0/2 | 0/2; 0/2 | 2/2; 0/2 | 0/2; 0/2 | 2/2; 0/2 | 2/2; 2/2 | 2/2; 2/2 |
| star-family-health-optima | newborn | 5/8; 5/8 | 7/8; 5/8 | 5/8; 5/8 | 6/8; 7/8 | 6/8; 5/8 | 6/8; 7/8 | 7/8; 5/8 | 7/8; 5/8 |
| star-family-health-optima | restoration | 5/7; 5/7 | 5/7; 6/7 | 6/7; 5/7 | 6/7; 5/7 | 5/7; 5/7 | 5/7; 5/7 | 5/7; 5/7 | 5/7; 5/7 |
| star-family-health-optima | family_floater | 4/11; 3/11 | 6/11; 4/11 | 3/11; 0/11 | 7/11; 8/11 | 3/11; 3/11 | 9/11; 8/11 | 4/11; 0/11 | 4/11; 0/11 |
| star-family-health-optima | portability | 3/5; 1/5 | 4/5; 2/5 | 3/5; 2/5 | 3/5; 4/5 | 2/5; 1/5 | 4/5; 3/5 | 4/5; 2/5 | 4/5; 2/5 |
| star-family-health-optima | geography | 1/3; 1/3 | 1/3; 1/3 | 2/3; 1/3 | 2/3; 2/3 | 1/3; 1/3 | 2/3; 2/3 | 1/3; 2/3 | 1/3; 2/3 |
| star-family-health-optima | eligibility | 7/9; 3/9 | 7/9; 7/9 | 7/9; 0/9 | 7/9; 0/9 | 3/9; 0/9 | 7/9; 0/9 | 4/9; 7/9 | 4/9; 7/9 |
| star-health-assure | sum_insured | 5/8; 0/8 | 5/8; 5/8 | 8/8; 3/8 | 8/8; 3/8 | 8/8; 0/8 | 8/8; 3/8 | 7/8; 4/8 | 7/8; 4/8 |
| star-health-assure | room_category | 11/11; 9/11 | 11/11; 11/11 | 11/11; 8/11 | 11/11; 11/11 | 8/11; 11/11 | 11/11; 11/11 | 11/11; 11/11 | 11/11; 11/11 |
| star-health-assure | copay | 0/3; 0/3 | 0/3; 3/3 | 0/3; 3/3 | 0/3; 3/3 | 0/3; 3/3 | 0/3; 3/3 | 3/3; 3/3 | 3/3; 3/3 |
| star-health-assure | deductible | 0/7; 0/7 | 0/7; 7/7 | 7/7; 0/7 | 7/7; 7/7 | 0/7; 0/7 | 0/7; 0/7 | 7/7; 0/7 | 7/7; 0/7 |
| star-health-assure | ped_waiting_period | 5/6; 0/6 | 5/6; 0/6 | 5/6; 0/6 | 5/6; 0/6 | 5/6; 0/6 | 5/6; 0/6 | 6/6; 6/6 | 6/6; 6/6 |
| star-health-assure | initial_specific_waiting_periods | 8/9; 0/9 | 9/9; 9/9 | 8/9; 9/9 | 8/9; 9/9 | 0/9; 2/9 | 0/9; 9/9 | 9/9; 9/9 | 9/9; 9/9 |
| star-health-assure | maternity | 7/11; 6/11 | 7/11; 11/11 | 4/11; 10/11 | 7/11; 10/11 | 4/11; 4/11 | 5/11; 8/11 | 5/11; 5/11 | 5/11; 5/11 |
| star-health-assure | newborn | 12/14; 6/14 | 12/14; 12/14 | 0/14; 6/14 | 8/14; 13/14 | 6/14; 6/14 | 12/14; 13/14 | 12/14; 12/14 | 12/14; 12/14 |
| star-health-assure | restoration | 10/10; 10/10 | 10/10; 10/10 | 10/10; 10/10 | 10/10; 10/10 | 10/10; 10/10 | 10/10; 10/10 | 10/10; 10/10 | 10/10; 10/10 |
| star-health-assure | family_floater | 0/3; 0/3 | 0/3; 0/3 | 2/3; 0/3 | 3/3; 0/3 | 0/3; 0/3 | 3/3; 0/3 | 0/3; 0/3 | 0/3; 0/3 |
| star-health-assure | portability | 4/5; 4/5 | 5/5; 4/5 | 2/5; 3/5 | 4/5; 5/5 | 4/5; 4/5 | 4/5; 4/5 | 5/5; 2/5 | 5/5; 2/5 |
| star-health-assure | geography | 1/3; 1/3 | 1/3; 1/3 | 2/3; 1/3 | 2/3; 2/3 | 1/3; 1/3 | 2/3; 2/3 | 2/3; 2/3 | 2/3; 2/3 |
| star-health-assure | eligibility | 4/9; 4/9 | 4/9; 4/9 | 9/9; 5/9 | 9/9; 5/9 | 4/9; 0/9 | 9/9; 5/9 | 8/9; 8/9 | 8/9; 8/9 |

## Every failed query/packet

Missing span IDs below resolve to the full IDs and exact source positions in the reference map. The adjacent JSON preserves all packet chunk IDs, budgets, omission counts and per-query latencies, including successes.

| Plan / criterion | Arm | Budget | Query | Missing span IDs |
|---|---|---:|---|---|
| star-comprehensive / copay | bm25 | 8000 | fixed | e6a35708 |
| star-comprehensive / copay | current | 8000 | customer | c668c3fd, c9030eae, 9c682f5e, e6a35708 |
| star-comprehensive / copay | current | 8000 | fixed | c668c3fd, c9030eae, 9c682f5e, e6a35708 |
| star-comprehensive / copay | current | 16000 | customer | c668c3fd, c9030eae, 9c682f5e, e6a35708 |
| star-comprehensive / copay | current | 16000 | fixed | c668c3fd, c9030eae, 9c682f5e, e6a35708 |
| star-comprehensive / copay | minilm | 8000 | customer | c668c3fd, c9030eae, 9c682f5e, e6a35708 |
| star-comprehensive / copay | minilm | 8000 | fixed | c668c3fd, c9030eae, 9c682f5e, e6a35708 |
| star-comprehensive / copay | minilm | 16000 | fixed | e6a35708 |
| star-comprehensive / copay | pageindex | 8000 | fixed | e6a35708 |
| star-comprehensive / deductible | bm25 | 8000 | customer | de1d8245 |
| star-comprehensive / deductible | current | 8000 | fixed | de1d8245 |
| star-comprehensive / deductible | current | 16000 | fixed | de1d8245 |
| star-comprehensive / deductible | minilm | 8000 | fixed | de1d8245 |
| star-comprehensive / deductible | minilm | 16000 | fixed | de1d8245 |
| star-comprehensive / eligibility | bm25 | 8000 | customer | af251711, 8f2dea70, 5377d39f, 2f0f2ec0, f697f3a1, dda18074, 462bf0e9, 00369f5e, 2ce1a514 |
| star-comprehensive / eligibility | bm25 | 8000 | fixed | f697f3a1, 00369f5e, 2ce1a514 |
| star-comprehensive / eligibility | bm25 | 16000 | customer | af251711, 8f2dea70, 5377d39f, 2f0f2ec0, f697f3a1, dda18074, 462bf0e9, 00369f5e, 2ce1a514 |
| star-comprehensive / eligibility | bm25 | 16000 | fixed | f697f3a1, 00369f5e, 2ce1a514 |
| star-comprehensive / eligibility | current | 8000 | customer | af251711, 8f2dea70, 5377d39f, 2f0f2ec0, f697f3a1, dda18074, 462bf0e9 |
| star-comprehensive / eligibility | current | 8000 | fixed | 8f2dea70, f697f3a1, 00369f5e, 2ce1a514 |
| star-comprehensive / eligibility | current | 16000 | customer | af251711, 8f2dea70, 5377d39f, 2f0f2ec0, f697f3a1, dda18074, 462bf0e9 |
| star-comprehensive / eligibility | current | 16000 | fixed | 8f2dea70, f697f3a1, 00369f5e, 2ce1a514 |
| star-comprehensive / eligibility | minilm | 8000 | customer | af251711, 8f2dea70, 5377d39f, 2f0f2ec0, f697f3a1, dda18074, 462bf0e9 |
| star-comprehensive / eligibility | minilm | 8000 | fixed | 8f2dea70, f697f3a1, 00369f5e, 2ce1a514 |
| star-comprehensive / eligibility | minilm | 16000 | customer | af251711, 5377d39f, 2f0f2ec0, f697f3a1, dda18074, 462bf0e9 |
| star-comprehensive / eligibility | minilm | 16000 | fixed | f697f3a1, 00369f5e, 2ce1a514 |
| star-comprehensive / eligibility | pageindex | 8000 | customer | f697f3a1, 00369f5e, 2ce1a514 |
| star-comprehensive / eligibility | pageindex | 8000 | fixed | 8f2dea70, f697f3a1, 00369f5e, 2ce1a514 |
| star-comprehensive / eligibility | pageindex | 16000 | customer | f697f3a1, 00369f5e, 2ce1a514 |
| star-comprehensive / eligibility | pageindex | 16000 | fixed | 8f2dea70, f697f3a1, 00369f5e, 2ce1a514 |
| star-comprehensive / family_floater | bm25 | 8000 | customer | 8f2dea70, 9ed1a8ce, 0165667c, 1eaf4639, daa0cbca, 84af2a32, d1bb62e0, e8eff439 |
| star-comprehensive / family_floater | bm25 | 8000 | fixed | 9ed1a8ce, 0165667c, 1eaf4639, daa0cbca, 84af2a32, d1bb62e0 |
| star-comprehensive / family_floater | bm25 | 16000 | customer | 8f2dea70, 9ed1a8ce, 0165667c, 1eaf4639, daa0cbca, 84af2a32, d1bb62e0, e8eff439 |
| star-comprehensive / family_floater | bm25 | 16000 | fixed | 0165667c, 1eaf4639, daa0cbca, 84af2a32, d1bb62e0 |
| star-comprehensive / family_floater | current | 8000 | customer | 8f2dea70, 0165667c, 1eaf4639, daa0cbca, 84af2a32, d1bb62e0 |
| star-comprehensive / family_floater | current | 8000 | fixed | 8f2dea70, af251711, 2f0f2ec0, dda18074, 462bf0e9, 0165667c, 1eaf4639, daa0cbca, 84af2a32, d1bb62e0 |
| star-comprehensive / family_floater | current | 16000 | customer | 8f2dea70, 0165667c, 1eaf4639, daa0cbca, 84af2a32, d1bb62e0 |
| star-comprehensive / family_floater | current | 16000 | fixed | 8f2dea70, af251711, 2f0f2ec0, dda18074, 462bf0e9, 0165667c, 1eaf4639, daa0cbca, 84af2a32, d1bb62e0 |
| star-comprehensive / family_floater | minilm | 8000 | customer | 8f2dea70, 9ed1a8ce, 0165667c, 1eaf4639, daa0cbca, 84af2a32, d1bb62e0 |
| star-comprehensive / family_floater | minilm | 8000 | fixed | 8f2dea70, 9ed1a8ce, 0165667c, 1eaf4639, daa0cbca, 84af2a32, d1bb62e0 |
| star-comprehensive / family_floater | minilm | 16000 | customer | 8f2dea70, 0165667c, 1eaf4639, daa0cbca, 84af2a32, d1bb62e0 |
| star-comprehensive / family_floater | minilm | 16000 | fixed | 8f2dea70, 0165667c, 1eaf4639, daa0cbca, 84af2a32, d1bb62e0 |
| star-comprehensive / family_floater | pageindex | 8000 | customer | 9ed1a8ce |
| star-comprehensive / family_floater | pageindex | 8000 | fixed | 9ed1a8ce, 0165667c, 1eaf4639, daa0cbca, 84af2a32, d1bb62e0, e8eff439 |
| star-comprehensive / family_floater | pageindex | 16000 | customer | 9ed1a8ce |
| star-comprehensive / family_floater | pageindex | 16000 | fixed | 9ed1a8ce, 0165667c, 1eaf4639, daa0cbca, 84af2a32, d1bb62e0, e8eff439 |
| star-comprehensive / geography | bm25 | 8000 | customer | 1de6b428, ce7bc7ec |
| star-comprehensive / geography | bm25 | 8000 | fixed | ce7bc7ec |
| star-comprehensive / geography | bm25 | 16000 | fixed | ce7bc7ec |
| star-comprehensive / geography | current | 8000 | customer | 1de6b428, ce7bc7ec |
| star-comprehensive / geography | current | 8000 | fixed | 1de6b428, ce7bc7ec |
| star-comprehensive / geography | current | 16000 | customer | 1de6b428, ce7bc7ec |
| star-comprehensive / geography | current | 16000 | fixed | 1de6b428, ce7bc7ec |
| star-comprehensive / geography | minilm | 8000 | customer | ce7bc7ec |
| star-comprehensive / geography | minilm | 8000 | fixed | 1de6b428, ce7bc7ec |
| star-comprehensive / geography | minilm | 16000 | customer | ce7bc7ec |
| star-comprehensive / geography | minilm | 16000 | fixed | ce7bc7ec |
| star-comprehensive / initial_specific_waiting_periods | bm25 | 8000 | customer | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | bm25 | 8000 | fixed | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | bm25 | 16000 | customer | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | bm25 | 16000 | fixed | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | current | 8000 | customer | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | current | 8000 | fixed | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | current | 16000 | customer | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | current | 16000 | fixed | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | minilm | 8000 | customer | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | minilm | 8000 | fixed | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | minilm | 16000 | customer | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | minilm | 16000 | fixed | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | pageindex | 8000 | customer | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | pageindex | 8000 | fixed | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | pageindex | 16000 | customer | 68676f5e |
| star-comprehensive / initial_specific_waiting_periods | pageindex | 16000 | fixed | 68676f5e |
| star-comprehensive / maternity | bm25 | 8000 | customer | 8a108a2e, 26261d47 |
| star-comprehensive / maternity | bm25 | 8000 | fixed | 6b284f3f, 129db5b0, 48599eb2, 9ae112c8, 0bff6acd, e9183b67, bebedaca, f2472395, 4a9f9f0a, 89d7ca0a, f15b151a, 8a108a2e, 26261d47 |
| star-comprehensive / maternity | bm25 | 16000 | fixed | 8a108a2e, 26261d47 |
| star-comprehensive / maternity | current | 8000 | customer | 8a108a2e, 26261d47 |
| star-comprehensive / maternity | current | 8000 | fixed | 6b284f3f, 129db5b0, 48599eb2, 9ae112c8, 0bff6acd, e9183b67, bebedaca, f2472395, 4a9f9f0a, 89d7ca0a, f15b151a |
| star-comprehensive / maternity | current | 16000 | customer | 8a108a2e, 26261d47 |
| star-comprehensive / maternity | current | 16000 | fixed | 6b284f3f, 129db5b0, 48599eb2, 9ae112c8, 0bff6acd, e9183b67, bebedaca, f2472395, 4a9f9f0a, 89d7ca0a, f15b151a |
| star-comprehensive / maternity | minilm | 8000 | fixed | 6b284f3f, 129db5b0, 48599eb2, 9ae112c8, 0bff6acd, e9183b67, bebedaca, f2472395, 4a9f9f0a, 89d7ca0a, f15b151a, 8a108a2e, 26261d47 |
| star-comprehensive / maternity | minilm | 16000 | fixed | 8a108a2e, 26261d47 |
| star-comprehensive / maternity | pageindex | 8000 | customer | 8a108a2e, 26261d47 |
| star-comprehensive / maternity | pageindex | 16000 | customer | 8a108a2e, 26261d47 |
| star-comprehensive / newborn | bm25 | 8000 | customer | f697f3a1, 4f8a1bc4, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7 |
| star-comprehensive / newborn | bm25 | 8000 | fixed | f697f3a1, 4f8a1bc4, cd0960d6, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7, 8a108a2e |
| star-comprehensive / newborn | bm25 | 16000 | customer | f697f3a1, 4f8a1bc4, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7 |
| star-comprehensive / newborn | bm25 | 16000 | fixed | f697f3a1, 4f8a1bc4, cd0960d6, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7, 8a108a2e |
| star-comprehensive / newborn | current | 8000 | customer | f697f3a1, 4f8a1bc4, cd0960d6, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7, 8a108a2e |
| star-comprehensive / newborn | current | 8000 | fixed | f697f3a1, cd0960d6, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7, 8a108a2e |
| star-comprehensive / newborn | current | 16000 | customer | f697f3a1, 4f8a1bc4, cd0960d6, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7, 8a108a2e |
| star-comprehensive / newborn | current | 16000 | fixed | f697f3a1, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7 |
| star-comprehensive / newborn | minilm | 8000 | customer | f697f3a1, 4f8a1bc4, cd0960d6, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7, 8a108a2e |
| star-comprehensive / newborn | minilm | 8000 | fixed | f697f3a1, 4f8a1bc4, cd0960d6, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7, 8a108a2e |
| star-comprehensive / newborn | minilm | 16000 | customer | f697f3a1, 4f8a1bc4, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7 |
| star-comprehensive / newborn | minilm | 16000 | fixed | f697f3a1, 4f8a1bc4, cd0960d6, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7, 8a108a2e |
| star-comprehensive / newborn | pageindex | 8000 | customer | f697f3a1, 4f8a1bc4, cd0960d6, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7, 8a108a2e |
| star-comprehensive / newborn | pageindex | 8000 | fixed | 4f8a1bc4, cd0960d6, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7, 8a108a2e |
| star-comprehensive / newborn | pageindex | 16000 | customer | f697f3a1, 4f8a1bc4, cd0960d6, 3f0ebce5, 2f0f2ec0, 121715de, d357a6b7, 8a108a2e |
| star-comprehensive / newborn | pageindex | 16000 | fixed | 4f8a1bc4, cd0960d6, d357a6b7, 8a108a2e |
| star-comprehensive / ped_waiting_period | bm25 | 8000 | customer | 4a60f92f, 78fca988, 9b371278, 32c72afd, 4302cb1b, bd036fd6, a20358ac, 2ff623fc, 580d47b7 |
| star-comprehensive / ped_waiting_period | bm25 | 16000 | customer | 4a60f92f, 78fca988, 9b371278, 32c72afd, 4302cb1b, bd036fd6, a20358ac, 2ff623fc, 580d47b7 |
| star-comprehensive / ped_waiting_period | current | 8000 | customer | 4a60f92f, 78fca988, 9b371278, 32c72afd, 4302cb1b, bd036fd6, a20358ac, 2ff623fc, 580d47b7 |
| star-comprehensive / ped_waiting_period | minilm | 8000 | customer | 4a60f92f, 78fca988, 9b371278, 32c72afd, 4302cb1b, bd036fd6, a20358ac, 2ff623fc, 580d47b7 |
| star-comprehensive / ped_waiting_period | minilm | 8000 | fixed | 4a60f92f, 78fca988, 9b371278, 32c72afd, 4302cb1b, bd036fd6, a20358ac, 2ff623fc |
| star-comprehensive / ped_waiting_period | minilm | 16000 | customer | 4a60f92f, 78fca988, 9b371278, 32c72afd, 4302cb1b, bd036fd6, a20358ac, 2ff623fc, 580d47b7 |
| star-comprehensive / ped_waiting_period | pageindex | 8000 | customer | 2ff623fc |
| star-comprehensive / ped_waiting_period | pageindex | 8000 | fixed | 580d47b7 |
| star-comprehensive / ped_waiting_period | pageindex | 16000 | customer | 2ff623fc |
| star-comprehensive / ped_waiting_period | pageindex | 16000 | fixed | 580d47b7 |
| star-comprehensive / portability | current | 8000 | customer | b0e56bdc, 43472171 |
| star-comprehensive / portability | current | 8000 | fixed | b0e56bdc, 43472171 |
| star-comprehensive / portability | current | 16000 | customer | b0e56bdc, 43472171 |
| star-comprehensive / portability | current | 16000 | fixed | b0e56bdc, 43472171 |
| star-comprehensive / portability | minilm | 8000 | customer | b0e56bdc, 43472171 |
| star-comprehensive / portability | minilm | 8000 | fixed | b0e56bdc, 43472171 |
| star-comprehensive / portability | minilm | 16000 | customer | b0e56bdc, 43472171 |
| star-comprehensive / room_category | bm25 | 8000 | customer | f5cc690f, e4b533a2 |
| star-comprehensive / sum_insured | bm25 | 8000 | customer | af251711, 5377d39f, d357a6b7, 5d555ab8 |
| star-comprehensive / sum_insured | bm25 | 8000 | fixed | af251711, 5377d39f, d357a6b7, 5d555ab8 |
| star-comprehensive / sum_insured | bm25 | 16000 | customer | af251711, 5377d39f, d357a6b7, 5d555ab8 |
| star-comprehensive / sum_insured | bm25 | 16000 | fixed | af251711, 5377d39f, d357a6b7, 5d555ab8 |
| star-comprehensive / sum_insured | current | 8000 | customer | 5d555ab8 |
| star-comprehensive / sum_insured | current | 8000 | fixed | af251711, 5377d39f, d357a6b7, 5d555ab8 |
| star-comprehensive / sum_insured | current | 16000 | customer | 5d555ab8 |
| star-comprehensive / sum_insured | current | 16000 | fixed | af251711, 5377d39f, d357a6b7, 5d555ab8 |
| star-comprehensive / sum_insured | minilm | 8000 | customer | af251711, 5377d39f, d357a6b7, 5d555ab8 |
| star-comprehensive / sum_insured | minilm | 8000 | fixed | af251711, 5377d39f, d357a6b7, 5d555ab8 |
| star-comprehensive / sum_insured | minilm | 16000 | customer | af251711, 5377d39f, d357a6b7, 5d555ab8 |
| star-comprehensive / sum_insured | minilm | 16000 | fixed | af251711, 5377d39f, d357a6b7, 5d555ab8 |
| star-comprehensive / sum_insured | pageindex | 8000 | customer | af251711, 5377d39f, d357a6b7, 5d555ab8 |
| star-comprehensive / sum_insured | pageindex | 8000 | fixed | 5d555ab8 |
| star-comprehensive / sum_insured | pageindex | 16000 | customer | d357a6b7, 5d555ab8 |
| star-comprehensive / sum_insured | pageindex | 16000 | fixed | 5d555ab8 |
| star-family-health-optima / copay | bm25 | 8000 | customer | bc19e01c |
| star-family-health-optima / copay | bm25 | 16000 | customer | bc19e01c |
| star-family-health-optima / copay | current | 8000 | customer | c7fb3038, bc19e01c |
| star-family-health-optima / copay | current | 8000 | fixed | bc19e01c |
| star-family-health-optima / copay | current | 16000 | customer | bc19e01c |
| star-family-health-optima / copay | minilm | 8000 | customer | bc19e01c |
| star-family-health-optima / copay | minilm | 16000 | customer | bc19e01c |
| star-family-health-optima / deductible | bm25 | 8000 | customer | ed10e2bd, 23662334 |
| star-family-health-optima / deductible | current | 8000 | fixed | ed10e2bd, 23662334 |
| star-family-health-optima / deductible | current | 16000 | fixed | ed10e2bd, 23662334 |
| star-family-health-optima / deductible | minilm | 8000 | fixed | ed10e2bd, 23662334 |
| star-family-health-optima / deductible | minilm | 16000 | fixed | ed10e2bd, 23662334 |
| star-family-health-optima / eligibility | bm25 | 8000 | customer | d47d86dc, 5499290a, 978bb899, ff380c92, 4f0c4e68, c0b4e87e, c34d6bfb, c1a593ca, 9839e4c8 |
| star-family-health-optima / eligibility | bm25 | 8000 | fixed | 5499290a, 978bb899 |
| star-family-health-optima / eligibility | bm25 | 16000 | customer | d47d86dc, 5499290a, 978bb899, ff380c92, 4f0c4e68, c0b4e87e, c34d6bfb, c1a593ca, 9839e4c8 |
| star-family-health-optima / eligibility | bm25 | 16000 | fixed | 5499290a, 978bb899 |
| star-family-health-optima / eligibility | current | 8000 | customer | d47d86dc, 5499290a, 978bb899, ff380c92, 4f0c4e68, c0b4e87e |
| star-family-health-optima / eligibility | current | 8000 | fixed | 5499290a, 978bb899 |
| star-family-health-optima / eligibility | current | 16000 | customer | 5499290a, 978bb899 |
| star-family-health-optima / eligibility | current | 16000 | fixed | 5499290a, 978bb899 |
| star-family-health-optima / eligibility | minilm | 8000 | customer | d47d86dc, 5499290a, 978bb899, ff380c92, 4f0c4e68, c0b4e87e, c34d6bfb, c1a593ca, 9839e4c8 |
| star-family-health-optima / eligibility | minilm | 8000 | fixed | d47d86dc, 5499290a, 978bb899, ff380c92, 4f0c4e68, c0b4e87e |
| star-family-health-optima / eligibility | minilm | 16000 | customer | d47d86dc, 5499290a, 978bb899, ff380c92, 4f0c4e68, c0b4e87e, c34d6bfb, c1a593ca, 9839e4c8 |
| star-family-health-optima / eligibility | minilm | 16000 | fixed | 5499290a, 978bb899 |
| star-family-health-optima / eligibility | pageindex | 8000 | customer | 5499290a, 978bb899 |
| star-family-health-optima / eligibility | pageindex | 8000 | fixed | 5499290a, 978bb899, c34d6bfb, c1a593ca, 9839e4c8 |
| star-family-health-optima / eligibility | pageindex | 16000 | customer | 5499290a, 978bb899 |
| star-family-health-optima / eligibility | pageindex | 16000 | fixed | 5499290a, 978bb899, c34d6bfb, c1a593ca, 9839e4c8 |
| star-family-health-optima / family_floater | bm25 | 8000 | customer | 90c25a6c, b053a313, 02ff798b, 5499290a, c26dd448, c34d6bfb, c1a593ca, 656eda43, e041a745, a8c40883, abb1238b |
| star-family-health-optima / family_floater | bm25 | 8000 | fixed | 90c25a6c, b053a313, 02ff798b, 5499290a, c26dd448, e041a745, a8c40883, abb1238b |
| star-family-health-optima / family_floater | bm25 | 16000 | customer | e041a745, a8c40883, abb1238b |
| star-family-health-optima / family_floater | bm25 | 16000 | fixed | c26dd448, e041a745, a8c40883, abb1238b |
| star-family-health-optima / family_floater | current | 8000 | customer | 90c25a6c, b053a313, 02ff798b, 5499290a, c26dd448, e041a745, a8c40883, abb1238b |
| star-family-health-optima / family_floater | current | 8000 | fixed | 90c25a6c, b053a313, 02ff798b, 5499290a, e041a745, a8c40883, abb1238b |
| star-family-health-optima / family_floater | current | 16000 | customer | b053a313, 02ff798b, 5499290a, c26dd448, e041a745, a8c40883, abb1238b |
| star-family-health-optima / family_floater | current | 16000 | fixed | 90c25a6c, b053a313, 02ff798b, 5499290a, abb1238b |
| star-family-health-optima / family_floater | minilm | 8000 | customer | 90c25a6c, b053a313, 02ff798b, 5499290a, c26dd448, e041a745, a8c40883, abb1238b |
| star-family-health-optima / family_floater | minilm | 8000 | fixed | 90c25a6c, b053a313, 02ff798b, 5499290a, c26dd448, e041a745, a8c40883, abb1238b |
| star-family-health-optima / family_floater | minilm | 16000 | customer | e041a745, a8c40883, abb1238b |
| star-family-health-optima / family_floater | minilm | 16000 | fixed | c26dd448, abb1238b |
| star-family-health-optima / family_floater | pageindex | 8000 | customer | 90c25a6c, b053a313, 02ff798b, 5499290a, c26dd448, c34d6bfb, c1a593ca, 656eda43, e041a745, a8c40883, abb1238b |
| star-family-health-optima / family_floater | pageindex | 8000 | fixed | c26dd448, c34d6bfb, c1a593ca, 656eda43, e041a745, a8c40883, abb1238b |
| star-family-health-optima / family_floater | pageindex | 16000 | customer | 90c25a6c, b053a313, 02ff798b, 5499290a, c26dd448, c34d6bfb, c1a593ca, 656eda43, e041a745, a8c40883, abb1238b |
| star-family-health-optima / family_floater | pageindex | 16000 | fixed | c26dd448, c34d6bfb, c1a593ca, 656eda43, e041a745, a8c40883, abb1238b |
| star-family-health-optima / geography | bm25 | 8000 | customer | 06979d97, 9d399bc2 |
| star-family-health-optima / geography | bm25 | 8000 | fixed | d7ce64a8 |
| star-family-health-optima / geography | bm25 | 16000 | customer | 9d399bc2 |
| star-family-health-optima / geography | bm25 | 16000 | fixed | d7ce64a8 |
| star-family-health-optima / geography | current | 8000 | customer | 9d399bc2, d7ce64a8 |
| star-family-health-optima / geography | current | 8000 | fixed | 9d399bc2, d7ce64a8 |
| star-family-health-optima / geography | current | 16000 | customer | 9d399bc2, d7ce64a8 |
| star-family-health-optima / geography | current | 16000 | fixed | 9d399bc2, d7ce64a8 |
| star-family-health-optima / geography | minilm | 8000 | customer | 06979d97, 9d399bc2 |
| star-family-health-optima / geography | minilm | 8000 | fixed | 06979d97, d7ce64a8 |
| star-family-health-optima / geography | minilm | 16000 | customer | 9d399bc2 |
| star-family-health-optima / geography | minilm | 16000 | fixed | d7ce64a8 |
| star-family-health-optima / geography | pageindex | 8000 | customer | d7ce64a8 |
| star-family-health-optima / geography | pageindex | 8000 | fixed | 06979d97, d7ce64a8 |
| star-family-health-optima / geography | pageindex | 16000 | customer | d7ce64a8 |
| star-family-health-optima / geography | pageindex | 16000 | fixed | 06979d97, d7ce64a8 |
| star-family-health-optima / initial_specific_waiting_periods | bm25 | 8000 | customer | c8dba22a, cca1d842, 750e187d, c785f5ad, fe47e0eb |
| star-family-health-optima / initial_specific_waiting_periods | bm25 | 8000 | fixed | c8dba22a, cca1d842, 750e187d, c785f5ad, fe47e0eb |
| star-family-health-optima / initial_specific_waiting_periods | current | 8000 | customer | 9abcb9f3, d9335d4d, a0e3529d, 15c90631, bf6cb657 |
| star-family-health-optima / initial_specific_waiting_periods | current | 8000 | fixed | 9abcb9f3, d9335d4d, a0e3529d, 15c90631, bf6cb657 |
| star-family-health-optima / initial_specific_waiting_periods | current | 16000 | customer | 9abcb9f3, d9335d4d, a0e3529d, 15c90631, bf6cb657 |
| star-family-health-optima / initial_specific_waiting_periods | current | 16000 | fixed | 9abcb9f3, d9335d4d, a0e3529d, 15c90631, bf6cb657 |
| star-family-health-optima / initial_specific_waiting_periods | minilm | 8000 | customer | 9abcb9f3, d9335d4d, a0e3529d, 15c90631, bf6cb657 |
| star-family-health-optima / initial_specific_waiting_periods | minilm | 8000 | fixed | 9abcb9f3, d9335d4d, a0e3529d, 15c90631, bf6cb657 |
| star-family-health-optima / initial_specific_waiting_periods | minilm | 16000 | customer | 9abcb9f3, d9335d4d, a0e3529d, 15c90631, bf6cb657 |
| star-family-health-optima / initial_specific_waiting_periods | minilm | 16000 | fixed | 9abcb9f3, d9335d4d, a0e3529d, 15c90631, bf6cb657 |
| star-family-health-optima / maternity | bm25 | 8000 | customer | 75d26eff, 66364ba8 |
| star-family-health-optima / maternity | bm25 | 8000 | fixed | 75d26eff, 66364ba8 |
| star-family-health-optima / maternity | bm25 | 16000 | customer | 75d26eff, 66364ba8 |
| star-family-health-optima / maternity | current | 8000 | customer | 75d26eff, 66364ba8 |
| star-family-health-optima / maternity | current | 16000 | customer | 75d26eff, 66364ba8 |
| star-family-health-optima / maternity | minilm | 8000 | customer | 75d26eff, 66364ba8 |
| star-family-health-optima / maternity | minilm | 8000 | fixed | 75d26eff, 66364ba8 |
| star-family-health-optima / maternity | minilm | 16000 | customer | 75d26eff, 66364ba8 |
| star-family-health-optima / newborn | bm25 | 8000 | customer | 71cb07cd, 57f6d07c, f5886007 |
| star-family-health-optima / newborn | bm25 | 8000 | fixed | 71cb07cd, 57f6d07c, f5886007 |
| star-family-health-optima / newborn | bm25 | 16000 | customer | 71cb07cd |
| star-family-health-optima / newborn | bm25 | 16000 | fixed | 57f6d07c, f5886007 |
| star-family-health-optima / newborn | current | 8000 | customer | 71cb07cd, 57f6d07c, f5886007 |
| star-family-health-optima / newborn | current | 8000 | fixed | 71cb07cd, 57f6d07c, f5886007 |
| star-family-health-optima / newborn | current | 16000 | customer | 71cb07cd, 57f6d07c, f5886007 |
| star-family-health-optima / newborn | current | 16000 | fixed | 71cb07cd |
| star-family-health-optima / newborn | minilm | 8000 | customer | 71cb07cd, 57f6d07c, f5886007 |
| star-family-health-optima / newborn | minilm | 8000 | fixed | 57f6d07c, f5886007 |
| star-family-health-optima / newborn | minilm | 16000 | customer | 71cb07cd |
| star-family-health-optima / newborn | minilm | 16000 | fixed | 57f6d07c, f5886007 |
| star-family-health-optima / newborn | pageindex | 8000 | customer | 71cb07cd, 57f6d07c, f5886007 |
| star-family-health-optima / newborn | pageindex | 8000 | fixed | 71cb07cd |
| star-family-health-optima / newborn | pageindex | 16000 | customer | 71cb07cd, 57f6d07c, f5886007 |
| star-family-health-optima / newborn | pageindex | 16000 | fixed | 71cb07cd |
| star-family-health-optima / ped_waiting_period | bm25 | 8000 | customer | e6d9dd21, edafdaff, 93fe5c04, 1340c2bf |
| star-family-health-optima / ped_waiting_period | bm25 | 8000 | fixed | e6d9dd21, edafdaff, 93fe5c04, 1340c2bf |
| star-family-health-optima / ped_waiting_period | bm25 | 16000 | customer | e6d9dd21, edafdaff, 93fe5c04, 1340c2bf |
| star-family-health-optima / ped_waiting_period | current | 8000 | customer | e6d9dd21, edafdaff, 93fe5c04, 1340c2bf |
| star-family-health-optima / ped_waiting_period | current | 16000 | customer | e6d9dd21, edafdaff, 93fe5c04, 1340c2bf |
| star-family-health-optima / ped_waiting_period | minilm | 8000 | customer | e6d9dd21, edafdaff, 93fe5c04, 1340c2bf |
| star-family-health-optima / ped_waiting_period | minilm | 8000 | fixed | e6d9dd21, edafdaff, 93fe5c04, 1340c2bf |
| star-family-health-optima / ped_waiting_period | minilm | 16000 | customer | e6d9dd21, edafdaff, 93fe5c04, 1340c2bf |
| star-family-health-optima / ped_waiting_period | pageindex | 8000 | customer | e6d9dd21, edafdaff, 93fe5c04, 1340c2bf |
| star-family-health-optima / ped_waiting_period | pageindex | 16000 | customer | e6d9dd21, edafdaff, 93fe5c04, 1340c2bf |
| star-family-health-optima / portability | bm25 | 8000 | customer | dcc71f0e, 3e9141e0, 7f9061c3 |
| star-family-health-optima / portability | bm25 | 8000 | fixed | dcc71f0e, a5f260de |
| star-family-health-optima / portability | bm25 | 16000 | customer | dcc71f0e |
| star-family-health-optima / portability | bm25 | 16000 | fixed | dcc71f0e, a5f260de |
| star-family-health-optima / portability | current | 8000 | customer | dcc71f0e, a5f260de, 3e9141e0, 7f9061c3 |
| star-family-health-optima / portability | current | 8000 | fixed | a5f260de, 7f9061c3 |
| star-family-health-optima / portability | current | 16000 | customer | dcc71f0e, a5f260de, 7f9061c3 |
| star-family-health-optima / portability | current | 16000 | fixed | 7f9061c3 |
| star-family-health-optima / portability | minilm | 8000 | customer | dcc71f0e, a5f260de, 3e9141e0, 7f9061c3 |
| star-family-health-optima / portability | minilm | 8000 | fixed | dcc71f0e, a5f260de, 7f9061c3 |
| star-family-health-optima / portability | minilm | 16000 | customer | dcc71f0e, a5f260de |
| star-family-health-optima / portability | minilm | 16000 | fixed | dcc71f0e |
| star-family-health-optima / portability | pageindex | 8000 | customer | dcc71f0e, 3e9141e0, 7f9061c3 |
| star-family-health-optima / portability | pageindex | 8000 | fixed | dcc71f0e |
| star-family-health-optima / portability | pageindex | 16000 | customer | dcc71f0e, 3e9141e0, 7f9061c3 |
| star-family-health-optima / portability | pageindex | 16000 | fixed | dcc71f0e |
| star-family-health-optima / restoration | bm25 | 8000 | customer | b3739119, abb1238b |
| star-family-health-optima / restoration | bm25 | 8000 | fixed | abb1238b |
| star-family-health-optima / restoration | bm25 | 16000 | customer | b3739119, abb1238b |
| star-family-health-optima / restoration | bm25 | 16000 | fixed | abb1238b |
| star-family-health-optima / restoration | current | 8000 | customer | b3739119, abb1238b |
| star-family-health-optima / restoration | current | 8000 | fixed | b3739119, abb1238b |
| star-family-health-optima / restoration | current | 16000 | customer | abb1238b |
| star-family-health-optima / restoration | current | 16000 | fixed | b3739119, abb1238b |
| star-family-health-optima / restoration | minilm | 8000 | customer | b3739119, abb1238b |
| star-family-health-optima / restoration | minilm | 8000 | fixed | b3739119, abb1238b |
| star-family-health-optima / restoration | minilm | 16000 | customer | b3739119, abb1238b |
| star-family-health-optima / restoration | minilm | 16000 | fixed | b3739119, abb1238b |
| star-family-health-optima / restoration | pageindex | 8000 | customer | b3739119, abb1238b |
| star-family-health-optima / restoration | pageindex | 8000 | fixed | b3739119, abb1238b |
| star-family-health-optima / restoration | pageindex | 16000 | customer | b3739119, abb1238b |
| star-family-health-optima / restoration | pageindex | 16000 | fixed | b3739119, abb1238b |
| star-family-health-optima / room_category | bm25 | 8000 | customer | c9178f57 |
| star-family-health-optima / room_category | bm25 | 16000 | customer | c9178f57 |
| star-family-health-optima / room_category | current | 8000 | customer | c9178f57 |
| star-family-health-optima / room_category | current | 16000 | customer | c9178f57 |
| star-family-health-optima / room_category | minilm | 8000 | customer | c9178f57 |
| star-family-health-optima / room_category | minilm | 8000 | fixed | c9178f57 |
| star-family-health-optima / room_category | minilm | 16000 | customer | c9178f57 |
| star-family-health-optima / room_category | minilm | 16000 | fixed | c9178f57 |
| star-family-health-optima / room_category | pageindex | 8000 | customer | c9178f57 |
| star-family-health-optima / room_category | pageindex | 8000 | fixed | c9178f57 |
| star-family-health-optima / room_category | pageindex | 16000 | customer | c9178f57 |
| star-family-health-optima / sum_insured | bm25 | 8000 | customer | 4cdeb468, 9ce36574, d47d86dc, 908ec11d |
| star-family-health-optima / sum_insured | bm25 | 8000 | fixed | 4cdeb468, 9ce36574, d47d86dc, 908ec11d |
| star-family-health-optima / sum_insured | bm25 | 16000 | customer | 4cdeb468, 9ce36574, d47d86dc, 908ec11d |
| star-family-health-optima / sum_insured | bm25 | 16000 | fixed | 4cdeb468, 9ce36574, d47d86dc, 908ec11d |
| star-family-health-optima / sum_insured | current | 8000 | fixed | 4cdeb468, 9ce36574, d47d86dc, 908ec11d |
| star-family-health-optima / sum_insured | current | 16000 | fixed | 4cdeb468, 9ce36574, d47d86dc, 908ec11d |
| star-family-health-optima / sum_insured | minilm | 8000 | customer | 4cdeb468, 9ce36574, d47d86dc, 908ec11d |
| star-family-health-optima / sum_insured | minilm | 8000 | fixed | 4cdeb468, 9ce36574, d47d86dc, 908ec11d |
| star-family-health-optima / sum_insured | minilm | 16000 | customer | 4cdeb468, 9ce36574, d47d86dc, 908ec11d |
| star-health-assure / copay | bm25 | 8000 | fixed | 26486fc4, e805caae, 76f45dbe |
| star-health-assure / copay | bm25 | 16000 | fixed | 26486fc4, e805caae, 76f45dbe |
| star-health-assure / copay | current | 8000 | customer | 26486fc4, e805caae, 76f45dbe |
| star-health-assure / copay | current | 8000 | fixed | 26486fc4, e805caae, 76f45dbe |
| star-health-assure / copay | current | 16000 | fixed | 26486fc4, e805caae, 76f45dbe |
| star-health-assure / copay | minilm | 8000 | fixed | 26486fc4, e805caae, 76f45dbe |
| star-health-assure / copay | minilm | 16000 | fixed | 26486fc4, e805caae, 76f45dbe |
| star-health-assure / deductible | bm25 | 8000 | customer | 1175f699, 3192a76d, 03f255d7, 68493f3a, db05310c, 7834309c, 87cda64a |
| star-health-assure / deductible | current | 8000 | customer | 1175f699, 3192a76d, 03f255d7, 68493f3a, db05310c, 7834309c, 87cda64a |
| star-health-assure / deductible | current | 8000 | fixed | 1175f699, 3192a76d, 03f255d7, 68493f3a, db05310c, 7834309c, 87cda64a |
| star-health-assure / deductible | current | 16000 | fixed | 1175f699, 3192a76d, 03f255d7, 68493f3a, db05310c, 7834309c, 87cda64a |
| star-health-assure / deductible | minilm | 8000 | customer | 1175f699, 3192a76d, 03f255d7, 68493f3a, db05310c, 7834309c, 87cda64a |
| star-health-assure / deductible | minilm | 8000 | fixed | 1175f699, 3192a76d, 03f255d7, 68493f3a, db05310c, 7834309c, 87cda64a |
| star-health-assure / deductible | minilm | 16000 | customer | 1175f699, 3192a76d, 03f255d7, 68493f3a, db05310c, 7834309c, 87cda64a |
| star-health-assure / deductible | minilm | 16000 | fixed | 1175f699, 3192a76d, 03f255d7, 68493f3a, db05310c, 7834309c, 87cda64a |
| star-health-assure / deductible | pageindex | 8000 | customer | 1175f699, 3192a76d, 03f255d7, 68493f3a, db05310c, 7834309c, 87cda64a |
| star-health-assure / deductible | pageindex | 16000 | customer | 1175f699, 3192a76d, 03f255d7, 68493f3a, db05310c, 7834309c, 87cda64a |
| star-health-assure / eligibility | bm25 | 8000 | customer | f4511abc, 02ce906d, 9b4088d8, 7dafbf76 |
| star-health-assure / eligibility | bm25 | 16000 | customer | f4511abc, 02ce906d, 9b4088d8, 7dafbf76 |
| star-health-assure / eligibility | current | 8000 | customer | 27c0babc, 4791a913, d8c7c235, 75c98da2, e8c4b7aa |
| star-health-assure / eligibility | current | 8000 | fixed | 27c0babc, 4791a913, d8c7c235, 75c98da2, e8c4b7aa |
| star-health-assure / eligibility | current | 16000 | customer | 27c0babc, 4791a913, d8c7c235, 75c98da2, e8c4b7aa |
| star-health-assure / eligibility | current | 16000 | fixed | 27c0babc, 4791a913, d8c7c235, 75c98da2, e8c4b7aa |
| star-health-assure / eligibility | minilm | 8000 | customer | 27c0babc, 4791a913, d8c7c235, 75c98da2, e8c4b7aa, f4511abc, 02ce906d, 9b4088d8, 7dafbf76 |
| star-health-assure / eligibility | minilm | 8000 | fixed | 27c0babc, 4791a913, d8c7c235, 75c98da2, e8c4b7aa |
| star-health-assure / eligibility | minilm | 16000 | customer | f4511abc, 02ce906d, 9b4088d8, 7dafbf76 |
| star-health-assure / eligibility | pageindex | 8000 | customer | 7dafbf76 |
| star-health-assure / eligibility | pageindex | 8000 | fixed | 7dafbf76 |
| star-health-assure / eligibility | pageindex | 16000 | customer | 7dafbf76 |
| star-health-assure / eligibility | pageindex | 16000 | fixed | 7dafbf76 |
| star-health-assure / family_floater | bm25 | 8000 | customer | 284535f8, 01e811eb, 053e7f99 |
| star-health-assure / family_floater | bm25 | 8000 | fixed | 053e7f99 |
| star-health-assure / family_floater | bm25 | 16000 | customer | 284535f8, 01e811eb, 053e7f99 |
| star-health-assure / family_floater | current | 8000 | customer | 284535f8, 01e811eb, 053e7f99 |
| star-health-assure / family_floater | current | 8000 | fixed | 284535f8, 01e811eb, 053e7f99 |
| star-health-assure / family_floater | current | 16000 | customer | 284535f8, 01e811eb, 053e7f99 |
| star-health-assure / family_floater | current | 16000 | fixed | 284535f8, 01e811eb, 053e7f99 |
| star-health-assure / family_floater | minilm | 8000 | customer | 284535f8, 01e811eb, 053e7f99 |
| star-health-assure / family_floater | minilm | 8000 | fixed | 284535f8, 01e811eb, 053e7f99 |
| star-health-assure / family_floater | minilm | 16000 | customer | 284535f8, 01e811eb, 053e7f99 |
| star-health-assure / family_floater | pageindex | 8000 | customer | 284535f8, 01e811eb, 053e7f99 |
| star-health-assure / family_floater | pageindex | 8000 | fixed | 284535f8, 01e811eb, 053e7f99 |
| star-health-assure / family_floater | pageindex | 16000 | customer | 284535f8, 01e811eb, 053e7f99 |
| star-health-assure / family_floater | pageindex | 16000 | fixed | 284535f8, 01e811eb, 053e7f99 |
| star-health-assure / geography | bm25 | 8000 | customer | 12d92a98, 1a4dc433 |
| star-health-assure / geography | bm25 | 8000 | fixed | 587bb852 |
| star-health-assure / geography | bm25 | 16000 | customer | 12d92a98 |
| star-health-assure / geography | bm25 | 16000 | fixed | 587bb852 |
| star-health-assure / geography | current | 8000 | customer | 12d92a98, 587bb852 |
| star-health-assure / geography | current | 8000 | fixed | 12d92a98, 587bb852 |
| star-health-assure / geography | current | 16000 | customer | 12d92a98, 587bb852 |
| star-health-assure / geography | current | 16000 | fixed | 12d92a98, 587bb852 |
| star-health-assure / geography | minilm | 8000 | customer | 12d92a98, 587bb852 |
| star-health-assure / geography | minilm | 8000 | fixed | 12d92a98, 587bb852 |
| star-health-assure / geography | minilm | 16000 | customer | 12d92a98 |
| star-health-assure / geography | minilm | 16000 | fixed | 587bb852 |
| star-health-assure / geography | pageindex | 8000 | customer | 1a4dc433 |
| star-health-assure / geography | pageindex | 8000 | fixed | 587bb852 |
| star-health-assure / geography | pageindex | 16000 | customer | 1a4dc433 |
| star-health-assure / geography | pageindex | 16000 | fixed | 587bb852 |
| star-health-assure / initial_specific_waiting_periods | bm25 | 8000 | fixed | 574834f7 |
| star-health-assure / initial_specific_waiting_periods | bm25 | 16000 | fixed | 574834f7 |
| star-health-assure / initial_specific_waiting_periods | current | 8000 | customer | 8e38456e, 354cfe46, fa4dcc47, 25dedb1b, aa458242, c6e371b5, 7d1230a7, 9a6a1365, 574834f7 |
| star-health-assure / initial_specific_waiting_periods | current | 8000 | fixed | 574834f7 |
| star-health-assure / initial_specific_waiting_periods | minilm | 8000 | customer | 8e38456e, 354cfe46, fa4dcc47, 25dedb1b, aa458242, c6e371b5, 7d1230a7 |
| star-health-assure / initial_specific_waiting_periods | minilm | 8000 | fixed | 8e38456e, 354cfe46, fa4dcc47, 25dedb1b, aa458242, c6e371b5, 7d1230a7, 9a6a1365, 574834f7 |
| star-health-assure / initial_specific_waiting_periods | minilm | 16000 | fixed | 8e38456e, 354cfe46, fa4dcc47, 25dedb1b, aa458242, c6e371b5, 7d1230a7, 9a6a1365, 574834f7 |
| star-health-assure / maternity | bm25 | 8000 | customer | 273d193c |
| star-health-assure / maternity | bm25 | 8000 | fixed | a83a5dc1, bc886888, a1f6bec6, 278104ae, 273d193c, fae99931, 633285b1 |
| star-health-assure / maternity | bm25 | 16000 | customer | 273d193c |
| star-health-assure / maternity | bm25 | 16000 | fixed | a83a5dc1, bc886888, a1f6bec6, 278104ae |
| star-health-assure / maternity | current | 8000 | customer | 273d193c, 053f65b1, d7a7d175, d0ef5483, d22291fc |
| star-health-assure / maternity | current | 8000 | fixed | a83a5dc1, bc886888, a1f6bec6, 278104ae |
| star-health-assure / maternity | current | 16000 | fixed | a83a5dc1, bc886888, a1f6bec6, 278104ae |
| star-health-assure / maternity | minilm | 8000 | customer | a83a5dc1, bc886888, a1f6bec6, 278104ae, 273d193c, fae99931, 633285b1 |
| star-health-assure / maternity | minilm | 8000 | fixed | a83a5dc1, bc886888, a1f6bec6, 278104ae, 273d193c, fae99931, 633285b1 |
| star-health-assure / maternity | minilm | 16000 | customer | 273d193c, fae99931, 633285b1 |
| star-health-assure / maternity | minilm | 16000 | fixed | a83a5dc1, bc886888, a1f6bec6, 278104ae, fae99931, 633285b1 |
| star-health-assure / maternity | pageindex | 8000 | customer | fae99931, 633285b1, 053f65b1, d7a7d175, d0ef5483, d22291fc |
| star-health-assure / maternity | pageindex | 8000 | fixed | fae99931, 633285b1, 053f65b1, d7a7d175, d0ef5483, d22291fc |
| star-health-assure / maternity | pageindex | 16000 | customer | fae99931, 633285b1, 053f65b1, d7a7d175, d0ef5483, d22291fc |
| star-health-assure / maternity | pageindex | 16000 | fixed | fae99931, 633285b1, 053f65b1, d7a7d175, d0ef5483, d22291fc |
| star-health-assure / newborn | bm25 | 8000 | customer | 2bf98336, 36f1a4a7, 0f32f0a3, ad5f381f, 50dc9cc7, b46cdc81, 01e811eb, 188e5972 |
| star-health-assure / newborn | bm25 | 8000 | fixed | 2bf98336, 36f1a4a7, 0f32f0a3, ad5f381f, 50dc9cc7, b46cdc81, 7f95af2e, 90983c76, 053f65b1, d7a7d175, d0ef5483, d22291fc, 01e811eb, 188e5972 |
| star-health-assure / newborn | bm25 | 16000 | customer | 01e811eb |
| star-health-assure / newborn | bm25 | 16000 | fixed | 36f1a4a7, 0f32f0a3, ad5f381f, 50dc9cc7, b46cdc81, 188e5972 |
| star-health-assure / newborn | current | 8000 | customer | 2bf98336, 36f1a4a7, 0f32f0a3, ad5f381f, 50dc9cc7, b46cdc81, 01e811eb, 188e5972 |
| star-health-assure / newborn | current | 8000 | fixed | 2bf98336, 01e811eb |
| star-health-assure / newborn | current | 16000 | customer | 2bf98336, 01e811eb |
| star-health-assure / newborn | current | 16000 | fixed | 2bf98336, 01e811eb |
| star-health-assure / newborn | minilm | 8000 | customer | 2bf98336, 36f1a4a7, 0f32f0a3, ad5f381f, 50dc9cc7, b46cdc81, 01e811eb, 188e5972 |
| star-health-assure / newborn | minilm | 8000 | fixed | 2bf98336, 36f1a4a7, 0f32f0a3, ad5f381f, 50dc9cc7, b46cdc81, 01e811eb, 188e5972 |
| star-health-assure / newborn | minilm | 16000 | customer | 01e811eb |
| star-health-assure / newborn | minilm | 16000 | fixed | 2bf98336, 188e5972 |
| star-health-assure / newborn | pageindex | 8000 | customer | 01e811eb, 188e5972 |
| star-health-assure / newborn | pageindex | 8000 | fixed | 2bf98336, 01e811eb |
| star-health-assure / newborn | pageindex | 16000 | customer | 01e811eb, 188e5972 |
| star-health-assure / newborn | pageindex | 16000 | fixed | 2bf98336, 01e811eb |
| star-health-assure / ped_waiting_period | bm25 | 8000 | customer | a678e8ea, 8c37a252, 355f3efa, a89aef2a, d1f7f01f, 539e1776 |
| star-health-assure / ped_waiting_period | bm25 | 8000 | fixed | a678e8ea |
| star-health-assure / ped_waiting_period | bm25 | 16000 | customer | a678e8ea, 8c37a252, 355f3efa, a89aef2a, d1f7f01f, 539e1776 |
| star-health-assure / ped_waiting_period | bm25 | 16000 | fixed | a678e8ea |
| star-health-assure / ped_waiting_period | current | 8000 | customer | a678e8ea, 8c37a252, 355f3efa, a89aef2a, d1f7f01f, 539e1776 |
| star-health-assure / ped_waiting_period | current | 8000 | fixed | a678e8ea |
| star-health-assure / ped_waiting_period | current | 16000 | customer | a678e8ea, 8c37a252, 355f3efa, a89aef2a, d1f7f01f, 539e1776 |
| star-health-assure / ped_waiting_period | current | 16000 | fixed | a678e8ea |
| star-health-assure / ped_waiting_period | minilm | 8000 | customer | a678e8ea, 8c37a252, 355f3efa, a89aef2a, d1f7f01f, 539e1776 |
| star-health-assure / ped_waiting_period | minilm | 8000 | fixed | a678e8ea |
| star-health-assure / ped_waiting_period | minilm | 16000 | customer | a678e8ea, 8c37a252, 355f3efa, a89aef2a, d1f7f01f, 539e1776 |
| star-health-assure / ped_waiting_period | minilm | 16000 | fixed | a678e8ea |
| star-health-assure / portability | bm25 | 8000 | customer | a89aef2a, d93726ad |
| star-health-assure / portability | bm25 | 8000 | fixed | 75f1bc46, 8bef6bf5, 881b740f |
| star-health-assure / portability | bm25 | 16000 | fixed | 8bef6bf5 |
| star-health-assure / portability | current | 8000 | customer | 8bef6bf5 |
| star-health-assure / portability | current | 8000 | fixed | 75f1bc46 |
| star-health-assure / portability | current | 16000 | customer | 8bef6bf5 |
| star-health-assure / portability | minilm | 8000 | customer | 8bef6bf5 |
| star-health-assure / portability | minilm | 8000 | fixed | 8bef6bf5 |
| star-health-assure / portability | minilm | 16000 | customer | 8bef6bf5 |
| star-health-assure / portability | minilm | 16000 | fixed | 8bef6bf5 |
| star-health-assure / portability | pageindex | 8000 | customer | 75f1bc46, a89aef2a, d93726ad |
| star-health-assure / portability | pageindex | 16000 | customer | 75f1bc46, a89aef2a, d93726ad |
| star-health-assure / room_category | bm25 | 8000 | customer | 36aabaee, 5b953336, 49f17ef3 |
| star-health-assure / room_category | current | 8000 | customer | 5b953336, 49f17ef3 |
| star-health-assure / room_category | minilm | 8000 | fixed | 36aabaee, 5b953336, 49f17ef3 |
| star-health-assure / sum_insured | bm25 | 8000 | customer | a2d03ebe, 1d98bef4, 4bc97229, bb043259, c84fa49f |
| star-health-assure / sum_insured | bm25 | 16000 | customer | a2d03ebe, 1d98bef4, 4bc97229, bb043259, c84fa49f |
| star-health-assure / sum_insured | current | 8000 | customer | a2d03ebe, 1d98bef4, 4bc97229, 27c0babc, d8c7c235, 4791a913, bb043259, c84fa49f |
| star-health-assure / sum_insured | current | 8000 | fixed | 27c0babc, d8c7c235, 4791a913 |
| star-health-assure / sum_insured | current | 16000 | customer | 27c0babc, d8c7c235, 4791a913 |
| star-health-assure / sum_insured | current | 16000 | fixed | 27c0babc, d8c7c235, 4791a913 |
| star-health-assure / sum_insured | minilm | 8000 | customer | a2d03ebe, 1d98bef4, 4bc97229, 27c0babc, d8c7c235, 4791a913, bb043259, c84fa49f |
| star-health-assure / sum_insured | minilm | 16000 | customer | a2d03ebe, 1d98bef4, 4bc97229, bb043259, c84fa49f |
| star-health-assure / sum_insured | pageindex | 8000 | customer | 27c0babc, d8c7c235, 4791a913, bb043259 |
| star-health-assure / sum_insured | pageindex | 8000 | fixed | bb043259 |
| star-health-assure / sum_insured | pageindex | 16000 | customer | 27c0babc, d8c7c235, 4791a913, bb043259 |
| star-health-assure / sum_insured | pageindex | 16000 | fixed | bb043259 |

## Reference map

| Span ID | Plan | Document / physical page | Raw page span | Characters [start, end) |
|---|---|---|---|---|
| 00369f5e-862f-4cf2-8af2-900073c131b1 | star-comprehensive | star-comprehensive-base-wording / 41 | 1fe34c5d-d0aa-48ea-81c2-9f59e3903527 | [942, 1125) |
| 0165667c-1dc0-4878-930d-cd9f6e2d670a | star-comprehensive | star-comprehensive-prospectus / 52 | 437ee578-b79d-44a2-a05e-99f76e324c7c | [344, 353) |
| 01e811eb-357d-49ec-9bbf-c774c94c90e7 | star-health-assure | star-health-assure-base-wording / 8 | fe779f3b-689f-4b5e-ad23-b98c65f12ea9 | [1669, 1845) |
| 02ce906d-5686-4d68-a164-6635cdc453a8 | star-health-assure | star-health-assure-prospectus / 3 | ed1e3651-39ed-4b7b-a6f3-2088e6c3edc3 | [1646, 2056) |
| 02ff798b-71d3-42a8-aebc-b4b9446ebfd6 | star-family-health-optima | star-family-health-optima-base-wording / 8 | 3dcca608-9bf9-4ebe-ac89-d37c20786769 | [1773, 1807) |
| 03f255d7-e8ac-41e8-8edf-c6ab92e0680a | star-health-assure | star-health-assure-customer-information-sheet / 14 | 4f82328c-5b0c-4b37-ba0b-87981a213a04 | [586, 603) |
| 053e7f99-7c82-4f49-9e02-f9dda47ed730 | star-health-assure | star-health-assure-base-wording / 40 | e6b77b9f-ef6c-48ef-9ed5-2e870cb8ccf7 | [1131, 1272) |
| 053f65b1-d6b0-425b-9b33-e4c085038fdb | star-health-assure | star-health-assure-base-wording / 16 | 29a24c5c-be66-4c7c-ae81-78c84e5271d7 | [2004, 2060) |
| 06979d97-53f4-4973-ae15-9181667313da | star-family-health-optima | star-family-health-optima-base-wording / 9 | 8f2d5061-19e4-46e0-afec-82e011a9e0de | [2037, 2311) |
| 06f072b9-b2d8-4420-b566-ea7478fed5b2 | star-health-assure | star-health-assure-base-wording / 13 | 993588f5-8223-422a-97ae-d11592dea408 | [1064, 1175) |
| 0af1cb90-e355-439f-8221-fa1f1680f46f | star-family-health-optima | star-family-health-optima-base-wording / 14 | 72cdf30a-0c61-4f67-be5a-84c297cc58fc | [2466, 2720) |
| 0bff6acd-9135-45cb-9f67-8ba4b049acee | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [798, 853) |
| 0cad4cbf-9674-4240-9198-865232b5cb93 | star-health-assure | star-health-assure-base-wording / 10 | a8a0ffcf-a19a-4e38-a360-8382a784845c | [163, 420) |
| 0e0fcd39-b6d8-46b0-81fc-3402ed7fa2b7 | star-comprehensive | star-comprehensive-base-wording / 13 | 832fe413-0802-4639-9e14-f26eb385afeb | [2989, 3073) |
| 0f32f0a3-17d6-40a4-b8ce-319f9c91beb7 | star-health-assure | star-health-assure-base-wording / 16 | 29a24c5c-be66-4c7c-ae81-78c84e5271d7 | [1053, 1120) |
| 11584c31-d07f-40cc-991f-1b7abd72d1d7 | star-family-health-optima | star-family-health-optima-base-wording / 36 | beea29f2-55e3-4603-aae9-5e10cecf0cfa | [2536, 2812) |
| 1175f699-2a72-4624-9380-028a8652f143 | star-health-assure | star-health-assure-customer-information-sheet / 14 | 4f82328c-5b0c-4b37-ba0b-87981a213a04 | [352, 528) |
| 117cd3cb-90e3-4b15-9ed4-5f6fa942933c | star-health-assure | star-health-assure-base-wording / 9 | 06e87488-b8c8-4ff0-b1aa-0a876f10104d | [2940, 2973) |
| 121715de-ce0e-45e2-9a59-529555d8d2f9 | star-comprehensive | star-comprehensive-prospectus / 2 | 12f52cb5-6a0d-4e62-ba2d-4f284bff8f05 | [1295, 1528) |
| 129db5b0-75d9-42ef-9f5d-3d2c6f0c98bf | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [577, 717) |
| 12d92a98-e9af-4be8-8781-7a6ee965ac34 | star-health-assure | star-health-assure-base-wording / 39 | 4706f1aa-54e2-4b7f-8f52-4a335f4ccff0 | [2242, 2346) |
| 1340c2bf-38f8-4e51-bd52-b502e7122c91 | star-family-health-optima | star-family-health-optima-customer-information-sheet / 8 | 9d93cf82-4da0-41f4-8b7e-a455776eac3e | [1920, 2096) |
| 14e9720b-70b9-4ab8-b03e-a6b0fe75e77c | star-comprehensive | star-comprehensive-base-wording / 13 | 832fe413-0802-4639-9e14-f26eb385afeb | [2028, 2199) |
| 15c90631-cbae-4c68-85bb-e5f61b3c0347 | star-family-health-optima | star-family-health-optima-base-wording / 28 | 9adf231e-3f59-43d2-a47f-4f47f274ff34 | [2326, 2489) |
| 188e5972-eda3-45bf-a2fa-5a5b6eda4ade | star-health-assure | star-health-assure-base-wording / 32 | a28bb6f9-1459-4a73-9394-370b8a0ee324 | [890, 1017) |
| 1a4dc433-cd2b-4a9e-a25b-8d5a44362f21 | star-health-assure | star-health-assure-base-wording / 9 | 06e87488-b8c8-4ff0-b1aa-0a876f10104d | [2164, 2312) |
| 1d98bef4-b991-41ee-9317-c44f1c56ecab | star-health-assure | star-health-assure-prospectus / 3 | ed1e3651-39ed-4b7b-a6f3-2088e6c3edc3 | [1287, 1450) |
| 1de6b428-3e4f-4dd2-bd98-34ab62097aca | star-comprehensive | star-comprehensive-base-wording / 44 | 7740dd5a-4799-425e-91bd-72d3edc93283 | [1258, 1342) |
| 1eaf4639-5d52-48fe-aba4-720b09fdbeb3 | star-comprehensive | star-comprehensive-prospectus / 52 | 437ee578-b79d-44a2-a05e-99f76e324c7c | [464, 466) |
| 23662334-31db-48c4-b7f4-cc8bc809c82e | star-family-health-optima | star-family-health-optima-customer-information-sheet / 12 | ee4f8188-80d9-4ce0-8583-57faada3e99d | [488, 542) |
| 25dedb1b-b0c0-4dad-8ca8-dc2164298444 | star-health-assure | star-health-assure-customer-information-sheet / 8 | 45bc137a-f2d8-451d-9b81-75a1e7b885d5 | [1566, 1852) |
| 26261d47-1fd3-4c9f-a12e-a47c4ca61cff | star-comprehensive | star-comprehensive-base-wording / 34 | 94711633-5762-412f-8b4e-f74c1c3f9fe5 | [2252, 2377) |
| 26486fc4-14c6-499d-9ae4-2a95d171b717 | star-health-assure | star-health-assure-base-wording / 20 | 074d84ee-ad7f-4651-9491-2c8d00ad0a83 | [1289, 1363) |
| 273d193c-784d-465a-9cf4-09c370a9a71f | star-health-assure | star-health-assure-base-wording / 31 | 51a5cc70-d2ea-463c-9454-23762d5edf02 | [1502, 1885) |
| 278104ae-cd61-4a20-ab2d-c7445a01ba7b | star-health-assure | star-health-assure-base-wording / 14 | 17eb3ee1-22a8-4784-bd0d-9a5146540a01 | [1285, 1382) |
| 27c0babc-f1a1-451f-83cd-9b851c1d3c6e | star-health-assure | star-health-assure-prospectus / 2 | 8d475b22-598c-42a8-a90f-7773a3ad6239 | [1799, 1957) |
| 284535f8-90eb-47b8-9450-a4c2c10e85c9 | star-health-assure | star-health-assure-base-wording / 8 | fe779f3b-689f-4b5e-ad23-b98c65f12ea9 | [1014, 1203) |
| 2bf98336-da84-44a3-8a8e-2c5d79b044a8 | star-health-assure | star-health-assure-base-wording / 6 | ccd095e5-8b98-49ab-9b13-fce79250e0ea | [1616, 1711) |
| 2ce1a514-7817-4623-8e2f-5e3a60a52b0e | star-comprehensive | star-comprehensive-base-wording / 41 | 1fe34c5d-d0aa-48ea-81c2-9f59e3903527 | [1126, 1271) |
| 2efa0e68-756c-424f-88ce-8c68aaf43c2e | star-health-assure | star-health-assure-base-wording / 9 | 06e87488-b8c8-4ff0-b1aa-0a876f10104d | [3067, 3075) |
| 2f0f2ec0-40e7-4821-8ea0-3b6021282408 | star-comprehensive | star-comprehensive-prospectus / 2 | 12f52cb5-6a0d-4e62-ba2d-4f284bff8f05 | [1152, 1294) |
| 2f3316d8-3a14-4454-9871-15c0e753fb08 | star-family-health-optima | star-family-health-optima-base-wording / 18 | 4e44ea0d-5c19-43bc-869d-ce9719b79b1c | [171, 248) |
| 2ff623fc-a1ba-4ee2-900e-046998b5964c | star-comprehensive | star-comprehensive-base-wording / 32 | 4b97dbd3-95b7-4189-b99d-ff4026cad6bd | [318, 533) |
| 3192a76d-fc6c-49db-8d92-c154b9b3bb87 | star-health-assure | star-health-assure-customer-information-sheet / 14 | 4f82328c-5b0c-4b37-ba0b-87981a213a04 | [529, 585) |
| 32c72afd-849d-4657-904e-4b667f7fe21b | star-comprehensive | star-comprehensive-base-wording / 31 | 07f429f2-ac0c-4265-a1a0-23950acfe0df | [1779, 1998) |
| 33f19c05-d1e7-4d74-be8f-2317494895c7 | star-comprehensive | star-comprehensive-base-wording / 13 | 832fe413-0802-4639-9e14-f26eb385afeb | [2554, 2662) |
| 354cfe46-cc2b-47f5-92b0-459af3a7db14 | star-health-assure | star-health-assure-customer-information-sheet / 8 | 45bc137a-f2d8-451d-9b81-75a1e7b885d5 | [1255, 1369) |
| 355f3efa-2f28-405d-baa5-7545ff99dc77 | star-health-assure | star-health-assure-base-wording / 27 | 11a810a2-bb01-44fc-ae8b-79ab175dfa7a | [1970, 2074) |
| 36aabaee-4500-4ceb-9b98-40535c310d80 | star-health-assure | star-health-assure-base-wording / 7 | a5b33661-5a87-4138-aefe-66d611394dd9 | [1754, 1899) |
| 36f1a4a7-2906-4b78-93c4-6bf6a9dc70bd | star-health-assure | star-health-assure-base-wording / 16 | 29a24c5c-be66-4c7c-ae81-78c84e5271d7 | [898, 1052) |
| 3c97202e-35dd-4c7f-a996-3821119d3b6f | star-health-assure | star-health-assure-base-wording / 13 | 993588f5-8223-422a-97ae-d11592dea408 | [2332, 2372) |
| 3e9141e0-eaa7-4e05-99e6-da80d6164361 | star-family-health-optima | star-family-health-optima-base-wording / 29 | 0612a134-2922-462e-ad74-e9c0767a5740 | [170, 388) |
| 3f0ebce5-ed95-4beb-bb1c-3076fd6d71d0 | star-comprehensive | star-comprehensive-prospectus / 2 | 12f52cb5-6a0d-4e62-ba2d-4f284bff8f05 | [646, 725) |
| 400e7955-2d2c-4501-91e6-b2cdbb8f1e8a | star-comprehensive | star-comprehensive-base-wording / 13 | 832fe413-0802-4639-9e14-f26eb385afeb | [1837, 2027) |
| 4302cb1b-a2f9-4851-a7ef-2ac2f06deaab | star-comprehensive | star-comprehensive-base-wording / 31 | 07f429f2-ac0c-4265-a1a0-23950acfe0df | [2248, 2535) |
| 43472171-d92a-4319-9425-8774977f6331 | star-comprehensive | star-comprehensive-customer-information-sheet / 17 | 6d8cc600-33aa-45a8-9af0-82466a4f5939 | [1645, 1920) |
| 462bf0e9-fa51-46b4-be67-f106058c8f7a | star-comprehensive | star-comprehensive-prospectus / 2 | 12f52cb5-6a0d-4e62-ba2d-4f284bff8f05 | [1463, 1528) |
| 4791a913-f2c3-4a28-a7e1-d1f3c321923c | star-health-assure | star-health-assure-prospectus / 2 | 8d475b22-598c-42a8-a90f-7773a3ad6239 | [1958, 2129) |
| 48599eb2-b5cc-4640-b334-83209101fb5a | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [718, 757) |
| 48d93d69-4fc9-4b82-b11d-d622a954f349 | star-comprehensive | star-comprehensive-customer-information-sheet / 8 | 91e82395-7f4f-40c5-ad42-e348f994bfe5 | [2135, 2503) |
| 49f17ef3-fab7-44ce-b2a1-c4c045d5f604 | star-health-assure | star-health-assure-base-wording / 46 | 85a7d6d2-a4b7-45be-b80a-f0c990b2e723 | [448, 455) |
| 4a60f92f-185c-4aaa-b562-c7105b8393d3 | star-comprehensive | star-comprehensive-base-wording / 31 | 07f429f2-ac0c-4265-a1a0-23950acfe0df | [1438, 1665) |
| 4a9f9f0a-d74f-477a-9526-6398be348f89 | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [1879, 2106) |
| 4bc97229-a6f7-4d98-be32-08cba51b6295 | star-health-assure | star-health-assure-prospectus / 3 | ed1e3651-39ed-4b7b-a6f3-2088e6c3edc3 | [1451, 1642) |
| 4cdeb468-5249-42de-aa54-dc13ba6c118c | star-family-health-optima | star-family-health-optima-prospectus / 2 | 2f9dbdcc-ea4b-47d5-bd14-846d894034f8 | [1272, 1373) |
| 4de6a765-7330-4a89-9c1c-4fafd6fd7c3c | star-health-assure | star-health-assure-base-wording / 13 | 993588f5-8223-422a-97ae-d11592dea408 | [458, 602) |
| 4f0c4e68-d1e0-40e1-879c-3d3482133605 | star-family-health-optima | star-family-health-optima-prospectus / 2 | 2f9dbdcc-ea4b-47d5-bd14-846d894034f8 | [1502, 1783) |
| 4f8a1bc4-e064-4068-8140-1abc4aa6ef72 | star-comprehensive | star-comprehensive-base-wording / 32 | 4b97dbd3-95b7-4189-b99d-ff4026cad6bd | [2318, 2419) |
| 50dc9cc7-030c-4b51-a168-3d0b212ac1f7 | star-health-assure | star-health-assure-base-wording / 16 | 29a24c5c-be66-4c7c-ae81-78c84e5271d7 | [1356, 1509) |
| 5377d39f-0281-4a51-9e76-ab8c355de790 | star-comprehensive | star-comprehensive-prospectus / 2 | 12f52cb5-6a0d-4e62-ba2d-4f284bff8f05 | [729, 1010) |
| 539e1776-7c3f-460e-b314-d8808a2f4f71 | star-health-assure | star-health-assure-base-wording / 27 | 11a810a2-bb01-44fc-ae8b-79ab175dfa7a | [2518, 2731) |
| 5499290a-bec2-4c2d-b892-3fae893dfe53 | star-family-health-optima | star-family-health-optima-base-wording / 8 | 3dcca608-9bf9-4ebe-ac89-d37c20786769 | [1176, 1361) |
| 574834f7-1a72-44ab-b6a0-0e987d24e2a7 | star-health-assure | star-health-assure-customer-information-sheet / 10 | 8a636278-a382-482e-9ea1-f4e72a0557c7 | [149, 343) |
| 57f17af3-28b5-43a8-9ebb-6ffabc900973 | star-health-assure | star-health-assure-base-wording / 13 | 993588f5-8223-422a-97ae-d11592dea408 | [936, 1057) |
| 57f6d07c-5e53-40db-985f-842ffc616f10 | star-family-health-optima | star-family-health-optima-base-wording / 31 | 9c0cc5b4-4e4d-43f6-9bfb-c9484816bba8 | [2287, 2452) |
| 580d47b7-486d-4b44-98ce-94f17543127b | star-comprehensive | star-comprehensive-base-wording / 30 | 0869c7fd-8109-4e99-a76f-2ab7d0a1a15a | [169, 405) |
| 587bb852-bbfb-4fff-ae1e-1b99bdb3992b | star-health-assure | star-health-assure-base-wording / 11 | bd837c11-91d5-4c13-b0ba-6679086c7b53 | [1226, 1298) |
| 5b953336-48fe-497a-aa5c-0dd6a4e69beb | star-health-assure | star-health-assure-base-wording / 46 | 85a7d6d2-a4b7-45be-b80a-f0c990b2e723 | [418, 447) |
| 5d555ab8-60db-4f4d-8ed0-b57e1f9d050a | star-comprehensive | star-comprehensive-base-wording / 44 | 7740dd5a-4799-425e-91bd-72d3edc93283 | [2191, 2408) |
| 611fadc5-e976-429b-bd3b-762e9e403339 | star-health-assure | star-health-assure-base-wording / 13 | 993588f5-8223-422a-97ae-d11592dea408 | [1739, 1758) |
| 633285b1-f93e-4128-94eb-2300bb1dcf30 | star-health-assure | star-health-assure-base-wording / 16 | 29a24c5c-be66-4c7c-ae81-78c84e5271d7 | [1169, 1349) |
| 656eda43-5e88-4ebd-bc16-1b9c19cf5d6b | star-family-health-optima | star-family-health-optima-base-wording / 37 | 6d26ee74-3767-4145-9656-2cacdb4c7d11 | [1415, 1731) |
| 66364ba8-1a6c-4079-af75-ed916b6c6f2c | star-family-health-optima | star-family-health-optima-base-wording / 31 | 9c0cc5b4-4e4d-43f6-9bfb-c9484816bba8 | [2453, 2578) |
| 66dd7df5-a8c3-4e44-884d-902d7691e27f | star-comprehensive | star-comprehensive-base-wording / 13 | 832fe413-0802-4639-9e14-f26eb385afeb | [2293, 2553) |
| 68493f3a-d67d-4f09-921d-c51a655f2601 | star-health-assure | star-health-assure-customer-information-sheet / 14 | 4f82328c-5b0c-4b37-ba0b-87981a213a04 | [604, 639) |
| 68676f5e-3eef-4eb2-882f-4fcbcf8949b3 | star-comprehensive | star-comprehensive-customer-information-sheet / 4 | 97a80481-96b8-474f-93bf-eacfb682872a | [1827, 2211) |
| 6b284f3f-bb61-4c0e-b7f8-8f2e290a7741 | star-comprehensive | star-comprehensive-base-wording / 13 | 832fe413-0802-4639-9e14-f26eb385afeb | [2694, 2988) |
| 6ef58a23-43cb-4dc5-8a0f-d94ec8b45973 | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [919, 1234) |
| 71cb07cd-9a5e-40e3-a262-0c063cc1ec0c | star-family-health-optima | star-family-health-optima-base-wording / 6 | b3475488-7a66-4e34-8d53-dd09866bff10 | [1700, 1794) |
| 750e187d-ebc8-45d7-b22d-2bd51406ec44 | star-family-health-optima | star-family-health-optima-base-wording / 29 | 0612a134-2922-462e-ad74-e9c0767a5740 | [2603, 2741) |
| 75c98da2-656f-4bff-ba8c-9a9f56191d46 | star-health-assure | star-health-assure-prospectus / 3 | ed1e3651-39ed-4b7b-a6f3-2088e6c3edc3 | [293, 364) |
| 75d26eff-45a4-41a5-a6e5-0dcad1da45e3 | star-family-health-optima | star-family-health-optima-base-wording / 31 | 9c0cc5b4-4e4d-43f6-9bfb-c9484816bba8 | [2254, 2452) |
| 75f1bc46-8e3f-4182-99cd-5ce7efb29b25 | star-health-assure | star-health-assure-base-wording / 7 | a5b33661-5a87-4138-aefe-66d611394dd9 | [271, 522) |
| 76f45dbe-3ea0-4bef-bffa-6357c26e42a1 | star-health-assure | star-health-assure-base-wording / 20 | 074d84ee-ad7f-4651-9491-2c8d00ad0a83 | [1402, 1474) |
| 77b88807-0df4-42ca-addb-a0ed1064545a | star-comprehensive | star-comprehensive-base-wording / 13 | 832fe413-0802-4639-9e14-f26eb385afeb | [2864, 2988) |
| 7834309c-aed9-4483-a663-48348c53c0d0 | star-health-assure | star-health-assure-customer-information-sheet / 14 | 4f82328c-5b0c-4b37-ba0b-87981a213a04 | [659, 694) |
| 78fca988-9c65-47b8-87f1-aaecd8f0c987 | star-comprehensive | star-comprehensive-base-wording / 31 | 07f429f2-ac0c-4265-a1a0-23950acfe0df | [2004, 2179) |
| 7a888cdb-0542-49b7-bc3b-4248980896d7 | star-comprehensive | star-comprehensive-customer-information-sheet / 9 | 30b3638b-3dd1-46fe-a320-4b97c97f38fb | [1029, 1551) |
| 7c5b48d8-6c9f-4e6c-bc98-17d4a17bc573 | star-health-assure | star-health-assure-base-wording / 13 | 993588f5-8223-422a-97ae-d11592dea408 | [1176, 1436) |
| 7d1230a7-8b45-41af-a9fb-91240b6afc4a | star-health-assure | star-health-assure-customer-information-sheet / 8 | 45bc137a-f2d8-451d-9b81-75a1e7b885d5 | [2138, 2281) |
| 7dafbf76-b26b-4aae-99e9-6f8f21943f62 | star-health-assure | star-health-assure-prospectus / 4 | 9a6a1f1c-4d52-40b1-b3ab-0bfbf7f90801 | [298, 525) |
| 7f9061c3-b697-4a3f-8c30-84f062b42b59 | star-family-health-optima | star-family-health-optima-base-wording / 28 | 9adf231e-3f59-43d2-a47f-4f47f274ff34 | [1444, 1662) |
| 7f95af2e-4591-4558-8411-b96710039895 | star-health-assure | star-health-assure-base-wording / 16 | 29a24c5c-be66-4c7c-ae81-78c84e5271d7 | [1725, 1934) |
| 816cf854-ed77-448b-a1c5-4a8fec2b6534 | star-health-assure | star-health-assure-base-wording / 13 | 993588f5-8223-422a-97ae-d11592dea408 | [862, 930) |
| 81cbe736-fb3a-4881-9a09-77cc0738a86e | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [404, 554) |
| 81da7282-60bc-4c8c-928b-712730445f15 | star-family-health-optima | star-family-health-optima-base-wording / 10 | 213fb310-fc02-43d2-bbad-c7ca170c78bd | [164, 365) |
| 84af2a32-309f-47d8-9b4c-332766db7e24 | star-comprehensive | star-comprehensive-prospectus / 52 | 437ee578-b79d-44a2-a05e-99f76e324c7c | [1947, 1952) |
| 87cda64a-2c26-4116-83d1-7ff8331b14a3 | star-health-assure | star-health-assure-customer-information-sheet / 14 | 4f82328c-5b0c-4b37-ba0b-87981a213a04 | [695, 773) |
| 881b740f-6ff9-43e9-b5ec-06e1f78491ec | star-health-assure | star-health-assure-base-wording / 36 | a1916f60-a5fc-42b1-bd92-df84d88ba331 | [1819, 2094) |
| 884119df-4ac7-49fd-bee0-e12cc90676e8 | star-comprehensive | star-comprehensive-customer-information-sheet / 8 | 91e82395-7f4f-40c5-ad42-e348f994bfe5 | [1555, 2134) |
| 89d7ca0a-c034-40d4-99c9-30a6c5b928de | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [2112, 2217) |
| 8a108a2e-9f2f-4a1e-8156-21901a5b3137 | star-comprehensive | star-comprehensive-base-wording / 34 | 94711633-5762-412f-8b4e-f74c1c3f9fe5 | [2035, 2246) |
| 8bef6bf5-eee8-424f-82b7-901cf036ef68 | star-health-assure | star-health-assure-base-wording / 36 | a1916f60-a5fc-42b1-bd92-df84d88ba331 | [1494, 1813) |
| 8c37a252-269d-45d9-b932-45c166276a2a | star-health-assure | star-health-assure-base-wording / 27 | 11a810a2-bb01-44fc-ae8b-79ab175dfa7a | [1693, 1965) |
| 8d79e37a-f2af-430b-b8e8-5d21864a22ac | star-comprehensive | star-comprehensive-customer-information-sheet / 8 | 91e82395-7f4f-40c5-ad42-e348f994bfe5 | [1166, 1425) |
| 8e38456e-d9ca-4a6b-9688-ed90b84208fb | star-health-assure | star-health-assure-customer-information-sheet / 8 | 45bc137a-f2d8-451d-9b81-75a1e7b885d5 | [1058, 1251) |
| 8ef21c1d-376b-460d-b3a2-5c367b8f31af | star-comprehensive | star-comprehensive-customer-information-sheet / 9 | 30b3638b-3dd1-46fe-a320-4b97c97f38fb | [1552, 2005) |
| 8f2dea70-a925-4447-8a5d-f3f6d47abf16 | star-comprehensive | star-comprehensive-base-wording / 7 | 5b320602-24ee-4fdb-b173-1f0001230353 | [2741, 2909) |
| 8f3743fe-b7f7-48e7-95ca-1c40cc425374 | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [1258, 1303) |
| 908ec11d-8922-4053-a4da-fbe7574c120f | star-family-health-optima | star-family-health-optima-prospectus / 2 | 2f9dbdcc-ea4b-47d5-bd14-846d894034f8 | [1244, 1267) |
| 90983c76-1975-443c-bff2-24194dbc1e5c | star-health-assure | star-health-assure-base-wording / 16 | 29a24c5c-be66-4c7c-ae81-78c84e5271d7 | [1940, 2003) |
| 90c25a6c-c8b0-4a1d-b166-137ad7e47de9 | star-family-health-optima | star-family-health-optima-base-wording / 8 | 3dcca608-9bf9-4ebe-ac89-d37c20786769 | [2462, 2556) |
| 93fe5c04-c5d3-4053-90da-12169a4c5b0d | star-family-health-optima | star-family-health-optima-customer-information-sheet / 8 | 9d93cf82-4da0-41f4-8b7e-a455776eac3e | [1697, 1919) |
| 978bb899-ba5e-4584-99cc-036bfc86a0b8 | star-family-health-optima | star-family-health-optima-base-wording / 8 | 3dcca608-9bf9-4ebe-ac89-d37c20786769 | [1606, 1807) |
| 97ab8d21-bc17-44ed-b084-f1b232996e24 | star-comprehensive | star-comprehensive-customer-information-sheet / 9 | 30b3638b-3dd1-46fe-a320-4b97c97f38fb | [550, 1028) |
| 97e40a10-5f7a-4b21-ab8d-ac2b20698d4c | star-family-health-optima | star-family-health-optima-base-wording / 14 | 72cdf30a-0c61-4f67-be5a-84c297cc58fc | [2003, 2274) |
| 9839e4c8-db99-452c-8df2-3188b4e250c1 | star-family-health-optima | star-family-health-optima-base-wording / 37 | 6d26ee74-3767-4145-9656-2cacdb4c7d11 | [1415, 1849) |
| 99423a38-8676-4d84-8d6f-df03f3bfc13f | star-family-health-optima | star-family-health-optima-base-wording / 14 | 72cdf30a-0c61-4f67-be5a-84c297cc58fc | [2275, 2443) |
| 9a6a1365-d5e6-4083-8518-4f0b7d026993 | star-health-assure | star-health-assure-customer-information-sheet / 8 | 45bc137a-f2d8-451d-9b81-75a1e7b885d5 | [2285, 2505) |
| 9abcb9f3-de4a-46a4-a146-26fbfd5d6e3c | star-family-health-optima | star-family-health-optima-base-wording / 28 | 9adf231e-3f59-43d2-a47f-4f47f274ff34 | [165, 273) |
| 9ae112c8-3150-4455-8c21-d1c5c9b52e40 | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [758, 797) |
| 9b371278-56e6-41f5-b4b5-8ad4f19db7fb | star-comprehensive | star-comprehensive-base-wording / 31 | 07f429f2-ac0c-4265-a1a0-23950acfe0df | [1671, 1773) |
| 9b4088d8-20de-4c66-9b55-cc7752fa69ea | star-health-assure | star-health-assure-prospectus / 3 | ed1e3651-39ed-4b7b-a6f3-2088e6c3edc3 | [2390, 2532) |
| 9c682f5e-f557-4648-a0b4-be43dec3a3ee | star-comprehensive | star-comprehensive-base-wording / 39 | 3bd95077-02ac-41fb-b855-001cb72ac0f4 | [943, 1070) |
| 9ce36574-9410-474d-b048-ef8d9b36f476 | star-family-health-optima | star-family-health-optima-prospectus / 2 | 2f9dbdcc-ea4b-47d5-bd14-846d894034f8 | [1375, 1498) |
| 9d399bc2-52d4-4f95-b51d-e01e81ffb3be | star-family-health-optima | star-family-health-optima-base-wording / 40 | 260f8253-cefd-434c-b93b-b17bd2ffc61c | [2271, 2351) |
| 9e756468-5f23-4e39-bd10-7a2574960346 | star-health-assure | star-health-assure-base-wording / 9 | 06e87488-b8c8-4ff0-b1aa-0a876f10104d | [3025, 3066) |
| 9ed1a8ce-338e-49aa-8915-e6c52799d8ce | star-comprehensive | star-comprehensive-base-wording / 45 | 0b9e14a9-91d2-42ba-bc1a-d6a55ab36ca6 | [1128, 1275) |
| a0e3529d-1208-450b-be23-cd277912085b | star-family-health-optima | star-family-health-optima-base-wording / 28 | 9adf231e-3f59-43d2-a47f-4f47f274ff34 | [1330, 1438) |
| a1f6bec6-0979-40a1-a09a-21b01dbf32c6 | star-health-assure | star-health-assure-base-wording / 14 | 17eb3ee1-22a8-4784-bd0d-9a5146540a01 | [1113, 1284) |
| a1ff0a22-e558-4d39-b62b-77e111f9eb92 | star-family-health-optima | star-family-health-optima-base-wording / 10 | 213fb310-fc02-43d2-bbad-c7ca170c78bd | [366, 764) |
| a20358ac-4955-4e8a-b9ee-4b71c21780b3 | star-comprehensive | star-comprehensive-base-wording / 31 | 07f429f2-ac0c-4265-a1a0-23950acfe0df | [2541, 2649) |
| a261e3f7-f716-430d-b4a3-175034772aba | star-health-assure | star-health-assure-base-wording / 9 | 06e87488-b8c8-4ff0-b1aa-0a876f10104d | [2993, 3024) |
| a2d03ebe-d995-4a18-a1d2-7a15c8bcb8a8 | star-health-assure | star-health-assure-prospectus / 3 | ed1e3651-39ed-4b7b-a6f3-2088e6c3edc3 | [1200, 1263) |
| a31d66e0-5630-4fdd-bac4-c2c21cfa9c24 | star-health-assure | star-health-assure-base-wording / 13 | 993588f5-8223-422a-97ae-d11592dea408 | [322, 452) |
| a3592ab2-9238-484a-9fa6-6aeb6378d38f | star-family-health-optima | star-family-health-optima-base-wording / 9 | 8f2d5061-19e4-46e0-afec-82e011a9e0de | [628, 980) |
| a5f260de-d2c4-43ae-ae11-c9590359391e | star-family-health-optima | star-family-health-optima-base-wording / 36 | beea29f2-55e3-4603-aae9-5e10cecf0cfa | [2210, 2529) |
| a678e8ea-6d1b-4be1-ada2-b9cdbda03ab7 | star-health-assure | star-health-assure-base-wording / 27 | 11a810a2-bb01-44fc-ae8b-79ab175dfa7a | [1430, 1692) |
| a714bb41-4fe6-45ed-9014-616c54c70af6 | star-comprehensive | star-comprehensive-customer-information-sheet / 9 | 30b3638b-3dd1-46fe-a320-4b97c97f38fb | [193, 549) |
| a83a5dc1-b61d-4b9a-adde-f43c8ee42660 | star-health-assure | star-health-assure-base-wording / 14 | 17eb3ee1-22a8-4784-bd0d-9a5146540a01 | [548, 747) |
| a89aef2a-49c9-4e59-9dc0-db40a2914413 | star-health-assure | star-health-assure-base-wording / 27 | 11a810a2-bb01-44fc-ae8b-79ab175dfa7a | [2080, 2300) |
| a8c40883-7942-4cfd-bc8c-edcf40ac3560 | star-family-health-optima | star-family-health-optima-base-wording / 17 | 268bf491-63bc-4724-bd98-b0cac3bbfde9 | [2506, 2642) |
| aa458242-c7cf-4e5e-8245-12e355b83eef | star-health-assure | star-health-assure-customer-information-sheet / 8 | 45bc137a-f2d8-451d-9b81-75a1e7b885d5 | [1856, 1965) |
| abb1238b-7bd5-4173-839f-5e4260106e9d | star-family-health-optima | star-family-health-optima-base-wording / 28 | 9adf231e-3f59-43d2-a47f-4f47f274ff34 | [171, 313) |
| ad5f381f-5847-4142-8457-e3fd87e6067d | star-health-assure | star-health-assure-base-wording / 16 | 29a24c5c-be66-4c7c-ae81-78c84e5271d7 | [1174, 1349) |
| af251711-a9dc-45a2-8098-9faa0233a91a | star-comprehensive | star-comprehensive-prospectus / 2 | 12f52cb5-6a0d-4e62-ba2d-4f284bff8f05 | [634, 725) |
| b053a313-b6a0-46a0-adf2-115436e36a57 | star-family-health-optima | star-family-health-optima-base-wording / 8 | 3dcca608-9bf9-4ebe-ac89-d37c20786769 | [1606, 1772) |
| b0bde587-be48-44dd-a418-129f3f5e9c49 | star-comprehensive | star-comprehensive-base-wording / 13 | 832fe413-0802-4639-9e14-f26eb385afeb | [2200, 2292) |
| b0e56bdc-fc1b-4c2d-8d11-28b0ea9dd885 | star-comprehensive | star-comprehensive-customer-information-sheet / 17 | 6d8cc600-33aa-45a8-9af0-82466a4f5939 | [1319, 1638) |
| b3739119-b9cb-4b94-a890-54f59e6b480f | star-family-health-optima | star-family-health-optima-base-wording / 9 | 8f2d5061-19e4-46e0-afec-82e011a9e0de | [164, 264) |
| b43d95b6-c085-4581-84ad-c3b6f1b5a868 | star-health-assure | star-health-assure-base-wording / 9 | 06e87488-b8c8-4ff0-b1aa-0a876f10104d | [2974, 2992) |
| b46cdc81-be56-4d92-aa1c-8d538f28b8fd | star-health-assure | star-health-assure-base-wording / 16 | 29a24c5c-be66-4c7c-ae81-78c84e5271d7 | [1517, 1718) |
| b7f4fcf9-d317-4baf-8681-ba7c4f654d57 | star-health-assure | star-health-assure-base-wording / 9 | 06e87488-b8c8-4ff0-b1aa-0a876f10104d | [3076, 3233) |
| bb043259-3f07-4b49-987a-fac12badbcba | star-health-assure | star-health-assure-customer-information-sheet / 18 | d1dc94e5-ac31-4753-979c-913c33b5e16f | [1916, 2215) |
| bc19e01c-180d-4dd1-a7ca-3e24c8160954 | star-family-health-optima | star-family-health-optima-base-wording / 28 | 9adf231e-3f59-43d2-a47f-4f47f274ff34 | [165, 313) |
| bc886888-8b3e-432a-be12-ddc2da895b01 | star-health-assure | star-health-assure-base-wording / 14 | 17eb3ee1-22a8-4784-bd0d-9a5146540a01 | [748, 1112) |
| bd036fd6-ee83-4665-8cf7-42ee451ee56c | star-comprehensive | star-comprehensive-base-wording / 31 | 07f429f2-ac0c-4265-a1a0-23950acfe0df | [2655, 2821) |
| bebedaca-8cad-42cf-a8c2-b96e363e3449 | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [1417, 1710) |
| bf6cb657-ac5b-49aa-9c41-1deb2fab09f4 | star-family-health-optima | star-family-health-optima-base-wording / 28 | 9adf231e-3f59-43d2-a47f-4f47f274ff34 | [2494, 2630) |
| bf8e8e1d-bbc6-4ab9-8394-5417f2e6a050 | star-family-health-optima | star-family-health-optima-base-wording / 18 | 4e44ea0d-5c19-43bc-869d-ce9719b79b1c | [254, 476) |
| c02e2cdd-20d1-4a2d-a853-70d1531ffc47 | star-family-health-optima | star-family-health-optima-base-wording / 14 | 72cdf30a-0c61-4f67-be5a-84c297cc58fc | [3091, 3203) |
| c0b4e87e-76fb-47ee-b0cc-8c89f1787cb4 | star-family-health-optima | star-family-health-optima-prospectus / 2 | 2f9dbdcc-ea4b-47d5-bd14-846d894034f8 | [1784, 1922) |
| c0bd8f0a-195c-4616-8a9a-a8cc63d5f0de | star-comprehensive | star-comprehensive-base-wording / 9 | 20ff97c6-7758-4a9d-a36b-847bb468e9af | [1688, 1793) |
| c1a593ca-fa46-41c9-9ee5-4bf99a238a14 | star-family-health-optima | star-family-health-optima-base-wording / 37 | 6d26ee74-3767-4145-9656-2cacdb4c7d11 | [1025, 1409) |
| c26dd448-a724-4b92-b8c6-6cb8f83a619e | star-family-health-optima | star-family-health-optima-base-wording / 41 | e3a3297b-ae95-4787-85af-d2a0bd0fdcbf | [1093, 1183) |
| c34d6bfb-16ef-4242-bf47-a8b417177af5 | star-family-health-optima | star-family-health-optima-base-wording / 37 | 6d26ee74-3767-4145-9656-2cacdb4c7d11 | [853, 1018) |
| c607dbd3-79eb-4e5a-b2e0-5d9b26584151 | star-comprehensive | star-comprehensive-base-wording / 9 | 20ff97c6-7758-4a9d-a36b-847bb468e9af | [2128, 2384) |
| c668c3fd-87ef-4ae1-a52b-453f43d78004 | star-comprehensive | star-comprehensive-base-wording / 39 | 3bd95077-02ac-41fb-b855-001cb72ac0f4 | [573, 771) |
| c6e371b5-adc8-4246-943b-724bd4d0599b | star-health-assure | star-health-assure-customer-information-sheet / 8 | 45bc137a-f2d8-451d-9b81-75a1e7b885d5 | [1969, 2134) |
| c785f5ad-89f0-471a-bdc4-bd60701b0607 | star-family-health-optima | star-family-health-optima-base-wording / 29 | 0612a134-2922-462e-ad74-e9c0767a5740 | [790, 1028) |
| c7fb3038-22b6-4113-84b5-570da19031c8 | star-family-health-optima | star-family-health-optima-base-wording / 21 | 9728a7bb-b4d2-4724-a640-4cdd106cce6e | [1405, 1716) |
| c84fa49f-7d95-4c06-9611-939815c8f221 | star-health-assure | star-health-assure-prospectus / 3 | ed1e3651-39ed-4b7b-a6f3-2088e6c3edc3 | [1646, 1916) |
| c8dba22a-ea23-4b5f-9de3-9d983c7da032 | star-family-health-optima | star-family-health-optima-base-wording / 29 | 0612a134-2922-462e-ad74-e9c0767a5740 | [2291, 2477) |
| c9030eae-ba4a-4bf1-935b-f0174afc9d57 | star-comprehensive | star-comprehensive-base-wording / 39 | 3bd95077-02ac-41fb-b855-001cb72ac0f4 | [772, 942) |
| c9178f57-3dac-478a-8a4c-67c7ae4114ba | star-family-health-optima | star-family-health-optima-base-wording / 8 | 3dcca608-9bf9-4ebe-ac89-d37c20786769 | [202, 813) |
| c99d29d7-f1a5-4ac4-aa24-0669cfa25130 | star-family-health-optima | star-family-health-optima-base-wording / 14 | 72cdf30a-0c61-4f67-be5a-84c297cc58fc | [2721, 2981) |
| cca1d842-6b92-49c8-ad65-9a6cbd09ef9a | star-family-health-optima | star-family-health-optima-base-wording / 29 | 0612a134-2922-462e-ad74-e9c0767a5740 | [2483, 2597) |
| cd0960d6-bb1d-40fa-9813-1624104361fe | star-comprehensive | star-comprehensive-base-wording / 34 | 94711633-5762-412f-8b4e-f74c1c3f9fe5 | [2641, 2772) |
| cd71208a-b340-49da-82f4-6bf566624a1d | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [1304, 1364) |
| ce7bc7ec-d1c6-4348-9213-8393795111aa | star-comprehensive | star-comprehensive-base-wording / 19 | 4f6fefbe-0340-4aaf-9b4b-40169ccca324 | [2566, 2634) |
| d0ef5483-59ad-48c6-89aa-038c95f5d2e8 | star-health-assure | star-health-assure-base-wording / 16 | 29a24c5c-be66-4c7c-ae81-78c84e5271d7 | [2088, 2110) |
| d1bb62e0-8ff1-4f75-ad05-237034222def | star-comprehensive | star-comprehensive-prospectus / 52 | 437ee578-b79d-44a2-a05e-99f76e324c7c | [2703, 2708) |
| d1f7f01f-c5dd-49b0-b567-a6ede6b22e2f | star-health-assure | star-health-assure-base-wording / 27 | 11a810a2-bb01-44fc-ae8b-79ab175dfa7a | [2306, 2517) |
| d22291fc-918e-4ac4-9e47-ec7f01182a0d | star-health-assure | star-health-assure-base-wording / 16 | 29a24c5c-be66-4c7c-ae81-78c84e5271d7 | [2111, 2242) |
| d357a6b7-7ef9-45ad-8a8e-0b430bb59df5 | star-comprehensive | star-comprehensive-prospectus / 3 | 432e1a3a-9f4c-46df-8da9-0056637645f1 | [293, 446) |
| d47d86dc-b52d-4944-b803-fe26df370071 | star-family-health-optima | star-family-health-optima-prospectus / 2 | 2f9dbdcc-ea4b-47d5-bd14-846d894034f8 | [399, 694) |
| d7a7d175-a409-40ec-8278-b310f8ae7715 | star-health-assure | star-health-assure-base-wording / 16 | 29a24c5c-be66-4c7c-ae81-78c84e5271d7 | [2061, 2087) |
| d7ce64a8-c771-4c24-a1f8-f693fab14d4d | star-family-health-optima | star-family-health-optima-base-wording / 12 | e49c2064-7b89-409b-8087-5d09c11d80c4 | [2105, 2170) |
| d8c7c235-f5dc-4737-9878-9daa82a621d8 | star-health-assure | star-health-assure-prospectus / 2 | 8d475b22-598c-42a8-a90f-7773a3ad6239 | [2130, 2347) |
| d8e5099a-d8c2-401c-b430-f7acdbc2177b | star-comprehensive | star-comprehensive-base-wording / 9 | 20ff97c6-7758-4a9d-a36b-847bb468e9af | [1800, 2043) |
| d9335d4d-f758-469c-b99a-2f7a8069ad19 | star-family-health-optima | star-family-health-optima-base-wording / 28 | 9adf231e-3f59-43d2-a47f-4f47f274ff34 | [1911, 2206) |
| d93726ad-f885-4ac0-98ca-7fb62b45cd8a | star-health-assure | star-health-assure-base-wording / 28 | aec1d42b-1597-4b65-8cc1-a5e68af487c2 | [946, 1166) |
| daa0cbca-6653-4ea2-81f9-6582a479ef30 | star-comprehensive | star-comprehensive-prospectus / 52 | 437ee578-b79d-44a2-a05e-99f76e324c7c | [1193, 1198) |
| db05310c-964e-46ba-920b-4907414124aa | star-health-assure | star-health-assure-customer-information-sheet / 14 | 4f82328c-5b0c-4b37-ba0b-87981a213a04 | [640, 658) |
| dcc71f0e-afeb-4c8e-beff-fd923e1ed724 | star-family-health-optima | star-family-health-optima-base-wording / 7 | 4893e951-2b00-41fd-84b9-a815d56f0b27 | [1754, 2010) |
| dda18074-3eb9-437a-88c3-58e5dca47d1a | star-comprehensive | star-comprehensive-prospectus / 2 | 12f52cb5-6a0d-4e62-ba2d-4f284bff8f05 | [1306, 1458) |
| de1d8245-e3e0-4b18-96f1-4bcf01f16583 | star-comprehensive | star-comprehensive-customer-information-sheet / 13 | e12bc2fb-0918-44e3-9170-f74085362c0d | [470, 679) |
| de8beb69-1ac2-4d21-8b48-73cfde6496b2 | star-family-health-optima | star-family-health-optima-base-wording / 29 | 0612a134-2922-462e-ad74-e9c0767a5740 | [434, 591) |
| df58943d-c9cc-4219-92e7-9573541eff5a | star-health-assure | star-health-assure-base-wording / 13 | 993588f5-8223-422a-97ae-d11592dea408 | [764, 855) |
| e041a745-5d16-4c0c-8b2a-1a123a2f9f14 | star-family-health-optima | star-family-health-optima-base-wording / 17 | 268bf491-63bc-4724-bd98-b0cac3bbfde9 | [2148, 2495) |
| e4b533a2-eeb5-40bb-ac55-60cbf75ca689 | star-comprehensive | star-comprehensive-base-wording / 7 | 5b320602-24ee-4fdb-b173-1f0001230353 | [2279, 2506) |
| e6a35708-f502-4128-816b-077980afb7e4 | star-comprehensive | star-comprehensive-customer-information-sheet / 13 | e12bc2fb-0918-44e3-9170-f74085362c0d | [274, 460) |
| e6d9dd21-63cd-4b32-aa6a-bf16099d376d | star-family-health-optima | star-family-health-optima-customer-information-sheet / 8 | 9d93cf82-4da0-41f4-8b7e-a455776eac3e | [1355, 1584) |
| e778d0fd-6a5e-45f9-b019-ee033de5a2a9 | star-comprehensive | star-comprehensive-base-wording / 8 | b9a87d61-3798-4bf1-a45b-cf2fc80e038e | [2197, 2528) |
| e805caae-9c59-4da0-aae9-ec377c9a888e | star-health-assure | star-health-assure-base-wording / 20 | 074d84ee-ad7f-4651-9491-2c8d00ad0a83 | [1364, 1401) |
| e843f1b4-7df6-489d-9d40-2bf495e3e44c | star-health-assure | star-health-assure-base-wording / 9 | 06e87488-b8c8-4ff0-b1aa-0a876f10104d | [2913, 2939) |
| e8c4b7aa-b476-443f-a81a-7690a841a3f2 | star-health-assure | star-health-assure-prospectus / 3 | ed1e3651-39ed-4b7b-a6f3-2088e6c3edc3 | [369, 609) |
| e8eff439-735d-488e-a2d4-9caa1564b22c | star-comprehensive | star-comprehensive-prospectus / 52 | 437ee578-b79d-44a2-a05e-99f76e324c7c | [3469, 3486) |
| e9183b67-5521-4c6a-a507-5c39f318076a | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [854, 913) |
| ed10e2bd-8ebd-46fe-bafe-8685372e8012 | star-family-health-optima | star-family-health-optima-customer-information-sheet / 12 | ee4f8188-80d9-4ce0-8583-57faada3e99d | [964, 1171) |
| edafdaff-70f4-46f3-8640-6319a165adb3 | star-family-health-optima | star-family-health-optima-customer-information-sheet / 8 | 9d93cf82-4da0-41f4-8b7e-a455776eac3e | [1585, 1696) |
| ef5054a6-c796-480b-b4db-55ea9b22117b | star-comprehensive | star-comprehensive-customer-information-sheet / 8 | 91e82395-7f4f-40c5-ad42-e348f994bfe5 | [969, 1165) |
| f15b151a-956b-42a1-9ff7-13cd12b954cd | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [2222, 2316) |
| f2472395-eeee-4e88-9ef8-04dd6d4c288f | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [1717, 1833) |
| f29a066b-7064-4a4b-9e62-7854df121c15 | star-health-assure | star-health-assure-base-wording / 13 | 993588f5-8223-422a-97ae-d11592dea408 | [609, 756) |
| f4511abc-a1d5-4b6c-b168-c1920756ee46 | star-health-assure | star-health-assure-prospectus / 3 | ed1e3651-39ed-4b7b-a6f3-2088e6c3edc3 | [1266, 1642) |
| f5886007-d9ef-44da-a81f-37537d1b31a7 | star-family-health-optima | star-family-health-optima-base-wording / 31 | 9c0cc5b4-4e4d-43f6-9bfb-c9484816bba8 | [2459, 2578) |
| f5a08a61-e0d8-47b9-a39f-dbb82b537766 | star-comprehensive | star-comprehensive-base-wording / 14 | 6845e8f4-0e08-47d8-af93-ee594a0cc94d | [164, 403) |
| f5a5043d-aa00-44ef-bfb8-346dac1ec162 | star-family-health-optima | star-family-health-optima-base-wording / 17 | 268bf491-63bc-4724-bd98-b0cac3bbfde9 | [2649, 2745) |
| f5cc690f-a697-4038-8ee1-8f85faa8c989 | star-comprehensive | star-comprehensive-base-wording / 7 | 5b320602-24ee-4fdb-b173-1f0001230353 | [1922, 2278) |
| f697f3a1-c6de-415c-8c19-78428a8da3c5 | star-comprehensive | star-comprehensive-base-wording / 6 | f1e37045-2e50-44d4-8f97-79af60cc483a | [844, 939) |
| f7a7e596-11bf-4b9a-acc8-fbc597eff599 | star-family-health-optima | star-family-health-optima-base-wording / 10 | 213fb310-fc02-43d2-bbad-c7ca170c78bd | [846, 1109) |
| fa4dcc47-8e7c-4a9b-a349-26d9a88efba3 | star-health-assure | star-health-assure-customer-information-sheet / 8 | 45bc137a-f2d8-451d-9b81-75a1e7b885d5 | [1373, 1511) |
| fae99931-02b3-431c-81b8-8e66c41381bc | star-health-assure | star-health-assure-base-wording / 16 | 29a24c5c-be66-4c7c-ae81-78c84e5271d7 | [775, 1120) |
| fe47e0eb-5169-422d-acb9-f921ef7f1561 | star-family-health-optima | star-family-health-optima-base-wording / 29 | 0612a134-2922-462e-ad74-e9c0767a5740 | [2125, 2245) |
| ff380c92-5aaf-4546-a4fe-967350e6e49e | star-family-health-optima | star-family-health-optima-prospectus / 2 | 2f9dbdcc-ea4b-47d5-bd14-846d894034f8 | [826, 1175) |
