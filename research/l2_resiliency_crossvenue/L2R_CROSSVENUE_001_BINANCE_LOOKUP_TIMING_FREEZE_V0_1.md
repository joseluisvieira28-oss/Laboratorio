# L2R-CROSSVENUE-001 — BINANCE EXTERNAL LOOKUP TIMING FREEZE V0.1

Date: 2026-10-01
Status: **FROZEN PRE-OUTCOME / SOURCE-TIMING ONLY**

## Scope

This freeze advances only the external Binance timestamp/cadence requirement for `L2R-CROSSVENUE-001`.

No cross-venue price response, return, WEAK/STRONG contrast, PnL, fees, Sharpe, leverage, 2025 outcome or 2026 outcome was computed.

## Source-only evidence

GitHub Actions run: `36816039423`
Artifact ID: `11141960210`
Artifact digest: `sha256:22de1277f5b87da2c1ff0bb8c6a89b75170d6830bee9eca469880956cdc3a336`

Source:
- Binance spot
- BTCUSDT
- official public historical daily aggTrades from `data.binance.vision`
- 20 dates frozen before this preflight: 5 dates in each of Q1/Q2/Q3/Q4 2024
- official `.CHECKSUM` SHA256 verified for all 20 daily ZIPs

Observed timestamp-only cadence:
- days verified: 20/20
- rows: 26,709,532
- inter-aggTrade gaps: 26,709,512
- p50: 1 ms
- p90: 194 ms
- p95: 385 ms
- p99: 946 ms
- p99.9: 1,947 ms
- maximum observed gap: 10,830 ms
- gap coverage <= 1,100 ms: 99.3283404055%
- gap coverage <= 1,500 ms: 99.7381232574%
- gap coverage <= 2,000 ms: 99.9113836299%
- gap coverage <= 3,000 ms: 99.9867762466%

## Frozen external lookup rule

For every external Binance observation target required later by the already-frozen six parent cells:

1. use the **first Binance BTCUSDT spot aggTrade timestamp at or after the target timestamp**;
2. no interpolation;
3. no backward fill;
4. maximum allowed lateness = **2,000 ms**;
5. if no eligible aggTrade is available within 2,000 ms, that external observation is timing-gated;
6. no best-cell or per-date tolerance adjustment is permitted.

The 2,000 ms maximum lateness was derived before any cross-venue outcome from:

`ceil(global timestamp-only p99.9 / 100 ms) × 100 ms`

with global p99.9 = 1,947 ms.

This cadence rule is source-quality engineering only and must not be changed after Binance price responses are opened.

## Remaining gate

The parent event anchor artifact must still be materialized byte-authoritatively before any Discovery outcome:

`L2_RESILIENCY_001_SWEEP_EVENT_ANCHORS_V0_1.csv`

Expected SHA256:

`be2c2d795a55ac3522fc6f3cdeb2d2c2ccf38bef8640a505934cbc76d9337eb3`

2025 remains protected holdout.
2026 remains forbidden.
No live trading, orders, exchange mutation or main merge.
