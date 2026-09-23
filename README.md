# CoverGuide health insurance adviser

CoverGuide is an evidence-grounded, local-only health-insurance policy comparison pilot. It
compares every reviewed product against customer-supplied criteria, exposes per-criterion outcomes,
evidence gaps, restrictions, and citations, and never ranks products or chooses a policy.

The customer-facing contract is fixed: “CoverGuide compares the reviewed products against the
criteria you shared. It does not choose a policy; the decision is yours.” There is no selected-product
field, purchase action, or stored user decision.

This repository is approved only for a single operator's synthetic/local pilot. It is not approved
for public or multi-user health-data use because per-user consent to third-party AI processing has
not been implemented.

## Run locally

Requirements: Python 3.12 through uv, Node.js 24, Docker, and the loopback OmniRoute service when
either interactive role is routed to Gemini.

1. Copy `.env.example` to `.env`, set mode `0600`, replace every placeholder, and generate fresh
   Django, encryption, and commitment keys. `.env` is ignored; never commit it.
2. Start infrastructure with
   `docker compose -p coverguide-v2-closeout up -d postgres18 redis nginx`.
3. Run `uv sync --all-groups` and `uv run --env-file .env python backend/manage.py migrate`.
4. Build the frontend with `npm --prefix frontend ci` and `npm --prefix frontend run build`.
5. Start the backend on `127.0.0.1:8018`, the frontend on `127.0.0.1:3018`, and separate Celery
   worker and beat processes. Nginx serves the single origin at <http://127.0.0.1:8088>.

For the persistent local runtime, link and enable the checked-in hardened user units:

```console
systemctl --user link "$PWD"/ops/systemd/coverguide-*.service
systemctl --user daemon-reload
systemctl --user enable --now \
  coverguide-infra.service coverguide-web.service \
  coverguide-celery-worker.service coverguide-celery-beat.service \
  coverguide-frontend.service
```

The units use journald, restart-on-failure, `UMask=0077`, `NoNewPrivileges`, read-only project/home
access, and narrow writable paths for application data, the beat schedule, and Next.js cache. The
account must have lingering enabled. Reboot validation is a separate operator checkpoint.

## Active API and comparison contract

Only `/api/v1/auth/*` remains active under v1. Adviser conversations, turns, streaming, catalogue,
evidence, documents, and comparisons are under `/api/v2/*`; the comparison resource is
`GET /api/v2/comparisons/{id}/`. The prior v1 adviser routes and v2 recommendation endpoint are
retired rather than aliased.

The active contract uses `Comparison`, `PolicyComparisonAssessment`, `comparison_id`, SSE event
`comparison.completed`, event kind `comparison`, and model role `comparison_answer`. Every reviewed
product remains visible in stable insurer/product/UIN/variant order. Cards have equal visual weight
and show criterion outcomes (`meets`, `partly_meets`, `does_not_meet`, `unknown`, or
`not_applicable`), evidence, gaps, and applicable decision-critical restrictions.

Generated comparison prose is limited to cited factual statements. The application owns the
outcome, introduction, missing-information question, and closing notice. Generated endorsement,
ranking, shortlisting, winner, selection, or purchase-direction language fails the turn closed.
Existing hard validation also rejects unsupported facts and numbers, wrong-person or wrong-product
references, policy-version mismatches, invalid calculations, and cross-product citations.

## Evidence and privacy boundary

Policy versions, source bytes, extraction revisions, source maps, evidence spans, rules, and release
membership are hash-bound. Product IDs, criteria, evidence, restrictions, and citations are retained
through the comparison migration; overall scores, ranks, dispositions, and candidate filtering are
not part of the active model.

Loopback is not data residency. If an interactive role is routed through OmniRoute, its synthetic or
customer context is sent to the selected Gemini account under Google's applicable terms. The local
operator acknowledgment is not a substitute for per-user consent. Policy extraction and review may
process private uploads, so they remain on the existing relay and cannot use OmniRoute.

