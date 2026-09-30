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

## Correction verification in progress

A version-2-only reader has been prepared but is not yet connected to stage runners,
so the remaining baseline commands retain their original behavior. It preserves
complete `pdftotext -raw` physical pages and their character offsets, with no
retrieval, ranking, text splitting or truncation. Exact source identity and quote
checks precede evidence use; reference/excluded captures cannot enter the bundle.

All 16 executable PDFs (374 physical pages) match the separately preserved raw text
exactly. Unmapped diamond bullets at the start of prospectus headings are retained
at their original offsets; Optima physical page 2 and Assure physical page 3 were
visually checked. Unmapped characters inside words and unreadable pages still fail.

Nineteen focused tests pass, including a real-PDF ingestion/reconciliation path,
full-page inclusion, reference exclusion, quote/page/hash/offset tampering,
number/unit mismatches and conditional copay derivation. These component checks
do not establish extraction or independent-review success.

Family Health Optima and Assure baseline results remain pending.
