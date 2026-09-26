# BTC-CONVEX-TREND-CAPTURE-001 — CROSS-ASSET SOURCE AMENDMENT 004

**Date:** 2026-09-23  
**Status:** FROZEN BEFORE ANY CROSS-ASSET ECONOMIC OUTCOME IS OPENED  
**Scope:** historical funding mark-price completion only

## Trigger

Source Gate V0.1B proved that:
- all required market-price monthly files exist;
- the accessible official funding-history transport works;
- some older funding-history records contain an empty `markPrice`.

No cross-asset economic outcome has been opened.

## Authorized mark-price hierarchy

For each official funding event:

1. use the funding-history record's `markPrice` when present and valid;
2. if and only if that field is empty, use the official Binance USD-M **1h markPriceKline OPEN** whose open timestamp equals the funding timestamp;
3. if no exact timestamp match exists, DATA_BLOCKED.

No ordinary market-price candle is permitted as funding mark fallback.

## Official fallback archive

Binance public historical USD-M mark-price klines:

`https://data.binance.vision/data/futures/um/monthly/markPriceKlines/{SYMBOL}/1h/{SYMBOL}-1h-YYYY-MM.zip`

## Unchanged

No change to:
- fundingRate;
- fundingTime;
- funding cashflow formula;
- assets;
- dates;
- 2026 lock;
- entry/exit rules;
- Parent/Sticky semantics;
- commission;
- slippage;
- scientific gates.

## Provenance requirements

Evidence receipt must record:
- count of funding events;
- count using direct funding-record markPrice;
- count using markPriceKline fallback;
- hashes of all downloaded market/funding/mark-price source pages/files;
- zero unresolved funding marks.

Any unresolved mark => FAIL_CLOSED.
