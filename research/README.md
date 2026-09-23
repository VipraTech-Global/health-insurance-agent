# CoverGuide evidence, scenarios and proposed database

The [database design, revision 26](design/FINAL_DATABASE_DESIGN.md), is implemented for the local neutral-comparison pilot. The requested full original-backed assessment and source reconciliation remain **unfinished**; their unresolved dependencies are preserved explicitly. Production consent, deployment and cutover remain unapproved.

## Current reviewable artifacts

| Deliverable | Current evidence | Read it |
|---|---|---|
| Reference cases | 200 individually authored available-evidence assessments, 10 per family; 56 conditional calculation records; 81 compound cases. All 200 have a bounded expanded-source follow-up: 62 partially resolved public-source assessments and 138 unchanged. | [Source follow-up casebook](reference/casebook-r6/README.md), [base casebook](reference/casebook-r5/README.md), [canonical records](reference/assessments-200-r5.jsonl), [current eight-category map](reference/information-map-r6.json) |
| Independent evaluation | 200 replacement cases, 10 per family, 80 compound cases. Safe export reports 39 completed bounded scopes and 161 unresolved broader scopes. | [Safe summary](reports/evaluation-safe-summary.json), [general information requirements only](reports/evaluation-information-requirements.json) |
| Additional original patterns | Nine supplementary reference cases outside the fixed 400, including claim clocks, interacting deductions and combi cancellation. | [Case-to-field map with artifact paths and hashes](design/additional-case-field-map.json) |
| Legacy reconciliation | All 203 identities retained; all 181 selected-insurer rows now have bounded wording candidates. Exact historical bundles remain incomplete. | [All-row report](reports/source-completion-dependencies-r22.md), [eight-role ledger](reports/source-completion-dependencies-r22.json), [cumulative assessment](registers/legacy-assessment-r22.json) |
| Original corpus | All 2,942 objects hash verified in the r22 snapshot. Manual relevance review covers 352 PDFs and 16 non-PDF originals across all 20 insurers. | [Full accounting](registers/source-corpus-accounting-r22.json), [input manifest](registers/source-corpus-inputs-r22.json), [manual scope evidence](registers/document-scope-r22.json) |
| Database proposal | Revision 26 neutral-comparison application design is implemented locally; the separate benchmark design and production cutover remain gated. | [Simple review guide](design/SIMPLE_DATABASE_REVIEW_GUIDE.md), [final proposal](design/FINAL_DATABASE_DESIGN.md), [every field](design/field-dictionary.md), [complete ERD](design/complete-entity-relationships.mmd), [all 400 safe requirement mappings](design/case-requirement-field-map.json) |
| Verification | Current final-package checks are recorded separately; 80 follow-up regions from 21 originals verified (79 native, one visual). Earlier structural and arithmetic reviews remain separate. | [Current package checks](reports/final-design-verification-r8.json), [source-anchor checks](reports/reference-followup-evidence-verification-r6.json), [reference calculations](reports/reference-calculation-review-r5.json) |

Counts describe preserved records and bounded review, not completed insurance decisions. **Zero full customer decisions, executed adviser successes or frozen independent evaluation cases are claimed.** No knowledge percentage is measurable until independent relevant-rule denominators are established. The original 180/200 overall, 9/10 per family, three-attempt requirement and all 60 robustness checks remain unchanged.

## Sources and unresolved evidence

The 203-row ledger retains 178 source-backed family findings, three unconfirmed aliases, one unresolved identity and 21 rows outside the selected roster. A current original can establish a family and printed UIN while leaving the historical listing edition, accepted options, underwriting, endorsements and complete bundle unresolved. Candidate association is not completed reconciliation. All 20 original insurers remain in scope; Galaxy, Narayana, Zurich Kotak and Generali Central are retained despite having no legacy rows.

The snapshot contains 2,466 PDFs and 476 non-PDF objects. Besides 352 currently classified PDFs, seven retain earlier manual assertions, 2,105 have automated previews only and two lack earlier previews. Sixteen non-PDF originals were manually reviewed; 460 remain unreviewed. All bytes passed hash verification. The frozen r22 snapshot contains 3,420 attempts (2,725 acquired, 695 failed). Two later NPPA attempts failed without preserved bytes, making the current total 3,422 attempts (2,725 acquired, 697 failed); a preserved failure body is not a successfully acquired policy. Thirteen imported objects lack an acquisition-attempt record, with the known legacy import distinguished from unresolved provenance. [Frozen accounting](registers/source-corpus-accounting-r22.json), [current acquisition delta and repeated object-hash verification](registers/source-corpus-delta-r23.json)

