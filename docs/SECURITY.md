# Security notes

- Browser authentication uses Django sessions; no bearer token is placed in browser storage.
- CSRF middleware protects login and every mutation.
- Login and registration counters use the shared Redis cache and the proxy connection address.
- Personal resources are filtered by the authenticated owner.
- Source files resolve beneath the configured data root and use private/no-store responses.
- Source acquisition validates each HTTPS redirect before requesting it and rejects private address
  resolutions. A deployed crawler should also enforce the allowlist at the network egress layer to
  protect against DNS rebinding.
- Preserved source bytes are checked against their recorded SHA-256 before extraction and delivery.
- The SSE proxy route disables buffering and shared caching.
- Routine application responses do not expose relay credentials or raw provider payloads.
- Production requires HTTPS, a new secret key, secure cookies, explicit hosts, and external review
  of retention and medical-data handling.

## OmniRoute (optional third-party gateway)

- Off by default. It runs only when `OMNIROUTE_ENABLED=1`, the URL is a literal loopback HTTP
  address, an API key is set, the operator confirms gateway logging and compression are off, and
  at least one model is allowlisted. Startup checks and calls refuse otherwise.
- Loopback is not data residency. Customer text for the two interactive roles is forwarded by the
  gateway to upstream free-tier providers whose terms may permit retention or training. Customers
  are not prompted; this is a documented operator decision.
- Policy extraction, policy review and every processing job (which can carry private uploads) are
  relay-only; the gateway layer rejects OmniRoute for them.
- No fallback: an OmniRoute failure fails the turn instead of switching to the relay, and each call
  is a single attempt with no retry.
- The exact route is qualified before use and every call records its qualification and the raw
  reported model. Reported model identity must equal the declared value exactly.
- Provider API keys live only in the OmniRoute store. CoverGuide holds a single gateway key in
  `.env` and never writes it to route records, hashes, logs or responses. HTTP clients ignore proxy
  environment variables and do not follow redirects.
- OAuth and coding-tool connections must never be added as OmniRoute providers.
