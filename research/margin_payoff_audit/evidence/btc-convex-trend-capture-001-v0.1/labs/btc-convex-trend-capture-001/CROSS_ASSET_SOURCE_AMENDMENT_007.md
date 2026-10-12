# BTC-CONVEX-TREND-CAPTURE-001 — CROSS-ASSET SOURCE AMENDMENT 007

**Date:** 2026-09-23  
**Status:** FROZEN BEFORE ANY CROSS-ASSET ECONOMIC OUTCOME IS OPENED  
**Scope:** exact-hour daily markPriceKline completion when the monthly archive omits an hour  
**Authority:** additive; preserves Amendments 004–006 where non-conflicting

## Trigger

Source Gate V0.1E failed closed because some official funding-history records had an empty `markPrice`, while the official monthly 1h markPriceKline archive also omitted the exact normalized funding hour.

No cross-asset economic outcome has been opened.

A source-only probe was run:

- workflow run: **35917842139**
- artifact: **10776166265**
- artifact SHA-256: **8dc6694f8dc4d82ab1c754dff971add681a108b73b1a4c4ecf1e3db14f4bcc31**
- probe: `FUNDING_MARK_GAP_PROBE_V0.1`
- role: SOURCE_ONLY_NO_ECONOMIC_OUTCOMES

## Proven exact gaps

### ETHUSDT
Funding timestamp:
- 2022-10-02 00:00:00 UTC
- fundingRate = 0.00001239
- funding record markPrice = empty

Monthly 1h markPriceKline:
- exact hour absent.

Official daily 1h markPriceKline:
- exact hour present;
- OPEN = **1311.31**.

### SOLUSDT
Funding timestamp:
- 2021-07-01 00:00:00 UTC
- fundingRate = 0.00008824
- funding record markPrice = empty

Monthly 1h markPriceKline:
- exact hour absent.

Official daily 1h markPriceKline:
- exact hour present;
- OPEN = **35.493**.

### BNBUSDT
Funding timestamp:
- 2021-07-01 00:00:00 UTC
- fundingRate = -0.00025920
- funding record markPrice = empty

Monthly 1h markPriceKline:
- exact hour absent.

Official daily 1h markPriceKline:
- exact hour present;
- OPEN = **303.44**.

The source-only probe resolved all three exact gaps.

## Frozen mark-price hierarchy

For every official funding event:

1. use the funding-history record's `markPrice` when present and valid;
2. if empty, use the official Binance USD-M **monthly 1h markPriceKline OPEN** at the normalized funding timestamp when present;
3. if the monthly archive lacks that exact hour, fetch the official Binance USD-M **daily 1h markPriceKline** for the UTC date and use the OPEN at the **same exact normalized timestamp**;
4. if the daily file is unavailable, the exact hour is absent, or monthly/daily values conflict where both exist:
   **DATA_BLOCKED / FAIL_CLOSED**.

No interpolation.
No nearest-neighbor substitution.
No ordinary market-price fallback.
No spot-price fallback.

## Daily archive path

`https://data.binance.vision/data/futures/um/daily/markPriceKlines/{SYMBOL}/1h/{SYMBOL}-1h-YYYY-MM-DD.zip`

## Provenance requirements

Evidence must record for every daily fallback:
- symbol;
- normalized funding timestamp;
- UTC date;
- source URL;
- archive SHA-256;
- exact-hour OPEN used.

Evidence must also report:
- direct funding-record mark count;
- monthly markPriceKline fallback count;
- daily markPriceKline fallback count;
- unresolved mark count = 0.

## Unchanged science

No change to:
- ETH/SOL/BNB universe;
- 1h timeframe;
- 2021-01-01 through 2025-12-31;
- 2026 lock;
- Parent V5 entry/exit parameters;
- Sticky H1;
- causal execution;
- 95% sizing;
- 10 bps commission per side;
- REPRO/BASE/STRESS slippage;
- fundingRate;
- funding cashflow formula;
- scientific gates;
- no-rescue rules.

This amendment is a source-completeness repair only.
