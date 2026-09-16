# USD-NET-LIQUIDITY-001 — Source Gate V0.1

Research-only / outcome-blind / fail-closed.

This branch implements only the prospectively frozen source gate for `UNL-FED-TGA-RRP-W1-001` before any BTC market outcome is opened.

Frozen macro inputs:
- `WALCL` — weekly H.4.1 total assets, millions USD, Wednesday.
- `WDTGAL` — weekly H.4.1 Treasury General Account, millions USD, Wednesday.
- `RRPONTSYD` — NY Fed overnight reverse repo, billions USD, daily; exact Wednesday only.

Frozen source window: `2017-12-27` through `2024-12-18`, inclusive.

The gate must:
1. request each FRED series with explicit start/end cutoff;
2. preserve exact response bytes and SHA-256;
3. hard-fail if any parsed observation is after 2024-12-18;
4. require exact Wednesday WALCL/WDTGAL joins and exact same-date non-missing RRP;
5. convert RRP billions to millions only for source alignment;
6. compute only net-liquidity source values and one-week source deltas, never BTC prices/returns/PnL;
7. classify `SOURCE_DATA_PASS` only if at least 350 exact aligned Wednesdays and at least 349 finite one-week deltas exist.

No BTC price values, signal returns, PnL, PF, expectancy, bootstrap, 2025 or 2026 data may be opened by this gate.

Drive authority: `USD-NET-LIQUIDITY-001 — PRE-DISCOVERY AUTHORITY V0.1 — 2026-09-16`, ID `1N4fatMYlLh0-R7YWf4DKfPogAR8tqSQdMzDIQbUaRgM`.
