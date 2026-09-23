# DEFI-LIQUIDATION-SHOCK-001 — KAMINO V1 EVENT CENSUS EXTENSION POLICY V0.1

Date: 2026-09-23
Status: FROZEN BEFORE FIRST-CHUNK OUTCOME / SOURCE-ONLY / OUTCOME-BLIND

After the already frozen first partial-day chunk completes with a source-valid PASS, continuation is deterministic:

- next start: `2023-11-18T00:00:00Z`;
- chunk width: exactly 1 UTC day;
- advance strictly calendar-day by calendar-day;
- no day may be skipped or reordered;
- terminal scientific-window end: `2025-01-01T00:00:00Z` exclusive;
- chunk width MUST NOT be changed because of event counts, event sizes, prices, returns, PnL or apparent profitability;
- a future transport-only expansion to 2-7 days is allowed only under the previously frozen BOUNDED_CENSUS_PLAN V0.1 using source-only runtime/bytes evidence, documented before viewing the affected chunk's event classifications;
- source anomaly, incomplete RAW coverage or unresolved null transaction => fail closed for that chunk;
- failed liquidation attempts remain separate from realized events;
- duplicate signatures or ambiguous multiple exact liquidation instructions block promotion of the affected chunk.

Existing preserved signature artifacts are preferred wherever they cover the requested UTC day. When preserved coverage ends, a new source-only signature acquisition must be frozen before execution.

No market outcomes are authorized by this policy.
