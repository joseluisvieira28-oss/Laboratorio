# PREDICTION-ORACLE-BASIS-001 — SOURCE GATE SPEC V0.1

Status: DESIGN_FROZEN / NOT_EXECUTED
Date: 2026-09-27

## Source feasibility already established at documentation level

### Polymarket
Public BTC Up/Down hourly markets explicitly state that resolution uses the Binance BTC/USDT 1H candle and warn that the market is about Binance BTC/USDT rather than other exchanges or pairs.

### Kalshi
Public API documentation exposes market objects containing bid/ask, bid/ask sizes, volume, open interest, timestamps, rules and settlement fields. Exact BTC series/rules must still be enumerated and verified prospectively.

## Gate tasks
1. Enumerate current BTC hourly binary series on both venues without selecting by price/PnL.
2. Snapshot exact rule text and immutable identifiers.
3. Determine whether an EXACT_EXCEPT_ORACLE matching population currently exists.
4. Verify bid/ask and size collection at the required cadence.
5. Verify public fee schedule provenance.
6. Identify the exact USD reference used by each Kalshi BTC series.
7. Freeze one USDT/USD basis source with point-in-time timestamps.
8. Run a source-only capture window.
9. Produce coverage, missingness, timestamp-lag and schema-change diagnostics only.

## Hard stop
If no current EXACT_EXCEPT_ORACLE population exists, close as SOURCE_POPULATION_UNAVAILABLE. Do not broaden to semantically different contracts simply to obtain a sample.

If public data cannot establish synchronized executable quotes, classify SOURCE_DATA_BLOCKED. Do not substitute last prices, screenshots or reconstructed mids.

## No economic outputs in Source Gate
Do not calculate:
- strategy PnL;
- profitability;
- win rate;
- optimal threshold;
- best hour;
- best direction;
- expected return.

Those require a separately frozen post-source protocol.
