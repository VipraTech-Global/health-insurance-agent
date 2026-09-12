# Values and conditional rules — discussion revision 6

This is a proposed representation, not an implemented evaluator. The companion [JSON Schema](json-contracts.schema.json) defines 46 named, closed structures using JSON Schema 2020-12. Every `json:Name` field in the dictionary resolves to one of them. Rule text, SQL and Python expressions are never executed from stored content. Examples containing customer data are synthetic.

## Types and absence

PostgreSQL storage types: `instant` means `timestamptz`; `date` means `date`; `integer` and `bigint` are signed 32/64-bit counts with the stated nonnegative/positive checks; `numeric(p,s)` is exact decimal; `json:Name` is `jsonb` validated against the pinned schema and semantic validator. UUID references are actual FKs except explicitly typed registries, whose deferred triggers resolve a closed target-table allowlist. Native Django authentication IDs keep their native types. Dates and times never stand in for one another.

| Value | Representation | Consequence |
|---|---|---|
| Known zero INR | `{"state":"finite","value":"0","unit":"money","currency":"INR"}` | Exactly zero; can be included in arithmetic |
| Unknown INR | `{"state":"unknown","expected_unit":"money","reason":"No owned current quote"}` | No numeric comparison or assumed affordability |
| Unlimited | `state=unlimited`, dimension and supporting spans | No limit from this rule; other limits still apply |
| Not applicable | `state=not_applicable`, reason and support | This rule has no application, rather than a zero amount |
| Up to sum insured | `ExpressionV1` input reference to the selected SI | Finite dependent ceiling; never labelled unlimited |
| Pending waiting credit | `DurationV1.state=unknown` with reason | No fabricated zero-month credit |
| Unknown date/boundary | Unknown temporal extent or explicit unresolved boundary | Affected eligibility remains unknown |
| Empty array | No recorded entries in that collection | Does not prove absence of disease, endorsement or claim |

Decimal strings preserve exact arithmetic; maximum 24 integer and 12 fractional digits is the proposed representation bound. Money and money-per-day/year carry an ISO currency. Rates are dimensionless ratios (5% = `0.05`), not bare integers; their base is a separately named input. No binary floats for contractual money. Stored results retain the rounding rule and authority. Without contractual rounding evidence, preserve exact intermediate decimal results and mark settlement rounding unresolved. Display formatting must not alter the stored comparison result.

Known durations state calendar months/years or elapsed days/hours/minutes and an explicit anchor. A three-calendar-month entry rule is not converted into 90 days. Anniversary handling for a February 29 inception, exact cutoff inclusivity, local timezone and end-of-day interpretation require governing evidence; unresolved conventions block that boundary. `TemporalExtentV1` separates date, instant, known interval and unknown. Interval bounds retain inclusivity and precision; semantic validation rejects reversed or incomparable intervals.

## Rule representation and evaluation

A `RuleV1` has its schema version, applicability predicate, typed input declarations, one or more effects, mandatory connected rules, original spans, unresolved dependencies and rounding policy. Effects cover definitions, eligibility, grants, exclusions, exceptions, limits, waits, deductions, accumulation, precedence and rights/deadlines. Each effect names its target and limit scope. A fixed absolute limit uses `percentage_base_key=null`; a waiting rule without prior credit uses `credit_input=null`. Those states do not fabricate a numeric base or credit.

`ExpressionV1` is a recursive discriminated union: literal, named input, closed operation, conditional or table lookup. Operations are add/subtract/multiply/divide/min/max/sum/abs/round/calendar_add/elapsed_between. Binary subtraction/division/multiplication/calendar addition require two operands; absolute value one; round and elapsed-between three. Round operands are value, explicit scale and registered rounding code. Elapsed-between operands are start, end and elapsed-unit code. Add/min/max/sum require one or more same-dimension values. A failed divisor or unhandled quantity state is an explicit invalid calculation, never silently zero.

`PredicateV1` supports constants true/false/unknown, all/any/not, comparisons, set membership and input-presence checks. Three-valued logic applies: false AND unknown is false; true AND unknown is unknown; true OR unknown is true; false OR unknown is unknown. All relevant rule dependencies and contradictory evidence are still loaded even if a predicate short-circuits. Presence only establishes that an input record exists; it does not convert an unknown value into a known one.

Unknown arithmetic inputs produce an unknown dependent result. `min(finite, unlimited)` can return the finite bound where both dimensions match; unlimited subtraction/division and zero-times-unlimited are rejected unless the specific operation has an approved semantic rule. Not-applicable values are excluded only by an explicit applicability branch, never coerced numerically. Mixed currencies, money-plus-ratio and dimensionally invalid percentages are invalid. An independently verified intermediate result may remain complete while final entitlement is unresolved.

The publication validator resolves every input and rule key against a pinned vocabulary/corpus. It checks AST depth (proposed 32), node count (proposed 10,000), operation arity, dimensions, allowed field scopes, predicate cardinality, all references and absence of calculation/override cycles. These are proposed safety bounds requiring qualification with the curated corpus; hitting a bound is a visible unsupported-rule failure. Definitions can contain mutually referring language, but retrieval closure must terminate and report an unresolved cycle; it must not recursively execute it.

## Limits, scopes and interacting deductions

`LimitScopeV1` records person/family/claim/admission/illness/body-part/policy/provider subject, actual member IDs, per-event/year/term/lifetime/day period, optional exact period dates, benefit keys and reset rule. Unknown scope or period prevents combining amounts. A policy year is selected from the policy's interval, not calendar year or the employer plan's year.

