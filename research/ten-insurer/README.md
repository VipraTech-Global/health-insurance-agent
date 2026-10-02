# Frozen ten-insurer experiment

Protocol v2 selected **H (hybrid)**. The live application supports H alone; P is preserved only in the byte-identical source snapshot in `protocol-v2-frozen-runtime/` and the original Git revision `bc48709`.

The frozen input fingerprint is `db24172e69e7da37cda1aa7e8d2b46e94f67e8aa39b133bcf25cfed69a731a21`. The local data and call-provenance archive lives at `/home/akhilesh/.local/state/coverguide-star-slice/reports/ten-insurer/bakeoff-v2/`. PDFs remain content-addressed in the parent `objects/` directory. Original pairs were never overwritten. `accounted-pairs/` contains the earliest same-model attempts used for scoring; see `pair-accounting.json` and `output/decisions-log.md` for the runner-label correction.

The source snapshot is a hash-verification archive, not an importable runtime package. For a fresh reproduction, use an isolated checkout of `bc48709`, its recorded document/data identities and protocol; do not replace or rerun the completed local experiment in place. No tuning or alternative live method is enabled by these artifacts.

`account_demo_bakeoff` performs only deterministic accounting and verifies the archived source hashes. `report_demo_rejections` reports paraphrase-only failures from the accounted pairs. Neither command makes AI calls.
