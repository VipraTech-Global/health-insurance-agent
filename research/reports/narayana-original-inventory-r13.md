# Narayana: bounded original-source assessment, r13

Four product families are supported by original medical-expense wordings. The assessment accounts for 14 version candidates: all 12 rows in the production product register, plus the newer Aditi V6 and Arya individual V2 originals now linked from the production product page. Narayana remains in the original 20-insurer scope despite having **zero legacy listings**.

This is a bounded identity, grant, configuration and connected-scope assessment. **No full original-rule inventory, issued bundle, historical applicability reconciliation, insurer denominator or adviser acceptance is completed.**

The integration artifact is `research/registers/narayana-original-inventory-r13.json`. It contains 20 newly manually classified PDFs (10 medical-expense wordings and 10 supporting documents), three manually classified HTML navigation sources, 68 evidence regions, exact original hashes and acquisition provenance. Twenty-three original-page renderings were independently inspected, including configuration tables, register rows, footers and extraction anomalies. All 22 acquisition attempts succeeded: 17 PDF downloads and five HTML downloads. Two acquired landing-page HTML objects remain outside manual scope classification. All bytes and immutable attempts are preserved.

## Family and version accounting

| Family | Version | Register UIN | Reviewed wording | Matching published CIS / prospectus candidates |
|---|---|---|---|---|
| Aditi | V1 | NHIHLIP25035V012425 | `31119eb1…`, 39 pages | Neither located in inspected links |
| Aditi | V2 | NHIHLIP25036V022425 | `aaedfa62…`, 41 pages; conflicting title UIN | Neither located |
| Aditi | V3 | NHIHLIP25037V032425 | `655cdc4b…`, 46 pages | Neither located |
| Aditi | V4 | NHIHLIP26040V042526 | `3bfab85f…`, 50 pages | CIS `da45dc78…`; prospectus `87c188ba…` |
| Aditi | V5 | NHIHLIP26044V052526 | Not located | Neither located |
| Aditi | V6 | Not listed; originals print NHIHLIP27048V062627 | `5740f72a…`, 84 pages | CIS `86dae322…`; prospectus `4408adbd…` |
| Arya individual | V1 | NHIHLIP26043V012526 | Not located | Neither located |
| Arya individual | V2 | Not listed; originals print NHIHLIP27047V022627 | `8e3392bb…`, 78 pages | CIS `357a7dd0…`; prospectus `5ab85fab…`, both have conflicting group-name footer |
| Arya Group | V1 | NHIHLGP25038V012425 | `8b9cc2b1…`, 57 pages | Neither located |
| Arya Group | V2 | NHIHLGP26042V022526 | `5093a3c1…`, 57 pages | Neither located |
| Narayana Group | V1 | NHIHLGP25039V012425 | `1d796618…`, 67 pages | Neither located |
| Narayana Group | V2 | NHIHLGP26041V022526 | Not located | Neither located |
| Narayana Group | V3 | NHIHLGP26045V032526 | Not located | Neither located |
| Narayana Group | V4 | NHIHLGP27046V042627 | `f6f6c4d3…`, 93 pages | Neither located |

“Not located” describes work still needed after examining actual production and public insurer staging page links and targeted official-domain search. It is **not proof that the document does not exist or cannot be obtained**. No matching-link HTTP failure occurred. Published companion candidates do not establish the issued schedule, member certificate, accepted underwriting outcome, endorsements or a complete bundle.

The production register `f50fcdc8…` has 12 rows; update register `8b6277e8…` has eight. Both URLs were refreshed and returned byte-identical originals. Historical staging registers `7f070b8b…` and `6f8e98dc…` have eight and five rows respectively. Every row in both update registers says **Updated**; their heading does not establish withdrawal. Production row 11 literally combines an end date of 10-May-2026 with “onwards.” Retain that ambiguity. Open-ended older intervals cannot establish present sale or policy applicability.

## Evidence findings that must survive integration

