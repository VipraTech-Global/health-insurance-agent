# Star catalogue pilot: source inventory, not a customer release

Snapshot date: 2026-09-27. Official sources: [Star product list](https://www.starhealth.in/list-products/) and [Star downloads](https://www.starhealth.in/downloads/). The source HTML checksums, links, product rows and provisional scope classifications are in `source-snapshot-2026-09-27.json`. Exact PDF capture dates, URLs, SHA-256 checksums, page counts and first-two-page identity triage are in `captures-2026-09-27.json`. The preserved PDF bytes are in the isolated local research artifact root `/home/akhilesh/Projects/coverguide-star-pilot-data/objects/`; they are not committed or served by the app.

The official product list had **56** rows. This inventory marks three named products as the internal pilot, ten more as provisional primary health candidates, and 43 as provisional candidates outside the primary hospitalisation comparison (group, travel, accident, add-on, top-up, outpatient, fixed-benefit or speciality categories). These are classification leads based on official list names/UINs and wording sections, not a final legal-scope decision. Every product still needs variant and option review. The downloads snapshot records **338** PDF links across document roles and categories, including **30** links in the withdrawn-products section.

For the 13 primary candidates, **91** product-document link associations point to **85** distinct PDF URLs. All 85 were captured successfully. The first-two-page triage finds the product's UIN in all **39** policy wording, CIS and prospectus candidates. This verifies an identity string only. It does not establish that their editions, schedules, endorsements, add-ons and exclusions apply together to a particular variant or policy inception date. Documents without a UIN need explicit applicability evidence. The proposal form shared by several products is discovery/underwriting context; it proves no customer's acceptance.

The detailed first-three audit is `pilot-audit-2026-09-27.json`. Star Comprehensive, Family Health Optima and Star Health Assure each have candidate wording, CIS and prospectus documents with matching UIN strings. The audit holds all nine as `edition_unresolved`. It holds eight listed supporting schedules/excluded-expense documents as `applicability_unresolved` and six brochure/proposal associations as `discovery_only`. Product variants, options and complete rule/evidence packets remain unreviewed. Price is `unavailable` because no current premium chart or verified quote was captured for a customer configuration. The audit's `release_ready` value is `false`.

Four invented profiles in `synthetic-profiles.json` cover adult/family/senior age, family composition, sum insured, waiting-period questions, exclusions, add-ons and price. `synthetic-probe-2026-09-27.json` accounts for all 84 profile × product × criterion cells. Every outcome is visibly `unknown` because applicable variants and reviewed policy rules do not yet exist. A separate test injects a mismatched CIS UIN and confirms that it remains unresolved. This is an abstention and accounting exercise, not a test of insurance-answer accuracy.

## Reproduce the research snapshot

From this worktree, with the project Python environment:

```bash
PYTHONPATH=backend /home/akhilesh/Projects/health-insurance-agent/.venv/bin/python -m research_workspace.star_catalogue snapshot --root /home/akhilesh/Projects/coverguide-star-pilot-data
PYTHONPATH=backend /home/akhilesh/Projects/health-insurance-agent/.venv/bin/python -m research_workspace.star_catalogue capture --scope primary --root /home/akhilesh/Projects/coverguide-star-pilot-data
PYTHONPATH=backend /home/akhilesh/Projects/health-insurance-agent/.venv/bin/python -m research_workspace.star_catalogue audit --root /home/akhilesh/Projects/coverguide-star-pilot-data
PYTHONPATH=backend /home/akhilesh/Projects/health-insurance-agent/.venv/bin/python -m research_workspace.star_catalogue probe --root /home/akhilesh/Projects/coverguide-star-pilot-data --profiles research/pilots/star/synthetic-profiles.json
```

`snapshot` fetches only the two official listing pages. `capture` fetches the listed primary-candidate PDFs through the existing HTTPS host allowlist and bounded acquisition routine; preserved originals are content addressed. Re-running `capture` reuses successful captures and retains failed attempts. The committed JSON files are a dated evidence snapshot, so refresh them only after inspecting source changes.

## Completion conditions

Review every candidate's comparison scope, identify every current variant/option, and reconcile each wording, CIS, prospectus, schedule, amendment and endorsement by exact UIN, edition and applicability. Read the complete clauses, definitions, exclusions, limits, tables and footnotes, then compile reviewed rules with complete evidence packets. Re-run the synthetic profiles against those reviewed rules, including actual conflicting-edition and missing-document cases. Until reviewed policy facts exist, these profiles cannot yield justified coverage outcomes.

Repeat the same source-led inventory for each additional insurer. `research_workspace.release_gate.check_release_gate` requires at least two distinct insurers, a verified independent product roster, reviewed scope/variant/document inventories, a complete neutral variant-by-criterion matrix, source-backed supported cells, reasoned unknowns, zero decision-critical errors on an independently scored held-out set, and verified privacy and no-purchase-direction checks. This offline gate is one prerequisite. The current app's PostgreSQL search uses `SearchRank`, not BM25; the selected BM25/MiniLM retrieval path and full multi-insurer domain assessment are still unimplemented and unqualified. No knowledge release or customer route is changed by this pilot.