Recent original findings include:

- [Galaxy](reports/galaxy-original-inventory-r13.md): serialized download cards, mixed group/accident medical grants, plan-specific rider attachments and a Guardian CIS link returning a Marvel original. [Independent bounded review](reports/galaxy-original-review-r13.json)
- [Narayana](reports/narayana-original-inventory-r13.md): four families and 14 version candidates, newer live-page versions absent from the register, four wording gaps and retained body/table/UIN conflicts.
- [Zurich Kotak and Generali Central](reports/zurich-generali-original-inventory-r13.md): separate combi component issuers, optional/standalone accidental medical grants, schedule-selected formulas and unresolved companion contradictions.
- [iHealth](reports/ihealth-family-reconciliation-r13.md): an accessible official wording explicitly identifies the family; earlier failures for another URL remain preserved. [Independent bounded review](reports/ihealth-source-review-r13.json)

The Star Super Surplus and New India Arogya Sanjeevani full-page candidate inventories remain provisional for atomic rule segmentation and connected dependencies. They are not complete insurer denominators. Every other relevance-classified original also needs its remaining pages, tables, figures, footnotes and connected clauses assessed. [Star candidate inventory](registers/independent-original-inventory-star-ssf-r6.json), [New India inventory](registers/independent-original-inventory-new-india-as-r6.json)

## Evaluation boundary

Implementation/design contexts may read only `reports/evaluation-safe-summary.json` and `reports/evaluation-information-requirements.json`. Do not read `evaluation/`, private question/answer diffs or the combined historical `seeds/scenarios.txt`. Replacement cases are handled by a separate assessor; the shared filesystem is **not** hard access isolation. Exposure and title-only overlap limitations remain recorded. No evaluation questions or case-specific solutions belong in implementation prompts, retrieval indexes or tuning data. [Benchmark storage and protocol](design/benchmark-storage-proposal.md)

The canonical 200 references and their numerical stipulations remain preserved. Their [200 completed bounded source follow-ups](reference/source-followup-200-r6.jsonl) retain case-specific unresolved dependencies; [integration verification](reports/reference-source-followup-integration-r6.json) checks identities, input preservation and calculation counts. The 80 follow-ups for reference families 03–10 have author verification, with independent re-review still outstanding. New originals may provide conditional alternatives or expose conflicts; they cannot change customer facts to make a product fit. Supplemental cases do not inflate the fixed acceptance denominator.

## Design discussion boundary

The proposal is inspectable, but complete source/case work must precede final design approval. The discussion must cover entities, every field, worked decisions, conditional calculations, versions, privacy, corrections, publication and migration. Approval of the overall plan does not approve this database design. Replacement implementation begins only after explicit approval of the resulting revision; production cutover is a separate decision.

The [revision-5 snapshot](design/history/discussion-r5/snapshot-manifest.json), earlier reports and cumulative registers remain historical evidence. [Batch revision audit](reports/source-batch-revision-audit-r22.json) distinguishes corrected report assertions from immutable original bytes.

## Research utilities and storage

Original bytes live in `objects/` under SHA-256 paths; `registers/attempts/` preserves each acquisition attempt, including access failures. Discovery records retain the original page and exact link occurrence. An observed link is not proof of product applicability. Keep originals and their registers together in backups.

The existing research CLI is separate from the running pilot:

```bash
PYTHONPATH=backend .venv/bin/python -m research_workspace --help
PYTHONPATH=backend .venv/bin/python -m research_workspace report
```

Targeted acquisition supports insurer, match and limit filters; success never establishes corpus coverage. Inspect failed/running attempts before recovery. Do not rerun the historical draft initializer over enriched case records. Git-ignore rules for originals, private evaluation material and renders prevent accidental inclusion, but do not constitute an access-control boundary.

The [connected-source issue register](reports/reference-followup-connected-issues-r6.json) retains HIV waiting, newborn-route, family-scope and pharmacy-mode issues. The [historical combi author recheck](reports/combi-author-recheck-r6.json) addressed the earlier three findings and added refusal/reversal events. The final database review rechecked those proposed constraints and corrected membership/payment/event-link inconsistencies. [Current verification](reports/final-design-verification-r8.json) remains document-level evidence, not PostgreSQL runtime qualification or human design approval.