1. **Aditi V2 has three conflicting identifier assertions.** Its title/footer prints `NHIHLIP25035V022425`; the production and historical registers print `NHIHLIP25036V022425`. The visible disclaimer on physical page 25 prints `NHIHLIP25035V012425`, while the same-page footer prints the V2 identifier. Family identity and a V2-labelled document are supported; the exact regulatory identifier needs resolution. Native text on page 25 also contains repeated/hidden text, so the disclaimer record uses a visible manual transcription.

2. **Production navigation labels lag behind linked originals.** The production product cards display Aditi V5 and Arya individual V1 identifiers but now link V6 and V2 wordings, CIS and prospectuses. The production register omits those newer originals. Preserve the card, anchor, register and document assertions separately. No launch/effective dates for V6/V2 are established here.

3. **Arya individual V2 companions have group-name footers.** The prospectus and CIS titles, CIS row 1, retail UIN and wording support the individual family. Their footer says “Arya Group Health Insurance.” These remain conflicted retail companion candidates; they do not merge the two families.

4. **Original post-hospitalization statements conflict.** Aditi V1 physical page 10 says 60 days preceding admission, while its page 27 table says 90 days post discharge. V2 and V3 body text says 90 days preceding admission while their tables say post discharge. V4 body says 90/180 preceding, but plan tables say post discharge. Arya individual V2 section 3.3(b), physical page 10, says 90 days; physical page 53 gives 180 days by provider for most cells and 90 days at Other Provider under Arya Plus. Narayana Group V4 body/table say preceding/before admission for post-hospitalization, while the V1 schedule table says post discharge. Do not silently repair these originals or publish affected calculation rules without resolution.

5. **Configurations are version-specific.** Aditi V1–V3 tables have Plan 1 and Plan 2; V4 adds Plus Plan; V6 has Plan 1, Plan 2, Plus, Prime, POS–Aditi and POS–Aditi Plus. V6 requires certain selected non-surgical sublimits to be no greater than the selected base SI. Its POS sublimit cells say “Not applicable.” Arya Group V1 lists finite 25/50-lakh and 1-crore choices; V2 also explicitly lists Unlimited. Neither not-applicable nor unlimited can be represented as zero. Older plans cannot acquire later options through a family-level merge.

6. **Public group templates leave material inputs unfilled.** Narayana Group V1/V4 point to the issued Certificate of Insurance/Policy Schedule for SI, room eligibility, amounts, periods and options. V4 prints `<selected option>`. That placeholder is not a policy value. Group membership and actual issued terms remain required for customer applicability.

7. **Provider restrictions and malformed references matter.** Current wordings distinguish Preferred, Verified, Other and Non-Network providers, selected network-access options, emergency/planned treatment and travel/relocation evidence. Some table and body references point to the wrong section or annexure number. The artifact preserves these locations. Full connected annexures, dated provider observations and applicable intimation clauses must be assessed before advice or calculation acceptance. The bounded grant classification does not claim complete provider-rule review.

## Acquisition and review limits

Preserved originals were read first. Production `/product` and `/customer-support` supplied current and historical links. A targeted official-domain search also surfaced the insurer's publicly accessible staging `/product` page, which supplied both group V1 wordings and Aditi V4 companions. Staging provenance is explicitly retained; these files are historical candidates, not proof of current production publication. The staging acquisition's `linking_url` recorded the production URL as navigation context; the artifact explicitly corrects its interpretation: **no production-to-staging anchor was observed; discovery was through web search**.

Seventeen PDF acquisitions produced 17 distinct downloaded PDF hashes, including two unchanged production registers and a byte-identical Aditi V4 wording reached through a second URL. They add 14 PDF byte objects beyond the six initially reviewed preserved originals. Full signed blob URLs are retained in the private acquisition/provenance records; this report uses hashes.

MuPDF emitted seven “No common ancestor in structure tree” warnings while producing renderings. All 23 requested images were produced and visually inspected; the warnings are recorded. Native extraction is a reading aid, not proof of faithful glyph order or an exhaustive rule count. Unread pages, complete exclusion/benefit inventories, full companion reconciliation and connected external originals remain work to perform.

No evaluation data, application code, cumulative registers, schema or reference cases were changed.
