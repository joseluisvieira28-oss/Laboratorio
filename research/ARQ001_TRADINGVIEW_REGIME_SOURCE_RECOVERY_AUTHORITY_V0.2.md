# ARQ-001-DRF-001 — TRADINGVIEW REGIME SOURCE RECOVERY AUTHORITY V0.2

Date: 2026-09-18
Status: FROZEN / SOURCE-ONLY / OUTCOME-BLIND
Branch: arq001-dominance-regime-follower-v0.1

## Purpose

Resolve only the frozen regime-source blocker for ARQ-001-DRF-001.

Required TradingView CRYPTOCAP series:
- BTC.D
- USDT.D
- TOTAL3

The economic hypothesis, BTC/ALT baseline, thresholds, horizons, costs, ablation and 2022-2024 Discovery split remain unchanged.

## Canonical source

Only official TradingView chart-data CSV exports are admissible for V0.2.

No unofficial scraping API, mirror, synthetic dominance reconstruction, CoinMarketCap/CoinGecko substitution, current-value backfill or cross-provider splice is allowed.

Official source semantics:
- CRYPTOCAP symbols are calculated by TradingView.
- BTC.D is a CRYPTOCAP dominance series.
- TOTAL3 is TradingView total crypto market cap excluding BTC and ETH.
- chart-data export exports only data actually available/loaded on the TradingView chart.

## Frozen required resolution

Exact 1-minute exports only.

Reason: the existing frozen ARQ contract uses contemporaneous 180-second regime changes during HH:00..HH:02 before entry at HH:03. V0.2 does not change that clock or approximate it with higher-timeframe bars.

## Frozen source period

2022-01-01T00:00:00Z through 2024-12-31T23:59:59Z.

2025 remains locked confirmation.
2026 remains locked final holdout.

## Source adequacy gate

For each of BTC.D, USDT.D and TOTAL3:

1. official TradingView CSV provenance identified;
2. 1-minute timestamp semantics parse unambiguously to UTC;
3. no duplicate minute timestamps;
4. no timestamp outside the frozen 2022-2024 source period is admitted to the source receipt;
5. coverage is sufficient to evaluate every top-of-hour ARQ regime window that survives the already-frozen Binance source mask;
6. for each usable UTC hour, required regime observations for HH:00..HH:02 are present under one identical deterministic rule;
7. all three series use the same deterministic timestamp alignment rule;
8. source file SHA-256 is persisted before any ARQ market outcome is opened.

V0.2 does not reduce the ARQ sample because TradingView history is inconvenient. If the exports cannot support the frozen Discovery population, result = SOURCE_GATE_BLOCKED_INSUFFICIENT_INTRADAY_HISTORY.

## Allowed values

The source audit may parse:
- timestamp;
- OHLC fields from the three regime series solely to validate 1m structure and derive the already-frozen 180-second regime input later.

It may not open or compute:
- ALT/BTC future return;
- ARQ trade outcome;
- PnL/PF/drawdown;
- 2025/2026;
- post-outcome thresholds.

## Terminal states

- SOURCE_DATA_PASS
- SOURCE_GATE_BLOCKED_MISSING_EXPORT
- SOURCE_GATE_BLOCKED_INSUFFICIENT_INTRADAY_HISTORY
- SOURCE_PROVENANCE_FAILURE
- SOURCE_SCHEMA_FAILURE

No terminal state here is NO_EDGE.

## Activation

Expected file paths:
- research/arq001_source_inputs/BTC.D.csv
- research/arq001_source_inputs/USDT.D.csv
- research/arq001_source_inputs/TOTAL3.csv

The source auditor may run whenever all three files are supplied. Discovery remains prohibited unless SOURCE_DATA_PASS is persisted first.
