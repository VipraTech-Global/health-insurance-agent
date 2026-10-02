# Historical Star processing and retrieval

This directory preserves the previous extraction/review pipeline, retrieval modes,
embedding wiring and answer engine for regression and research. The mounted demo
uses `apps.adviser_v2.demo` and its frozen H winner. It does not import this package.

Historical management commands live in `research_workspace/management/commands`.
Only `research_workspace.test_settings` installs that command app. The normal
local stack cannot discover these commands. Tests retain their original assertions
and use updated import locations; no historical benchmark is re-scored by this move.

Historical models, evidence, facts and migrations remain in `apps.adviser_v2`.
Authentication and account erasure retain their existing data graph. In particular,
the 39 stored Star facts and the frozen 236-span reference set are protected.

The exact protocol-v2 scored sources are separately preserved, byte for byte, in
`research/ten-insurer/protocol-v2-frozen-runtime`. Do not substitute these relocated
research modules when reproducing that frozen run.
