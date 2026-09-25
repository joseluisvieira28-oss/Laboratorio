# CMM-002 — SOURCE TRANSPORT REMEDIATION V0.1B

Status: FROZEN BEFORE ANY CMM-002 2025 BTC OUTCOME ACCESS

V0.1A failed closed because the Internet Archive CDX endpoint returned HTTP 503 from the GitHub runner.

This is classified TRANSPORT_BLOCKED, not a semantic source failure.

V0.1B changes ONLY snapshot discovery transport:
- replace CDX lookup with Internet Archive's archive.org/wayback/available availability endpoint;
- request the same exact DefiLlama endpoint and timestamp target 2025-12-31 23:59:59;
- require returned snapshot timestamp < 2026-01-01;
- replay the exact snapshot through Wayback raw id_ mode;
- preserve every V0.1A schema, no-2026, coverage and semantic-continuity gate unchanged.

No BTC outcome, PnL, event result or 2026 source is authorized during this remediation.
If availability lookup or replay fails, remain SOURCE_BLOCKED. No scientific parameter may change.
