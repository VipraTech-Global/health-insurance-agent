# Section 16 agent PDF spot-checks

Run `section16-a-20261003-04`. These are agent spot-checks, not expert verification. Ten answered application cases were compared with rendered original physical PDF pages; every stored anchor in these cases also resolved to PDF geometry. The check does not establish exhaustive answer correctness.

| Case | Plan | Physical page viewed | Finding |
|---|---|---:|---|
| answer-cataract-0 | Star Comprehensive | 30 | Cataract appears in the specified-disease list with a 24-month waiting condition and exceptions. The displayed answer is primarily waiting-period evidence, not a cataract monetary limit. Extraction also retains a hidden template header absent from the visible page. |
| answer-cataract-0 | Family Health Optima | 5 | The sum-insured, per-eye and per-policy-period table is present. Printed limits remain separate from applicability conditions. |
| answer-cataract-0 | Star Health Assure | 28 | Cataract is in the specified-condition list; the preceding 1/2-year and 3-year policy-term PED distinctions are visible. Answer evidence is broader than the cataract question. |
| answer-cataract-1 | HDFC ERGO Optima Secure | 32 | Cataract appears in the illness table governed by a 24-month wait and accident exception. This is condition evidence, not proof of a cataract amount. |
| answer-cataract-1 | ICICI Lombard Elevate | 38 | INR 30,000 per eye appears in the sub-limit table. Stored page-37 quotations retain the Vital Essence optional-add-on and co-payment context; this must not be treated as universal base cover. |
| answer-air_ambulance-0 | Star Comprehensive | 11 | Rs 2,50,000 per hospitalization and Rs 5,00,000 per policy period, medical advice, nearest hospital and licensing restrictions are present. The excerpt also includes adjacent road-ambulance wording. |
| answer-air_ambulance-0 | Family Health Optima | 12 | 10% of sum insured, emergency/medical-necessity/India/licensing conditions and the Rs 5 lakh minimum-SI note are present. |
| answer-air_ambulance-1 | Star Comprehensive repeated flagship slot | 11 | Independently generated answer retains the original air-ambulance limits and licensing quotation. This repeated slot remains part of the frozen application weighting. |
| answer-air_ambulance-1 | HDFC ERGO Optima Secure | 16 | Benefit and conditions a–g are present, including no return transport and admissible hospitalization. Excerpt also includes adjacent daily-cash wording. |
| answer-air_ambulance-1 | Niva Bupa ReAssure 3.0 | 5 | Classic/Select says NA; Elite/Black says up to INR 5L per hospitalization. Original variant distinctions remain visible; adjacent table rows are also included. |

Limitations found: exact extraction can be verbose and include neighboring clauses or hidden PDF template text. “Full answer” means every proposed unit passed the deterministic checks; it does not prove every aspect of a broad customer question was answered. Three cataract cases above primarily show waiting conditions. These findings must remain in the delivery report and must not be represented as expert-confirmed complete benefit answers.
