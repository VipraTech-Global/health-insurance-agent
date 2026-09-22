# Implementation and qualification status

Status date: 2026-09-22

| Area | Current local status | Evidence or remaining gate |
|---|---|---|
| Approved v2 data design | Implemented | 63 entities, 601 fields, 170 relationships, and 31 state machines; `discussion-r25-final-review` and the route-pinning amendment are recorded as approved |
| Immutable turn routes | Implemented and test verified | Both interactive routes bind before enqueue; retries copy the binding; route/qualification/identity/schema/configuration/commitment mismatches fail closed |
| Consent lifecycle | Implemented and test verified | `requested` is an explicit default choice; grant still requires a customer action |
| PostgreSQL 18 replacement | Locally healthy | Fresh isolated volume, empty-database migration through `0012`, no historical customer/runtime import |
| Redis and application stack | Locally healthy | Isolated Redis volume/database; backend, Celery worker, beat, frontend, and Nginx passed health checks |
| OmniRoute integration | Implemented, live proof blocked | Exact 3.5/3.1 allowlist, local/debug acknowledgement, strict identity, no fallback, and relay-only processing are enforced; gateway key/runtime is absent, so neither Gemini route is freshly qualified |
| Three-product development release | Blocked | Fresh reviewed capture admitted only two complete products before source-hash drift stopped it; no release exists in the replacement database |
| Five-product release | Blocked | ReAssure 3.0 prospectus hash drift, incomplete processing/review, and no accepted embedding qualification |
| Private processing and erasure | Deterministic tests pass; live replacement flow deferred | Processing refuses OmniRoute and erasure tests pass; a controlled replacement pilot cannot run before route and release gates |
| Old pilot deletion | Not performed | Replacement proof is incomplete; old PostgreSQL/Redis volumes and legacy private tree remain intact |
| Production readiness | Not claimed | Provider retention/compliance, production consent, independent benchmark/robustness, deployment, and cutover remain deferred |

Current verification passes: 319 backend application tests, 30 research tests, Ruff, strict mypy
over 106 source files, Django checks, migration drift, validated OpenAPI generation, generated
TypeScript, frontend lint/typecheck/build, an empty PostgreSQL 18 migration rehearsal, and local
service health checks.

Live verification does **not** pass yet. `check_omniroute` reports the missing gateway key and the
loopback gateway is not listening. The reviewed source recapture stops on an exact SHA-256 mismatch.
Those failures prevent honest Gemini 3.5/3.1 pilot claims, a ready release, the full advice
Playwright flows, and old-runtime deletion.

See [LOCAL_V2_CLOSEOUT_2026-09-22.md](LOCAL_V2_CLOSEOUT_2026-09-22.md) for the exact local boundary,
blockers, retained-runtime inventory, and deletion decision. Earlier activation files in `docs/`
remain historical evidence for the prior pilot; they are not proof for this greenfield replacement.
