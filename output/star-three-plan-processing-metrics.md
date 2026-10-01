# Star criterion processing measurements

Checkpoint 2 processing is still in progress. These measurements do not establish
that a criterion is independently supported or that the release can be published.

## Same-plan, same-criterion observation

Comprehensive, sum insured:

| Measurement | Retained initial response | Remaining corrective response |
| --- | ---: | ---: |
| Wall time | 283.187 s | 69.495 s |
| Input tokens | 72,597 | 75,666 |
| Cached input tokens | Not recorded | 0 |
| Output tokens | 5,826 | 3,276 |
| Reasoning tokens | Not recorded | 128 |
| Extraction effort | Provider default | Explicit low |
| Output ceiling | Unspecified | 8,192 tokens |
| Attempt | `ea1f4056-161a-4654-a12f-ea8c7f765536` | `4c08e4bb-84cc-45b6-9c7d-80f64dea17c0` |

The remaining call was about 4.1 times faster. It corrected a failed validation;
the earlier timeout did not consume its corrective retry. This is an operational
before/after observation, not a controlled benchmark: the correction prompt,
output, effort, request order and concurrency differ. A zero cache hit means this
particular improvement cannot be attributed to a cached bundle prefix.

The next corrective call, Comprehensive newborn, did reuse the shared prefix:
72,064 of 81,461 input tokens were cached (88.5%). It completed in 137.165 s,
compared with 621.143 s for its retained initial response. Its output was 7,399
tokens, including 372 reasoning tokens, within the 8,192-token ceiling. The same
before/after limitations apply; independent validation is still pending.

The remaining plans run sequentially. Existing successful responses are retained;
no finished plan was restarted. Earlier calls ran with up to three concurrent plans.
The old successful-call medians were 339.6 s for Comprehensive, 226.6 s for Optima,
and 296.0 s for Assure; different criteria make these descriptive only.

## Complete evidence accounting

| Plan | Core physical pages | Pages with prospectus | Core serialized evidence bytes | With prospectus bytes |
| --- | ---: | ---: | ---: | ---: |
| Comprehensive | 72 | 125 | 228,349 | 402,782 |
| Family Health Optima | 65 | 124 | 203,297 | 388,116 |
| Health Assure | 69 | 125 | 215,994 | 394,578 |

These byte counts cover document identities, page text and citation metadata.
Request sizes also include the executable-rule contracts and instructions. The
earlier approximately 280 KB Comprehensive requests did **not** include its
prospectus. Prospectus use and its specific missing-core-evidence reason are
recorded per criterion in the final validation artifact and Checkpoint 2 report.

## Verification and audit

- Backend: 357 tests passed, 18 existing missing-static-directory warnings.
- Ruff, Django checks and migration check passed.
- Focused request-order, retry, usage and compatibility checks: 75 passed.
- Existing frontend verification remains applicable; this change modifies no API
  response schema or frontend code.
- Retry change: `d50d7c9`; prompt order, generation options and metrics: `d9e0827`.
- Retained call audit: `~/.local/state/coverguide-star-slice/reports/retained-call-audit.json`.
- Per-call metrics: `~/.local/state/coverguide-star-slice/reports/*-v2-resumed.log`.

The output ceiling includes reasoning tokens, consistent with the
[Responses documentation](https://developers.openai.com/api/docs/guides/reasoning).
Incomplete output remains a failed response. Missing provider usage fields remain
unavailable rather than being reported as zero.
