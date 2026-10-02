# Frozen two-method protocol, version 2

This protocol is committed before scored calls. A run additionally freezes content hashes of its document roster, raw pages, maps, sections, reference memberships, queries, prompts, schemas, validators, packet settings and this protocol. A changed input creates a different run; it cannot resume the original run.

## Shared evidence

Build the three existing Star plans, then one family flagship per insurer. Deduplicate physical PDFs by SHA-256 while retaining thirteen evaluation slots. Use PageIndex with summaries and descriptions on. Summaries/descriptions are navigation only. Both arms use identical original-source sections, offsets and a 16,000-token packet budget. Map failures use 1,024-token/128-overlap fallback pieces with page ranges and first lines for navigation. Record omitted sections, missing source dependencies and fallback counts.

## Arms

- H: BM25 (k1=1.5, b=.75) top 20 plus BGE-M3 top 20 (plan-filtered exact pgvector cosine), reciprocal-rank fusion with k=60, then PageIndex selects sections from the full map with candidates marked. Fill the packet with remaining fused candidates in order.
- P: PageIndex selects sections from the full map, without lexical or vector ranking.

All answer calls use the same schema, prompts and six deterministic validators. One code-check correction is permitted. Transport retries and one invalid-JSON/schema retry are separate. Use low reasoning and bounded output through the shared six-slot subscription relay. No independent AI review.

## Questions and scoring

Star uses the existing 39 stored fact cells and their fixed/customer questions (78 queries). Preserve criterion membership and every stored reference span, expected 236 distinct spans. A complete cell requires **both** packets to contain **every** reference span. Report unique-span recall separately.

The answer sheet contains twenty questions for each of thirteen evaluation slots (260 cases): room rent, ICU, PED waiting, specified-disease waiting, maternity, newborn, co-pay, deductible, restoration, no-claim bonus, pre/post hospitalisation, day care, road ambulance, air ambulance, AYUSH, organ donor, domiciliary/home care, health check-up, OPD and cataract. Missing/unavailable cases remain visible and count as unanswered. Repeated Star flagship slots retain their fixed weight and are disclosed.

Score = complete Star cells + (passed answer cases / 260 * 39). Answered means all six deterministic checks passed, not expert verified. Only wrong-plan quotations **shown to the customer after passing all six checks** disqualify an arm. Attempts rejected by the code checks are counted and reported separately and do not disqualify: the check did its job. If both arms qualify, P wins when absolute score difference <=2; otherwise higher score wins. If only one qualifies, it wins. If both are disqualified, the higher score still wins (an exact tie goes to P); the report explicitly states both disqualifications. Live answering is never disabled because of the bake-off result. These rules are the user's explicit decision before any scored call, overriding version 1 and the supplied plan.

## Fairness and persistence

For each question, H and P must use the same model for selection and answering. A Redis model change that splits a pair invalidates the pair; retain the attempts for audit and rerun both on the now-active model. Keep displayed and rejected wrong-plan counts separate. Preserve both across retries; only displayed wrong-plan quotations enter disqualification accounting. Record per-call requested/observed model, queue/model/total time, tokens including cached/reasoning, transport retries and JSON retries. Maps include all contributing model identities and remain reusable under matching cache metadata.

Run independent jobs concurrently and persist terminal results atomically. No new methods or tuning after results. Report table-heavy room/ICU/maternity/newborn/cataract cases separately. Freeze the winner as the sole live search method; move the loser to research and ingest the remaining catalogue with the winner's required indexes only.