## OmniRoute gateway

OmniRoute must bind only to `127.0.0.1:20128`. The CoverGuide server key must remain private,
non-expiring, `noLog=true`, compression disabled, combination access empty, automatic model
resolution disabled, and restricted to exactly:

- `gemini/gemini-3.5-flash-lite`
- `gemini/gemini-3.1-flash-lite`

It is pinned to the five approved Gemini connections. `providerStrategies.gemini` uses
`fallbackStrategy="round-robin"` and `stickyRoundRobinLimit=1`; cross-provider and cross-model
fallback are not enabled. Provider credentials stay in OmniRoute. The CoverGuide gateway key stays
only in the ignored server `.env`.

The reproducible policy helper is:

```console
uv run python scripts/configure_coverguide_omniroute.py
```

It authenticates through the supported dashboard API and never prints the dashboard password or
session cookie. After initial setup, remove `INITIAL_PASSWORD` from OmniRoute's runtime environment;
to reconfigure later, supply the current password through the protected
`OMNIROUTE_DASHBOARD_PASSWORD` process environment.

Configure the application with `OMNIROUTE_ENABLED=1`, the loopback base URL, the server-only API
key, `OMNIROUTE_LOGGING_DISABLED_CONFIRMED=1`, the local-pilot acknowledgment, and exact
requested-to-reported model mappings. The two optional route overrides are
`COVERGUIDE_CUSTOMER_INTERPRETATION_ROUTE` and `COVERGUIDE_COMPARISON_ROUTE`; an empty value keeps
that role on its relay model.

Before activation, run:

```console
uv run --env-file .env python backend/manage.py check_omniroute
uv run --env-file .env python backend/manage.py qualify_v2_models
uv run --env-file .env python scripts/verify_coverguide_omniroute.py
```

The qualification suite makes 40 normal interactive calls: 12 interpretation and 8 comparison
cases against each Gemini model. It checks exact reported identity, current suite/corpus/prompt/
validator/protocol/schema hashes, 100% assertions, neutrality, a 75-second p95, and a 120-second
hard call timeout. Only no-output transport or quota failures receive one retry; semantic and schema
failures do not. Each role selects independently by assertion score, then lower p95 latency, with
Gemini 3.5 winning only an exact tie. A newer failure invalidates an older pass. If neither model
passes a role, leave that role on the relay and do not run a real-data OmniRoute pilot.

The gateway acceptance helper requires ten consecutive successful synthetic calls, exactly two per
Gemini connection, and verifies that the no-log key retained only administrative metadata—not
request/response bodies, detail rows, or request artifacts.

## Verification

Run the repository checks before review:

```console
uv run ruff check backend scripts
uv run --env-file .env pytest
uv run --env-file .env python backend/manage.py check
uv run --env-file .env python backend/manage.py makemigrations --check --dry-run
npm --prefix frontend run generate:api
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

Regenerate `openapi.json` before the TypeScript contract whenever the API changes. Browser smoke
tests must use synthetic data. No push, merge, production deployment, real-health-data pilot, or
reboot is implied by local acceptance.

## Local-only inputs

These are deliberately not in the repository and must be supplied locally:

- `research/seeds/scenarios.txt`: the private combined scenario set read by the research tooling.
- `research/objects/`, `research/evaluation/`, and `data/source-blobs/`: original insurer documents
  and private benchmark material.
- `data/v2/`, `data/reports/`, and `data/manifests/`: encrypted runtime storage and generated run
  artifacts (only `data/reports/corpus-coverage.json` is tracked).

## Contributing

Work on a branch and open a pull request against `main`. Report security issues privately to the
maintainers; see [docs/SECURITY.md](docs/SECURITY.md) for the current security posture.

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE). Insurer policy documents
referenced by the research registers remain the property of their respective insurers and are not
redistributed here.
