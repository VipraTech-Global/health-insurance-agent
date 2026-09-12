# CoverGuide health insurance adviser

CoverGuide is an evidence-first local pilot for health insurance conversations. The current
implementation establishes the account, profile, conversation, provenance, catalogue, and
streaming boundaries. A hash-pinned Care Supreme policy wording is active for a narrow local test;
other plans and unsupported questions still return an evidence-limited outcome.

## Run locally

Requirements: Python 3.12 through uv, Node.js 24, and Docker.

1. Run `docker compose up -d` to start PostgreSQL, Redis, and Nginx.
2. Run `uv sync --all-groups`.
3. Run `uv run python backend/manage.py migrate`.
4. Acquire the pinned official pilot source with `uv run python backend/manage.py ingest_document
   'https://cms.careinsurance.com/cms/public/uploads/download_center/care-supreme---policy-terms-%26-conditions-%28effective-from-29-april-2026%29.pdf?rv=0.39631700+1788960674'
   --identity 'Care Supreme policy wording (Ditto-hosted)' --allow-host cms.careinsurance.com`.
5. Extract the document ID printed by that command with `uv run python backend/manage.py
   extract_document <document-id>`, then run `uv run python backend/manage.py
   activate_care_supreme_pilot`.
6. Run `uv run --env-file .env uvicorn config.asgi:application --app-dir backend --host 127.0.0.1 --port 8018`.
7. In another terminal, run `uv run celery --workdir backend -A config worker --beat --loglevel=INFO --concurrency=1`.
8. In `frontend`, run `npm ci`, `npm run build`, and `npm start`.
9. Keep the host processes running; Nginx in Compose routes the single local origin.

The site is then available at http://localhost:8088. API documentation is at
http://localhost:8088/api/docs/.

## Implemented boundary

- Session accounts with CSRF-protected register, login, logout, password change, and deletion.
- Owned conversations, immutable profile revisions, profile confirmation, and canonical messages.
- Idempotent logical turns separated from execution attempts.
- POST-based SSE with accepted, progress, result, and error events.
- Cancellation state, explicit retry rules, and stale-profile publication checks.
- Catalogue, document, extraction, source-map, evidence, fact, corpus, answer, and recommendation
  persistence models.
- Live sitemap discovery and coverage reporting for 203 current Ditto plan listings, separated from
  recommendation readiness.
- Content-addressed PDF storage, native word geometry, frozen source maps, exact evidence spans,
  protected range-capable source delivery, and browser highlight rendering.
- Three-state applicability and deterministic suitability/rating/premium tie rules.
- A strict relay boundary with complete-message preservation and no silent retry or model substitution.
- A responsive Next.js interface for accounts, conversations, profile confirmation, and coverage.
- OpenAPI schema generation and generated TypeScript contracts.

## Evidence status

One Care Supreme version is active for local evidence-delivery testing. Its preserved bytes match
Care Health Insurance's official policy download effective 29 April 2026. Four facts are verified:
the pre-existing disease, named ailment, and initial waiting periods, plus optional co-payment terms.
Live discovery found 203 plan-shaped Ditto listings; the other 202 are not active. The active result
does not provide a personalised premium or predict underwriting, and it is not a full-catalogue
recommendation.

For an HTTPS deployment, set `DJANGO_DEBUG=0`, use a high-entropy `DJANGO_SECRET_KEY`, and enable
`DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SECURE_COOKIES`, and a suitable `DJANGO_HSTS_SECONDS` value.

See docs/STATUS.md for milestone status and acceptance evidence.

## AI settings and the shared relay

CLIProxyAPI is activated locally at `http://127.0.0.1:8317`. Open **AI settings** in
CoverGuide to choose a qualified model. `gpt-6-astra` is the initial choice; `gpt-5.6-sol`,
`gpt-5.6-terra`, and `gpt-5.6-luna` are also qualified. Preferences apply to future turns,
and existing turns retain their captured model. No terminal or provider login is needed
for ordinary users.

The pilot administrator sees masked Codex account controls and can qualify newly discovered
models. OAuth opens a new tab and status polling completes or rolls back the switch. The
subscription and account-operation locks are shared with Job-In; account changes affect both
applications. Read-only status requests never complete an OAuth operation. Polling and account
changes use authenticated, CSRF-protected POST requests.

Server credentials belong only in the ignored `.env` (mode `0600`), loaded by the backend
process. Never put them in frontend environment variables, route records, or source control.
The live backend runs with debug error pages disabled. OmniRoute is inactive.

The shared relay explicitly sets `request-retry: 0`, `max-retry-credentials: 1`,
`max-retry-interval: 0`, and all three `quota-exceeded` fallbacks to false, with loopback
listener and management access. These override the defaults in the
[official CLIProxyAPI configuration](https://github.com/router-for-me/CLIProxyAPI/blob/main/config.example.yaml).
The original configuration is backed up beside the shared relay configuration, with mode `0600`.

Live host services are `coverguide-web.service` and `coverguide-frontend.service` in the
user systemd manager (transient units for this login session). Use `systemctl --user restart
coverguide-web.service coverguide-frontend.service` after code/build changes; the existing
Celery process and Compose PostgreSQL, Redis, and Nginx services remain in place.

AI selects relevant verified policy explanations. Publication accepts only the exact approved
fact text, with resolved evidence IDs, and rechecks the profile, corpus, route qualification,
account, cancellation, and deadline. Interview suggestions quote the user's message and need
review before becoming a new profile revision. These safeguards deliberately limit generated
prose. Personalised recommendations remain withheld pending reviewed recommendable plans.

Authenticated endpoints: `GET /api/v1/ai/models/`, `PATCH /api/v1/ai/preferences/`,
`GET /api/v1/admin/ai-relay/`, `POST /api/v1/admin/ai-relay/accounts/` (connect, status,
cancel, disconnect, restore, forget), and `POST /api/v1/admin/ai-relay/qualifications/`.
Each qualification tests both answer and interview schemas and records safe call metadata.
The one-time `promote_pilot_admin` command requires an inspected user ID and exact last-login
timestamp and refuses ambiguous accounts, changed logins, or repeat promotion.
