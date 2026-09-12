# Retrieval operations and all-case mapping

`case-requirement-field-map.json` maps all 200 reference and 200 safe evaluation identifiers to generalized requirements and final application fields. Concrete evaluation questions, values, expected answers and selected evidence remain outside this package.

For every buying/comparison request, the selector:

1. authenticates owner and conversation, loads the exact starting/current profile and resolves the latest fact and requirement version per logical key;
2. identifies the intended insured people and separates family relationship from actual policy membership;
3. filters exact product versions, variants and options using mandatory applicability rules before semantic ranking;
4. loads the complete mandatory rule graph, definitions, exceptions, table axes, footnotes, document precedence and original evidence from the pinned knowledge release;
5. uses BM25/BGE-M3 only to retrieve additional supporting passages within that release;
6. selects date- and scope-specific quotes and provider-network observations;
7. performs deterministic calculations only with known typed inputs and operation order; and
8. persists candidate dispositions, requirement matches, information needs, statements and citations against the final profile revision.

The 20 scenario families exercise first purchase, family composition, children, senior cover, diabetes, other medical history, mental/disability/congenital terms, maternity/newborn, procedures, outpatient/services, deductions, bonus/restoration, employer overlap, top-ups, portability, renewals, hospitals/cashless, quotes, planned-care/waiting-period questions and multi-turn conversation behavior. Every frozen evaluation case must still be a buying/comparison decision. Operational behavior is tested inside the decision rather than counted as advice by itself.

Representative operations include mandatory-rule graph closure, historical policy-version selection, exact table-cell lookup, member-equivalent quote comparison, dated provider-branch matching, current-versus-proposed cover comparison, supported waiting-period arithmetic and atomic recommendation publication. Public claim procedures may be compared as policy features; no customer claim timeline or insurer-receipt inference is created.

Suggested indexes are declared per entity in `field-dictionary.md`. Actual query plans and the five-conversation p95 targets remain unmeasured until implementation with representative knowledge and customer fixtures.
