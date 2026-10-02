# Ten-insurer demo decisions

## 2026-10-02 — scope and protocol, before scored calls

- Work starts at `b1a5a22` on `feat/ten-insurer-chat-demo`, in the existing pilot worktree. Only `coverguide_star_slice`, its test database and Redis on port 6401 are allowed. API/frontend remain 8021/3021. No push or off-machine publication.
- The supplied final plan supersedes the older brief where they conflict: rejected wrong-plan quotation attempts disqualify; both disqualified means no admissible winner and live answers disabled; a Star cell requires complete reference coverage in **both** queries; no customer profile in search queries; preserve old dependencies until their replacements work.
- The user's section 15 addition supersedes the single-model rule. Luna is primary; only an explicit subscription usage/weekly-limit error permits Sonnet on the same `/v1/responses` relay. Ordinary transport errors never switch models. Redis coordinates the model state, probes and six-call cap across processes. Sonnet receives a message list and schema instructions; local schema validation is mandatory for both models.
- The full brief was found at `../health-insurance-agent/output/codex-brief-final-plan.md`. Its ten fallback sample names and twenty answer-sheet topics are available. Comparable official retail-health figures must establish any ranking; otherwise label these insurers a demo sample.
- Preserve the 39 historical facts and the original stored reference memberships. Old Sol maps are incompatible with the new cache configuration. New map caches record every contributing model, PDF/raw hashes, settings and processing version.
- H versus P only. Score = complete Star cells + answered/260*39. Wrong-plan attempts disqualify. P wins eligible ties within two points. No post-result tuning. Thirteen slots remain weighted separately even if physical documents overlap. Missing cases stay in the denominator. See `docs/ten-insurer-bakeoff-protocol.md`.
- Existing local pilot stays intact during replacement. No destructive schema cleanup until source data, authentication and erasure dependencies are preserved and verified.

## Implementation status

Work in progress. No new bake-off has run and no ten-insurer release has been published.