`ExpenseLine` retains gross bill identity; `ExpenseAllocation` records included package components, distinct payable components, exclusions and time/scope splits. Billing, admissibility, threshold contribution and cover consumption are independent roles. The validator checks no package cycles, no duplicate allocation per role/pool and conservation of finite portions. A line spanning stabilization requires an evidenced time allocation or an explicit hypothetical assumption; a date-only service entry cannot locate the amount before an instant.

`ClaimLineAssessment` stores admissible expense, threshold contribution, cover consumption and actual payment separately. `UsageEntry` records immutable postings and reversals with a stable posting key. A base insurer payment is neither the gross bill nor necessarily the expense admitted by a top-up. Co-pay recovery and premium-debt recovery are different operations. The policy-specific calculation sequence must be evidenced: there is no universal deductible-before-co-pay order.

Rule tables have typed axes, selector ranges, values, original cells and footnotes. The Star Silver table uses deductible as selector; Gold uses sum insured. Exactly all declared axes must be supplied once; overlapping ranges or missing cells produce unknown/conflict, not nearest-cell guessing. The root design includes separate `RuleTable` and `RuleTableCell` records because plain JSON arrays would hide this distinction.

## Versions and semantic validation

Schema version and semantic-validator version are pinned in publication/processing/decision artifacts. Schema-valid does not mean original-supported. Required semantic checks include:

1. Original hash and media-specific OriginalLocatorV1 resolution; real physical page/geometry for PDFs, exact HTML/JSON/text locations otherwise; complete connected clause/table context. Visual transcription is distinguishable from native text.
2. Actual relationship existence, owner and conversation/contract lineage for every referenced ID, including IDs embedded in JSON.
3. Exactly one record for each reconciliation dimension, with unresolved/conflicted dimensions retained.
4. Chronology and precise interval interpretation; valid date/time formats alone are insufficient.
5. Scalar/set/event-series predicate rules, supersession chains and immutable snapshot membership.
6. Table-axis completeness, range overlap and original footnote closure.
7. Event-kind required payloads: decision ID for decision events, message ID for clarification, error code for failure, revision for stale and progress code for progress.
8. Complete material dependencies, source precedence and absence of unsupported critical claims.

Readers/extractors may propose candidates in these shapes. Independently inventoried original rule instances establish the denominator and semantic review establishes support. Parser-produced rules cannot establish their own coverage denominator. Unknown denominators remain unmeasured.


OriginalLocatorV1 has four closed variants. Byte ranges are half-open with end greater than start; JSON pointers resolve against decoded immutable originals, with duplicate-key ambiguity rejected; HTML selectors must resolve the stated occurrence and interpretation using the pinned resolver. Content hashes and references are checked outside JSON Schema. ReconciliationV1 requires six separate dimensions: family, variant, observed source revision, historical version, complete bundle and applicability. A current wording/UIN can resolve the observed-source dimension while historical association remains unknown.


## Discussion revision 5 additions

The companion now defines 50 closed JSON structures. `ClaimPartyV1` distinguishes the exact insurer, person, provider or named intermediary and never infers authority from a name. `ClaimDocumentationV1` pins requirement, receipt and rule revisions; complete status requires no unresolved keys and a supporting rule, with cross-record completeness checked separately. `InventoryCountingProtocolV1` preserves independent origin, atomicity, hierarchy, repeated-occurrence and shared-cell policies. `InventorySourceManifestV1` binds original document identities, byte hashes and instance keys. Candidate segmentation remains explicitly unresolved until adjudicated; schema-valid JSON alone cannot approve a denominator.

`CalculationInputsV1` can bind source artifact IDs for claim-document, payment and rate inputs. Those IDs must resolve within the allowed owner scope and to the exact retained revision. New structures follow the same three-valued unknown handling, source provenance and semantic-validation requirements as the existing rule expressions. JSON structure validation does not verify that a stated document is necessary, that a recipient has insurer authority, or that an inventory is complete.

## Versioned package consequences

`BundleConsequenceV1` is a closed `RuleV1` effect for the source-derived free-look coupling pattern. It names the permitted trigger action, exact triggering and affected component slots, whether an individual action is allowed, the reinstatement state and whether a new proposal is required. Its scope must be `contract_bundle`; the schema rejects person/policy scope, empty or duplicate slot arrays, unknown actions and extra properties. The existing outer predicate and mandatory-rule closure establish the specific wrapper, new-issue/free-look applicability, receipt clock and known component membership.

Semantic checks resolve every slot against `TermsComponent` in the rule's wrapper edition, require complete authorized package membership and reject unexplained or unrelated target contracts. Public rules contain no private subject IDs; the authorized turn binds the exact owned bundle revision. Unknown selection or membership cannot be treated as an empty set. An effect with multiple affected components cannot be represented as independent component cancellation. Source evidence must support reinstatement and new-proposal assertions separately. Package scope does not create a pooled financial limit or life-policy eligibility.

The [illustrative records](combi-worked-records-r6.json) preserve the two original passages and a synthetic two-component mapping. Schema checks validate representation only. They do not establish actual receipt, insurer acceptance, cancellation, refund or an executable adviser. The effect explains a contractual consequence and does not authorize an external action.

`PolicyEventPartyV1` reuses the closed party-identity structure for cancellation and refund correspondence. Its semantic context is the target contract issuer or exact package-component issuer set. Same-owner person references and delegated-authority evidence remain mandatory. `unknown` preserves missing identity and cannot certify an insurer receipt/decision/payment. These are event observations, not commands to insurers.
