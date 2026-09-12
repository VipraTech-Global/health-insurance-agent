# Evidence-derived design inputs — incomplete, not a database proposal

The agreed sequence still controls: finish original assessment and all worked cases, then
derive and discuss the complete database proposal. No design approval is requested by this
document. No replacement models, migrations, dependency changes or service changes have been made.

## Case-to-information work

`reference/information-map.json` contains individually authored requirements and a decision
boundary for each of the 200 reference cases. These are requirements assessments, not worked
customer decisions. `reference/assessments-original-backed.jsonl` contains six additional
partial assessments with original passages, synthetic conversation steps, assumptions and four
calculation illustrations. Five separately rearranged Decimal arithmetic checks passed.

The benchmark assessor owns the replacement evaluation questions and solutions. Its only
implementation-facing outputs are `evaluation-safe-summary.json` and
`evaluation-information-requirements.json`. Its private case-to-requirement mapping must remain
with the benchmark custodian. General requirements can inform the design without disclosing
question text, selected examples, expected values or solutions.

## Requirements grounded in observed decisions

| Information to preserve | Reference distinctions | Original or operational basis |
|---|---|---|
| Account owner, payer, proposer and each insured person; legal relationship, dependency and corrections | ref-04-01, ref-03-05, ref-20-03, ref-20-08 | New India definitions 3.2, 3.20 and benefit table 12; customer correction requirement |
| Base product identity, UIN, revision printed inside document, configuration, selected options and individual acceptance | ref-01-10, ref-05-07, ref-18-06 | New India 3.44 and 10.20; Star Super Surplus has Silver and Gold in one wording |
| Distinct assertions and their conflicts, including table headers, exceptions and express precedence | ref-05-01, ref-16-02, ref-09-10 | New India 6.1 versus table 12; 10.16 versus table 12; ambulance grant versus Annexure A |
| Amount, unit, percentage base, cap, calculation ordering, rounding and applicability | ref-11-01, ref-11-04, ref-11-08, ref-11-09 | New India 4.1, 4.3, 9.5; four conditional original-backed calculations |
| Limit ownership by person, family, eye, procedure and policy year; used/reserved amounts | ref-02-03, ref-11-04, ref-12-10 | New India 4.3 per eye/year; definition 3.53 individual/floater; bonus allocation section 5 |
| Continuity, date anchors, increased cover layers and conflicting duration values | ref-15-03, ref-16-01, ref-19-03 | New India 6.1, 6.2, 8 and 10.21; proposed schema must not use one policy-wide waiting date |
| Admissible expense membership and per-hospitalisation or aggregate accumulation | ref-14-01, ref-14-02, ref-14-05, ref-14-07 | Star Super Surplus Silver clause II versus Gold clause III notes 3–5, physical pages 2–4 |
| Owner-specific dated quotes, hospital branches, observation completeness and validity | ref-17-02, ref-17-07, ref-18-01, ref-18-04 | Scenario requirements; no current personal quotes or complete hospital observations established |
| Mandatory linked rules, exclusions, exceptions and conflicts loaded before an answer | ref-03-08, ref-09-01, ref-10-04 | New India daycare list plus cataract wait/cap; a service definition can coexist with an exclusion |
| Saved decision dependencies on facts, originals, accepted terms, calculations and corpus revision | ref-20-04, ref-20-09, ref-20-10 | User's concurrency, reopening, deletion and invalidation requirements |

Authentication, tenant ownership, durable worker events, retries, cancellation, idempotency,
storage access, deletion and audit retention are operational requirements. They require their
own traceability and verification; they are not insurance facts inferred from a policy PDF.

## Original findings that would be lost in a single-value schema

The New India Arogya Sanjeevani original is identified by UIN `NIAHLIP25044V022425` and
SHA-256 `890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce`.
The 45 newly recorded rule observations are in `registers/original-reading-new-india.json`.
All saved passages resolve against its bytes. This proves location, not exhaustive review
or readiness to publish a recommendation.

- Physical page 9, section 6.1 says 36 continuous months for PED; physical page 21 says four
  years. Keep the conflict unresolved until the controlling evidence is established.
- Physical page 19, section 10.16 expressly overrides contrary terms and gives 30 days for
  quarterly/half-yearly instalments; page 21 says 15 days for modes other than yearly. A
  precedence decision needs the overriding passage and its scope, not a generic source rank.
- Physical page 7 provides a road-ambulance benefit, while List I row 67 on page 23 says
  AMBULANCE. Neither keyword matching nor silently deleting one assertion resolves this.
- The cataract cap is per eye in one policy year. Person/family/claim/year alone is insufficient
  to express every observed limit; body-part scope also appears.
- Package-subsumed items differ from excluded items. Deducting both their item price and an
  inclusive package reduction can charge the customer twice.
- The document has 33 physical pages. Early footers say “of 31” and later ones “of 33”. Physical
  and printed page identities must remain distinct.

Star Super Surplus (Floater), UIN `SHAHLIP22034V062122`, SHA-256
`c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31`, contains both
per-hospitalisation and aggregate variants. Its downloaded filename says V17 while its footer
says V18/2025. Neither a product name nor a filename is a safe configuration/version key.
The rotated modern-treatment table remains a reading dependency.

## Unfinished work preventing the complete proposal

The 203 historical listings remain incompletely reconciled. Seven now have specific original
candidates, with version/configuration ambiguity explicit. The broad corpus has only first-two-page
triage, not complete scope classification or a complete original rule denominator. There are five
manual scope classifications, with all other decisions still requiring reading. Source acquisition
and challenge failures remain preserved. No insurer's 90% knowledge denominator is established.

Neither split has 200 completed original-backed cases. The evaluation replacements are unfrozen,
their compound status is authored rather than independently adjudicated, and no hard access
boundary has been established. No adviser acceptance, robustness, performance or migration claim
can be made from these artifacts. The ERD, complete field dictionary, conditional-rule contract,
constraints, indexes, retrieval catalogue and migration mapping remain outstanding until the
case assessment supports them. The pilot remains the running application.
