# Star three-plan processing baseline

The unchanged `process_policy_bundle` and `validate_policy_bundle` commands run
sequentially in `coverguide_star_slice`. Logs are preserved in
`~/.local/state/coverguide-star-slice/reports/`. No knowledge release is published.

## Comprehensive: failed before extraction

The first run exited 1. Four documents were blocked at reconciliation: prospectus,
wording, CIS and the modern-treatment schedule. Recorded codes include
`reader_text_disagreement`, `reader_table_text_disagreement` and
`reader_table_disagreement`. Extraction and independent review did not run because
the document gate rejected the bundle; this is not a validated criterion result.

The cover pages contain native labels (`Prospectus` and `Policy Wordings`). The
baseline unnecessarily selects noisy OCR there, then blocks on its disagreement
with Docling. On wording physical page 3, native paragraph assembly interleaves
the two printed columns (for example, AYUSH hospital conditions and congenital
anomaly definitions). None of the 116 generated wording spans is an exact
substring of the preserved raw physical page. This is a concrete source/citation
failure, not an unknown policy benefit.

The full wording table on physical page 10 was rendered and checked against raw
text. Raw text preserves the printed numbers, headers and footnote. Merged cells
still require interpretation against the complete page; raw text alone does not
prove a rule's table association.

## Family Health Optima: failed before extraction

The unchanged run also exited 1 before extraction or independent review. Its
prospectus, wording and CIS were blocked at reconciliation. The prospectus has
one `reader_text_disagreement` and two `reader_table_text_disagreement` issues;
the wording has four table-text disagreements and two table disagreements;
the CIS has three table-text disagreements. The three separate schedules passed.
Figure-count warnings are retained separately and are not the reason for the block.

## Assure: failed before extraction

The unchanged process exited 1 before extraction or independent review, with all
four executable documents blocked. Prospectus, wording and CIS each have a
`reader_text_disagreement`; their table-text/table disagreements are respectively
5/1, 3/2 and 2/1. The modern-treatment schedule has one table disagreement.
Figure-count warnings are retained separately. Validation using the original
`e2728a2` readiness implementation also failed; its separate log is
`star-health-assure-original-baseline-validation.log`.

## Version-2 correction and verification in progress

A version-2-only reader is connected to the existing stage runners. The Assure
baseline process had already loaded the unchanged implementation before this
connection, and completed with that implementation. The corrected reader preserves
complete `pdftotext -raw` physical pages and their character offsets, with no
retrieval, ranking, text splitting or truncation. Exact source identity and quote
checks precede evidence use; reference/excluded captures cannot enter the bundle.

All 16 executable PDFs (374 physical pages) match the separately preserved raw text
exactly. Unmapped diamond bullets at the start of prospectus headings are retained
at their original offsets; Optima physical page 2 and Assure physical page 3 were
visually checked. Unmapped characters inside words and unreadable pages still fail.

The full backend suite passed 341 tests (18 missing-static-directory warnings),
with Django check and migration drift checks passing. After adding the final
publication-threshold and wrong-source-file citation checks, 28 focused processing
and release tests passed. Coverage includes a real-PDF ingestion/reconciliation path,
full-page inclusion, reference exclusion, quote/page/hash/offset tampering,
number/unit mismatches, conditional copay derivation and exactly 13 criteria.
Ruff and `git diff --check` passed. These component checks do not establish
extraction or independent-review success.

The corrected Comprehensive run is in progress. Its first sum-insured model call
returned HTTP 408; the single permitted retry returned an exact-identity Sol
response. Core requests measured about 280 KB, with 200 KB reserved under the
existing application byte bound; the provider reported roughly 73,000 input
tokens. No source text is truncated. These are candidate extraction outputs,
not independently validated benefit findings.

All three unchanged baselines are now complete. None reached rule extraction.
No release is published.
