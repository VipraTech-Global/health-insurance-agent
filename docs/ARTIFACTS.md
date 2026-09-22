# Artifact and licence manifest

This manifest records artifacts actually present in the local pilot. Exact package hashes are in
uv.lock and frontend/package-lock.json.

| Artifact | Pinned version or hash | Licence | Use |
|---|---|---|---|
| Python | 3.12 | PSF | Backend runtime |
| Django | 5.2.17 | BSD-3-Clause | Application and persistence |
| Django REST framework | 3.18.1 | BSD-3-Clause | Ordinary APIs |
| drf-spectacular | 0.29.0 | BSD-3-Clause | OpenAPI generation |
| psycopg | 3.2.10 | LGPL-3.0 | PostgreSQL and bounded pooling |
| pdfplumber | 0.11.10 | MIT | Native PDF words and geometry |
| Celery | 5.6.3 | BSD-3-Clause | Background job boundary |
| defusedxml | 0.7.1 | PSF | Defensive remote sitemap parsing |
| Next.js | 16.3.4 | MIT | Browser application |
| React | 19.2.0 | MIT | Browser rendering |
| PDF.js | 5.4.149 | Apache-2.0 | Original document rendering |
| PostgreSQL/pgvector replacement | `0.8.6-pg18-bookworm@sha256:2ba9ca5f2e7daa0f0e7723cba1ee9167bab54efd3640516a44ac1a928dd67e7a` | PostgreSQL licence | Isolated local v2 relational/vector storage |
| PostgreSQL/pgvector legacy pilot | `pg16@sha256:ccc6e83d6e35e931dc7c5def2022729d5a6c370318d099181995567ff1fb4d6b` | PostgreSQL licence | Retained rollback data; not the replacement runtime and not yet deleted |
| Redis container | `7.2-alpine@sha256:ccd6aa8d45ff3f033d6fa15b8cc1a50579f65c89f38cf9bb607a954c4f2128ed` | BSD-3-Clause | Queue and cancellation coordination |
| Nginx container | `1.28-alpine@sha256:a8b39bd9cf0f83869a2162827a0caf6137ddf759d50a171451b335cecc87d236` | BSD-2-Clause | Same-origin proxy and protected file delivery |
| Care Supreme wording | SHA-256 1b1eea97989a76090767482093e663af04f8cadbd122b5f845b0b7144c6083d2 | Source document; insurer terms apply | Active one-plan pilot source; bytes match insurer download effective 29 April 2026 |
| Care source map revision 1 | SHA-256 4413a6594e3ce31022eafbd2ce0df872554ab1f4cfd585dc75ebe27709d08b0b | Application artifact | 83-page pending review fixture |
| Care source map revision 2 | SHA-256 e872793c5d49005b9f02688396b6bc563739c6893da31f6dca39d96fb24b1520 | Application artifact | Published 83-page source map for exact pilot citations |

Docling and the BGE-M3 reference assets are local optional artifacts. No BGE-M3 candidate has passed
the fixed retrieval gate, so none is accepted for the replacement release. CLIProxyAPI qualification
records in `cliproxyapi-activation-2026-09-10.json` belong to the earlier local runtime and are not
imported into the greenfield database. OmniRoute is optional and interactive-role-only; the
2026-09-22 replacement has no live Gemini qualification because its gateway credential/runtime is
absent. Historical probes in `omniroute-spike-2026-09-19.json` do not satisfy that gate.
