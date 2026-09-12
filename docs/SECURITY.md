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
