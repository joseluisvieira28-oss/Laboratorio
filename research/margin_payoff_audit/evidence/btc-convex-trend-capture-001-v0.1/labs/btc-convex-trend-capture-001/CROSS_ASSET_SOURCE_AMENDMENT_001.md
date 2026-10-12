# BTC-CONVEX-TREND-CAPTURE-001 — CROSS-ASSET SOURCE AMENDMENT 001

**Date:** 2026-09-23  
**Status:** FROZEN BEFORE ANY ETH/SOL/BNB ECONOMIC OUTCOME  
**Reason:** transport/source-access repair only

## Trigger

The first cross-asset source gate confirmed complete monthly 1h price-file coverage for:
- ETHUSDT: 61/61;
- SOLUSDT: 61/61;
- BNBUSDT: 61/61.

However, GitHub Actions access to the public USD-M REST funding endpoint:
`https://fapi.binance.com/fapi/v1/fundingRate`

returned HTTP 451 for all three symbols.

No cross-asset economic outcomes were computed or opened.

## Amendment

Replace only the funding acquisition transport with Binance's public historical archive:

`https://data.binance.vision/data/futures/um/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-YYYY-MM.zip`

This remains Binance public historical futures data.

Unchanged:
- ETH/SOL/BNB universe;
- 1h timeframe;
- 2021-01-01 through 2025-12-31 evaluation;
- 2026 locked;
- Parent V5 parameters;
- Sticky H1 parameters;
- causal execution semantics;
- funding cashflow formula;
- commission;
- BASE/STRESS slippage;
- scientific gates;
- no-rescue rules.

## Funding record semantics

The archive must provide a funding timestamp and funding rate.

If the archive also contains a usable mark price at the funding timestamp, use it.

Otherwise use the already frozen fallback:
- Binance 1h market OPEN whose open timestamp equals the funding timestamp.

If the archive schema cannot be parsed reproducibly or has incomplete required coverage:
- DATA_BLOCKED;
- STOP before economic outcomes.

## Audit trail

The failed REST source gate remains preserved as evidence and is not rewritten.

This amendment supersedes only the funding transport/source-access clause where it conflicts with the original freeze.
