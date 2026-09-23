# BTC-CONVEX-TREND-CAPTURE-001 — CROSS-ASSET SOURCE AMENDMENT 005

**Date:** 2026-09-23  
**Status:** FROZEN BEFORE ANY CROSS-ASSET ECONOMIC OUTCOME IS OPENED  
**Scope:** SOLUSDT official daily market-kline gap completion only  
**Authority:** additive; preserves Amendments 001–004

## Trigger

Internal timestamp coverage audit found that the official Binance Vision SOLUSDT 1h **monthly** market-kline archives are missing exactly 120 hourly timestamps inside the frozen 2021–2025 evaluation interval:

- 2022-02-26 00:00 through 2022-02-28 23:00 UTC — 72 hours;
- 2022-04-01 00:00 through 2022-04-02 23:00 UTC — 48 hours.

A source-only probe opened no economic outcomes and confirmed that the corresponding five official Binance Vision **daily** 1h files all return HTTP 200.

## Authorized repair

Primary market source remains the official monthly Binance Vision USD-M 1h kline archive.

For SOLUSDT only, the following official daily files are authorized solely to fill timestamps absent from the monthly archive:

- SOLUSDT-1h-2022-02-26.zip
- SOLUSDT-1h-2022-02-27.zip
- SOLUSDT-1h-2022-02-28.zip
- SOLUSDT-1h-2022-04-01.zip
- SOLUSDT-1h-2022-04-02.zip

Path:
`https://data.binance.vision/data/futures/um/daily/klines/SOLUSDT/1h/`

## Hard rules

1. Daily data may add **only** timestamps absent from monthly data.
2. If a daily timestamp overlaps a monthly timestamp, OHLCV must match exactly/to source precision or FAIL_CLOSED.
3. No interpolation.
4. No forward fill.
5. No synthetic candles.
6. No date-window shift.
7. After repair, the frozen 2021-01-01 00:00 through 2025-12-31 23:00 UTC sequence must contain every exact hourly timestamp.
8. Hash every daily repair ZIP in the provenance receipt.

## Unchanged

No change to:
- ETHUSDT / SOLUSDT / BNBUSDT universe;
- 1h timeframe;
- evaluation dates;
- 2026 lock;
- Parent V5;
- Sticky H1;
- causal execution;
- funding rates or official funding mark-price hierarchy;
- fees/slippage;
- scientific gates.

This amendment repairs source completeness only and cannot create promotion credit by itself.
