# ARQ-001-DRF-001 — OFFICIAL TRADINGVIEW CHUNKED CSV SOURCE RECOVERY AUTHORITY V0.3

Date frozen: 2026-10-03
Status: FROZEN / SOURCE-ONLY / OUTCOME-BLIND
Parent: ARQ-001-DRF-001

## Purpose

Resolve only the frozen 1-minute TradingView regime-source blocker without changing the ARQ-001 economic hypothesis, event clock, thresholds, costs, assets, horizons, or temporal split.

TradingView officially documents that chart CSV export contains chart data that has actually been loaded. Current intraday chart bar limits are materially smaller than the full 2022-2024 1-minute period, while Bar Replay on Premium/professional plans may access deeper historical intraday time-based data.

Therefore V0.3 permits multiple official TradingView chart-data CSV exports per frozen CRYPTOCAP series and deterministically stitches them into one canonical 1-minute source series.

## Frozen admissible source

Only official TradingView chart-data CSV exports for:
- CRYPTOCAP:BTC.D
- CRYPTOCAP:USDT.D
- CRYPTOCAP:TOTAL3

Required timeframe:
- 1 minute

No:
- unofficial TradingView websocket/API scraping;
- mirror;
- CoinMarketCap/CoinGecko substitute;
- synthetic dominance;
- interpolation;
- resampling from higher timeframes;
- current-value backfill;
- cross-provider splice.

## Input directories

- research/arq001_source_inputs_v03/BTC.D/*.csv
- research/arq001_source_inputs_v03/USDT.D/*.csv
- research/arq001_source_inputs_v03/TOTAL3/*.csv

Each directory may contain one or many official CSV exports.

## Deterministic merge

For each series:
1. parse only rows whose timestamps resolve unambiguously to UTC minute boundaries;
2. retain only 2022-01-01T00:00:00Z through 2024-12-31T23:59:00Z for the source receipt;
3. require finite OHLC values;
4. duplicate timestamps are allowed only when OHLC values are byte/numerically identical after parsing;
5. conflicting duplicate timestamps => SOURCE_PROVENANCE_FAILURE;
6. sort ascending by timestamp;
7. preserve exact original per-file SHA-256 values in the receipt;
8. write one canonical merged CSV plus SHA-256 before any ARQ market outcome is opened.

No current or future ARQ outcome may affect merge logic.

## Conservative source adequacy gate

Because the frozen Binance event mask is not yet allowed to influence source acquisition, V0.3 uses a strict superset gate.

For every UTC hour from 2022-01-01 through 2024-12-31 inclusive, all three source series must contain:
- HH:00
- HH:01
- HH:02

This is sufficient for every possible frozen ARQ regime window.

If a series lacks any required minute:
SOURCE_GATE_BLOCKED_INSUFFICIENT_INTRADAY_HISTORY.

This conservative gate may reject a source that could theoretically cover only the eventual Binance mask; it may not falsely admit an under-covered source.

## Expected source scale

Three calendar years contain 26,304 UTC hours, therefore:
- expected required regime minutes per series = 78,912

This gate concerns only the three event-window minutes per hour, not all 1,578,240+ calendar minutes.

## Schema

Accepted timestamp header names:
- time
- Time
- timestamp
- Timestamp
- datetime
- Date
- date

Accepted OHLC header names are case-insensitive:
- open
- high
- low
- close

The auditor must record the observed schema. It may not infer missing OHLC from another field.

## Terminal classifications

- SOURCE_DATA_PASS
- SOURCE_GATE_BLOCKED_MISSING_EXPORT
- SOURCE_GATE_BLOCKED_INSUFFICIENT_INTRADAY_HISTORY
- SOURCE_PROVENANCE_FAILURE
- SOURCE_SCHEMA_FAILURE

No source classification is NO_EDGE.

## Firewall

No Binance ALT/BTC future return.
No ARQ signal outcome.
No PnL/PF/drawdown.
No 2025.
No 2026.
No live trading.
No orders.
No wallets.
No exchange mutation.
No main merge.
No post-outcome tuning.

Discovery remains prohibited unless V0.3 emits SOURCE_DATA_PASS.
