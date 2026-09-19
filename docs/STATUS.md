# Implementation and qualification status

Status date: 2026-09-10

| Area | Status | Evidence or remaining work |
|---|---|---|
| Application boundary | Implemented | Django/DRF models and APIs, session auth, CSRF, Redis-backed rate limits, owned resources, native async SSE, conversation-level active-attempt ownership, and expiry reconciliation |
| Frontend shell | Implemented | Next.js account, conversation, profile, and corpus coverage screens |
| API contract | Implemented | OpenAPI schema generation and TypeScript generation are part of verification |
| Exact citation storage | Partial | One 83-page native source map, four verified fact bundles, and browser overlays work; OCR and mixed-page fixtures remain |
| Recommendation rules | Partial | One Care Supreme test option returns four cited facts and an honest needs-evidence candidate outcome; full profile suitability and multi-plan ranking remain |
| CLIProxyAPI | Implemented and live verified | Four independently qualified models; strict Responses transport, exact identity, per-user preferences, captured turn routes, masked admin OAuth controls, and audited calls. OmniRoute is an optional, off-by-default second provider for the two interactive v2 roles only (operator-selected, qualified per route, no fallback); live turns on it are not yet verified |
| Retrieval benchmarks | Not measured | The reviewed question corpus and retrieval evaluation remain outstanding |
| Full catalogue inventory | Implemented | Live sitemap discovery recorded 203 listings on 2026-09-09; Care Supreme is active for evidence testing but remains awaiting recommendation review, and 202 remain discovered |
| Quality targets | Not measured | The 1,000-question and 200-profile independently reviewed evaluation sets do not exist |
| Latency targets | Partial | Real proxied SSE behavior is verified; five-session browser p95 qualification is not measured |
| Voice | Reserved | Contracts allow a later adapter; no voice dependencies or services are installed |

The current report is catalogue-coverage-2026-09-09.json: 203 listings, one preserved document,
two immutable extraction revisions, four verified facts, one active local-test plan, and zero plans
currently qualified as recommendable.

Current verification passes: 81 PostgreSQL-backed backend tests, Ruff, strict mypy over 46 production
modules, Django system checks, migration drift, validated OpenAPI generation, generated TypeScript
compilation, frontend lint/build, and 3 proxied Playwright flows. These cover model selection and
persistence, ordinary-user/admin controls, an actual AI policy answer with a rendered source,
interview suggestions applied through profile review, and the existing recommendation/coverage flow.
Live AI calls reported the exact selected gpt-6-astra identity: 7.854 seconds for the policy answer
and 4.301 seconds for interview extraction. These are individual call durations, not p95 measurements.

The pilot remains an application-boundary and one-plan provenance prototype until full fact review,
recommendation evaluation and browser latency targets have passed.

Activation evidence is in [cliproxyapi-activation-2026-09-10.json](cliproxyapi-activation-2026-09-10.json).
All four initial models passed both answer and interview qualifications. The original shared Codex
account and all nine raw relay catalogue entries survived the strict-configuration restart. Job-In
returned its seven eligible catalogue models and passed its own gpt-6-astra readiness probe.

The one-time promotion followed the plan's uniquely most recent login rule and initially selected
an existing test account. Its staff access has now been revoked. The human-designated account is
registered and has pilot staff access, with its existing password and sessions preserved. Its admin
relay endpoint returned HTTP 200 and its selected model is `gpt-6-astra`. Ordinary users have access
to all four qualified model choices. No subscription switch was performed during activation.
