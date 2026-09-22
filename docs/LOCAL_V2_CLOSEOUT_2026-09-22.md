# Local CoverGuide v2 closeout evidence

Status date: 2026-09-22
Scope: local implementation and proof only; no production deployment, external cutover, provider
retention claim, or old-runtime deletion.

## Outcome

The approved v2 schema amendment and immutable interactive-route selection are implemented. A
greenfield PostgreSQL 18 and Redis replacement starts with the backend, Celery worker, Celery beat,
frontend, and Nginx. Deterministic verification passes. The service-health rehearsal explicitly
disabled OmniRoute because its required key/runtime is absent; it is not a live Gemini proof.

The local closeout is **blocked**, not complete:

1. `check_omniroute` stops on missing `OMNIROUTE_API_KEY`, and the loopback gateway is not listening.
   `qualify_v2_models --skip-checks` consequently stops with
   `fact_interpretation route is not usable: provider_misconfigured`. Neither Gemini route has a
   fresh live qualification or pilot attempt.
2. A fresh capture of the reviewed five-product manifest stopped at
   `reassure-3-prospectus` because the downloaded bytes no longer match its approved SHA-256. The
   command admitted two complete products and 13 verified public objects, then stopped. It created
   no release.
3. The prior BGE-M3 candidates failed the fixed retrieval thresholds. The replacement did not
   silently accept or reuse one of those failed configurations.
4. With no qualified interactive Gemini route and no ready knowledge release, the controlled 3.5
   pilot, bounded 3.1 comparison, full Playwright advice flows, and replacement-account erasure run
   cannot truthfully pass.

## Implemented boundary

- Each accepted turn stores one `TurnRouteBinding` for `fact_interpretation` and one for
  `recommendation_answer`, plus a keyed `Turn.route_commitment`.
- A binding pins the exact route and qualification, requested/expected/observed identity, endpoint
  profile, adapter version, route configuration hash, and schema hash before enqueue.
- Workers consume the stored bindings. Explicit retries copy them and do not resolve current role
  settings. Disabled, unqualified, identity-mismatched, schema-mismatched, commitment-mismatched, or
  endpoint-configuration-mismatched routes fail closed.
- Every model-attempt request commitment includes the qualification, route key, endpoint profile,
  expected model, route configuration hash, and schema hash. No cross-provider/model fallback exists.
- Policy extraction, review, and processing jobs remain relay-only. V2 route choice is operator-only;
  the customer-facing picker is labelled as legacy v1.
- `ConsentRecord` represents its default `requested` state explicitly. A record is not described as
  granted without a customer action.

## Verification evidence

- 202 v2 backend tests passed.
- 319 complete backend application tests passed.
- 30 research-workspace tests passed.
- Ruff, `git diff --check`, Django system checks, migration drift, and strict mypy over 106 source
  files passed.
- OpenAPI validation and generated TypeScript, frontend lint, typecheck, and production build passed.
- An empty temporary PostgreSQL 18 database applied every migration through
  `adviser_v2.0012_turn_route_bindings`; Django checks passed and it contained zero users,
  conversations, turns, products, and releases. The temporary database was then removed.
- The isolated replacement readiness endpoint returned HTTP 200 with database, storage, ASGI
  runtime, and reconciler healthy. PostgreSQL 18 and Redis health checks passed; Celery worker and
  beat processed their empty-queue maintenance tasks.
- Focused tests prove that a processing job refuses OmniRoute and that account erasure removes the
  private file/index/session boundary represented by the erasure receipt.

## Replacement boundary

The replacement uses:

- Compose project `coverguide-v2-closeout`;
- volume `coverguide-v2-closeout_health_adviser_pg18`;
- volume `coverguide-v2-closeout_health_adviser_redis`, Redis database 8;
- private/public storage root `data/v2-closeout`.

The replacement database has no imported users, sessions, conversations, turns, uploads, model
attempts, or private objects. The failed current-source capture created only public corpus rows and
objects: two products, 13 source captures, and 13 checksum-verified public objects. The replacement
private-object count is zero.

## Deletion boundary and decision

Deletion is deferred because replacement verification has not passed. No deletion manifest is
issued and no old volume or runtime artifact is removed.

Preliminary retained inventory:

| Boundary | Retained target | Observed size/count |
|---|---|---:|
| Legacy PostgreSQL 16 | `health-insurance-agent_health_adviser_pg` | 68,874,004 bytes |
| Earlier PostgreSQL 18 work | `health-insurance-agent_health_adviser_pg18` | 147,984,001 bytes |
| Legacy Redis | `health-insurance-agent_health_adviser_redis` | 50,834,849 bytes |
| Legacy v2 private tree | `data/v2/private` | 1,060 files / 211,024,791 bytes |
| Preserved public source corpus | `data/v2/public` | 37 files / 40,402,527 bytes |
| Replacement private tree | `data/v2-closeout/private` | 0 files |

The eventual deletion manifest must exclude `research/`, the approved design documents, the public
source corpus, audit history required for the retained design/research evidence, and both replacement
volumes. It must not be created or executed until both Gemini routes, a ready release, controlled
pilot/comparison, private-processing proof, erasure, backup/restore, and post-deletion smoke tests
all pass.

## Deferred production gates

Provider retention/compliance verification, production consent policy, the independent
200-case/600-attempt benchmark, robustness cohort, production deployment, and production cutover
remain outside this local proof.
