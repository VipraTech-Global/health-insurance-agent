# Star, Care, and Niva Bupa comparison research

Snapshot date: 2026-09-27. This is an internal source inventory and blocked release assessment. It does not publish or change the customer adviser.

## Sources and captured material

- Star: [product list](https://www.starhealth.in/list-products/) and [downloads](https://www.starhealth.in/downloads/), audited in `../star/`. The list has 56 products; 13 are provisional primary hospitalisation candidates, including the three-product pilot.
- Care: [policy terms](https://www.careinsurance.com/other-downloads.html), [CIS](https://www.careinsurance.com/customer-information-sheet.html), [brochures and prospectuses](https://www.careinsurance.com/health-insurance-brochure.html), and [modified or withdrawn products](https://www.careinsurance.com/modified-or-withdrawn-product.html). These four browser-readable pages yielded 197 distinct document links. Direct page capture returned HTTP 403, so their HTML checksums are unavailable. The separate [proposal form page](https://www.careinsurance.com/health-insurance-proposal-forms.html) was located but could not be fully expanded in this snapshot; its links are still a known inventory gap. The 46 current policy wording links yield provisional product/UIN leads, not an independent current roster.
- Niva Bupa: [download centre](https://transactions.nivabupa.com/pages/downloads.aspx), [vernacular proposal forms](https://transactions.nivabupa.com/pages/vernacular.aspx), and [list of products offered](https://www.nivabupa.com/content/dam/nivabupa/PDF/List%20of%20Products%20Offered_22nd%20November%202023.pdf). The PDF roster says it was updated 10 September 2026 and contains 44 machine-parsed product/UIN rows. Preserved page HTML and its JavaScript resolver account for 234 main-page link occurrences, including 15 proposal forms served through product-code URLs, and 207 vernacular proposal-form links. Source checksums are in `niva-source-verification-2026-09-27.json`.

`source-links-2026-09-27.json` has 638 link occurrences across Care and Niva. The isolated artifact root `/home/akhilesh/Projects/coverguide-star-pilot-data/objects/` holds original responses; raw PDFs and HTML are not committed or served. `audit-2026-09-27.json` records 618 clean acquisitions, 15 readable PDFs followed by unexpected HTML in the same response, and five HTTP 404 links. For the 15 mixed responses, the exact HTTP original and a separately checksummed PDF portion are preserved. The five 404s are two older Care Secure wordings and three Niva translated proposal forms. They remain unresolved, even where they may later be classified outside the comparison.

The candidate scope labels are leads only: 20 Care wording rows and 19 Niva roster rows are provisional primary candidates. Twelve Care and 17 Niva rows still need classification. Every document edition, option, variant, schedule, amendment, and exclusion association remains unreviewed. Finding a UIN on the first two PDF pages establishes an identity lead only.

The Niva roster has an exact first-two-page wording UIN match for 40 of 44 entries. The other four use legacy/nonstandard identities or have no UIN in the first two wording pages; none has been silently dropped. No observed wording UIN falls outside the roster. These checks do not resolve document editions or variant applicability.

## Release assessment

`release-assessment-2026-09-27.json` pins the Star snapshot, Care/Niva link register, and audit by SHA-256. It accounts for 56 Star rows, 46 Care wording derived leads, 44 Niva roster rows, and seven comparison criteria. The release gate is **false**. There is no reviewed variant-by-criterion matrix, no cited policy-rule packet, no qualified BM25/MiniLM retrieval on reviewed evidence, and no independently frozen and scored held-out set. Price is unavailable without a current chart or verified quote for a specific configuration. The current five-product demo is not replaced or promoted by this research candidate.

The application rule engine now rejects a release containing multiple variants for a policy version, so a first variant cannot be selected silently. A three-insurer customer release still requires a reviewed, pinned variant-complete manifest and the full app contract, persistence, and UI migration. No customer release has been authorized.

## Reproduce the offline audit

From this worktree, using the project Python environment:

```bash
PYTHONPATH=backend /home/akhilesh/Projects/health-insurance-agent/.venv/bin/python -m research_workspace.three_insurer_catalogue roster --root /home/akhilesh/Projects/coverguide-star-pilot-data --links research/pilots/three-insurer/source-links-2026-09-27.json
PYTHONPATH=backend /home/akhilesh/Projects/health-insurance-agent/.venv/bin/python -m research_workspace.three_insurer_catalogue capture --root /home/akhilesh/Projects/coverguide-star-pilot-data --links research/pilots/three-insurer/source-links-2026-09-27.json --scope all --max-new-bytes 700000000
PYTHONPATH=backend /home/akhilesh/Projects/health-insurance-agent/.venv/bin/python -m research_workspace.three_insurer_catalogue audit --root /home/akhilesh/Projects/coverguide-star-pilot-data --links research/pilots/three-insurer/source-links-2026-09-27.json
PYTHONPATH=backend /home/akhilesh/Projects/health-insurance-agent/.venv/bin/python -m research_workspace.three_insurer_assessment --star-source research/pilots/star/source-snapshot-2026-09-27.json --star-audit research/pilots/star/pilot-audit-2026-09-27.json --links research/pilots/three-insurer/source-links-2026-09-27.json --other-audit research/pilots/three-insurer/audit-2026-09-27.json --output research/pilots/three-insurer/release-assessment-2026-09-27.json
```

The capture command resumes verified originals and retries failures. Refresh the link register against official pages before using this snapshot at a later date. Resolve the Care proposal-form page and every applicable variant document, review complete rules with page citations, then run a genuinely independent held-out release assessment. Any unresolved required bundle blocks release.
