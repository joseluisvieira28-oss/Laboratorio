# BTC-CONVEX-TREND-CAPTURE-001 — CROSS-ASSET SOURCE AMENDMENT 002

**Date:** 2026-09-23  
**Status:** FROZEN AFTER TECHNICAL FAILURE, BEFORE ANY CROSS-ASSET ECONOMIC OUTCOME  
**Scope:** funding timestamp normalization only

## Trigger

The first adjudicating engine attempt stopped before calculating/reporting cross-asset outcomes because Binance Vision funding archive contained:

`calc_time = 1609459200002`

for the funding event corresponding to 2021-01-01 00:00:00 UTC.

The official 1h market bar timestamp is:
`1609459200000`.

Difference:
**+2 milliseconds**.

No economic result artifact was produced.

## Frozen normalization

For Binance Vision funding `calc_time`:

1. compute the nearest exact UTC hour:
   `round(calc_time / 3,600,000) × 3,600,000`;
2. calculate absolute deviation from the raw timestamp;
3. normalize to that exact hour **only if deviation <= 1,000 ms**;
4. if deviation > 1,000 ms, classify DATA_TIMESTAMP_BLOCKED and STOP.

Duplicate funding events after normalization:
- if rates agree exactly/to numerical precision, deduplicate;
- if rates conflict, FAIL_CLOSED.

The raw timestamp and normalized timestamp must remain auditable in the evidence receipt.

## Unchanged

No scientific/economic rule changes:
- universe unchanged;
- dates unchanged;
- 2026 locked;
- signals unchanged;
- Parent/Sticky unchanged;
- funding rates unchanged;
- funding cashflow formula unchanged;
- fee/slippage unchanged;
- gates unchanged.

This amendment repairs source timestamp alignment only.
