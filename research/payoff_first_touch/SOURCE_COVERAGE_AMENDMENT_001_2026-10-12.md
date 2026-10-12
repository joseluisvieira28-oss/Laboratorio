# SOURCE COVERAGE AMENDMENT 001 — PAYOFF-FIRST-TOUCH-RETRO-001
Date: 2026-10-12. Pre-price-outcome source gate; zero promotion credit.

**Observed source availability, not trading outcomes:** Workflow [38268804917](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38268804917) made HEAD-only availability probes to the frozen official BTCUSDT USD-M 1h archive. It returned **HTTP 404** for 2019-10 ZIP and checksum, and HTTP 200 for the 2020-01, 2021-01, 2024-01 and 2025-01 ZIP/checksum pairs. No historical price bars were parsed: the initial reader stopped at 2019-10. Initial seed corpus contains 95 closed trade episodes dated before 2026 and one 2026 open exclusion + five 2026 closed exclusions. Ledger header from run establishes explicit `entry` and `exit` price columns.

**Predeclared purely availability-based amendment:** classify any episode whose `entry_dt < 2020-01-01T00:00:00Z` as **SOURCE_BLOCKED_2019** and omit it from first-touch processing. Continue with the complete, predeclared 2020-01-01 through 2025-12-31 original seed subset on exactly the same frozen bar/price/cost/touch rules from RETRO_FIRST_TOUCH_FROZEN_PROTOCOL_V0.1.md. Report excluded trade count and all 2020-2025 results. If any other month/source checksum unavailable, fail closed for the subset; no adaptive removal based on outcome.

**Pure metadata technical correction:** use the ledger's existing `entry` field as exact entry price; never invent from post-entry OHLC. Code may make only these coverage/field corrections before opening archive prices. The MEXC fee still only an illustrative cost proxy; whole exercise remains retrospective and cannot establish forward net 4:1 economic edge. No leverage/target/stop parameter changes, no selection based on MFE/outcomes.

2026 remains out of scope. This amendment does not change or reinterpret original BTC-CONVEX freezes, P00 or Donchian OOS.
