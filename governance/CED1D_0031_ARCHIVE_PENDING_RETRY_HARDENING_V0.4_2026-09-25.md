# CED1D-0031 — ARCHIVE PENDING RETRY HARDENING V0.4 — 2026-09-25

**Status:** FROZEN TECHNICAL REMEDIATION / NO SCIENCE CHANGE  
**Parent authority:** CED1D_0031_RENDER_SHADOW_ACTIVATION_V0.3  
**Runtime:** crypto-edge-radar-v05-canary / Render Frankfurt

## Observed blocker

At the first mature CED1D signal-day boundary on 2026-09-25 UTC, the canonical collector attempted the frozen path for through-signal-day 2026-09-22.

The path requires:
- signal day 2026-09-22;
- reference entry day 2026-09-23;
- reference exit/path day 2026-09-24.

Binance Vision returned HTTP 404 for the exact frozen public archive:
`AVAXUSDT-1m-2026-09-24.zip`.

The parent source-readiness guard remained satisfied:
`through_signal_day <= current_UTC_date - 3 days`.

The 404 is therefore treated as publication/availability state of the **latest required path archive**, not as evidence against the strategy.

## Runtime defect

The canonical web runtime previously marked the UTC date as checked after any CED1D exception. A transient archive-publication 404 could therefore prevent another CED1D attempt until the next UTC day even if the exact frozen archive became available minutes later.

## Frozen remediation

1. No source substitution.
2. Binance Vision remains the exact archive authority for these path files.
3. Only an HTTP 404 whose archive date equals the exact latest required path day
   `through_signal_day + HORIZON + 1`
   may be classified as `WAITING_SOURCE_ARCHIVE`.
4. A 404 for warmup/history or any earlier required archive remains fail-closed.
5. `WAITING_SOURCE_ARCHIVE` creates no trade row, performance row, success receipt or scientific failure evidence.
6. The runtime retries `WAITING_SOURCE_ARCHIVE` at most once every 15 minutes during the same UTC day.
7. Unexpected failures remain fail-closed and are not retried aggressively.
8. A new UTC day remains independently eligible for the normal mature-day check.
9. No missed/path event is reconstructed outside the already-frozen collector semantics.

## Scientific invariants unchanged

- candidate: CED1D-0031 / AVAXUSDT;
- family: A_MOMENTUM;
- lookback: 20 valid prior daily observations;
- direction: CONTINUATION;
- horizon: 1 day;
- first eligible signal day: 2026-09-22;
- source-readiness guard: 3 days;
- research notional: 100 USDT;
- reference costs: BASE14 / STRESS20 bps;
- execution fees: BASE8 / STRESS10 bps;
- aggTrades window: 5000 ms;
- bookDepth: +/-1%, max age 60000 ms;
- Tier-1 gate: >=60 resolved events, >=8 complete UTC signal weeks, >=50 complete execution pairs;
- no retrospective 2026 backfill;
- no parameter changes.

## Safety

- public/read-only data only;
- no authenticated trading endpoint;
- no order;
- no exchange mutation;
- no wallet;
- no leverage;
- no production capital;
- no automatic promotion;
- no main merge.

This hardening changes only operational retry semantics for a not-yet-published exact frozen archive.
