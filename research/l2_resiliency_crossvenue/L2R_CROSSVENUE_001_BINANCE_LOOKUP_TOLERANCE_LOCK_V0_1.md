# L2R-CROSSVENUE-001 — BINANCE EXTERNAL LOOKUP TOLERANCE LOCK V0.1

Date: 2026-10-01
Status: **FROZEN PRE-OUTCOME**

## Scope

This lock freezes the external Binance BTCUSDT spot aggTrades lookup tolerance using **timestamp cadence only**.

No price column was parsed.
No return, signed response, weak/strong cross-venue contrast, PnL, fee, 2025 outcome, or 2026 outcome was opened.

## Source-only cadence evidence

Canonical workflow run:
- run_id: `36816039423`
- head_sha: `6324c3cb2570533468b2c9a9f5b05d9f7d60835d`
- artifact_id: `11141960210`
- artifact_zip_sha256: `22de1277f5b87da2c1ff0bb8c6a89b75170d6830bee9eca469880956cdc3a336`

Frozen source sample:
- Binance official public historical spot aggTrades
- symbol: BTCUSDT
- year: 2024 only
- 20 dates frozen before cadence analysis
- 26,709,532 aggregate trades
- 26,709,512 inter-trade timestamp gaps

Observed cadence:
- p50: 1 ms
- p90: 194 ms
- p95: 385 ms
- p99: 946 ms
- p99.9: 1,947 ms
- max observed gap: 10,830 ms

Observed gap coverage:
- <= 1,100 ms: 99.32834040547053%
- <= 1,500 ms: 99.73812325736239%
- <= 2,000 ms: 99.9113836299218%
- <= 3,000 ms: 99.98677624660458%
- <= 5,000 ms: 99.99959190568514%

## Frozen external lookup rule

For every parent Hyperliquid target timestamp used by the later Discovery runner:

1. Search Binance BTCUSDT spot aggTrades for the **first executed aggregate trade timestamp at or after the exact target timestamp**.
2. Accept the external observation only when:
   `0 <= observed_timestamp - target_timestamp <= 2,000 ms`.
3. Do not interpolate.
4. Do not backfill from a trade before the target.
5. Do not widen 2,000 ms after any Binance price or response outcome is observed.
6. A missing qualifying trade is classified as external source/timing gated for that lookup.

### Why 2,000 ms

The threshold is chosen before any outcome opening from timestamp cadence alone. It is the smallest tested round threshold above the observed aggregate p99.9 cadence (1,947 ms), covering 99.9113836299218% of observed 2024 inter-aggTrade gaps.

This is a source-timing design choice, not an effect-maximizing threshold.

## Remaining blocker before Discovery

The exact parent event anchors remain required:

`L2_RESILIENCY_001_SWEEP_EVENT_ANCHORS_V0_1.csv`

Recorded SHA256:

`be2c2d795a55ac3522fc6f3cdeb2d2c2ccf38bef8640a505934cbc76d9337eb3`

The Library contains the historical ZIP snapshot, but its bytes are currently not exportable through the connected runtime. Exact recovery or deterministic regeneration from preserved 2024 Hyperliquid raw bodies remains required before any Discovery outcome may be opened.

## Firewalls

- Binance price parsed: false
- returns computed: false
- signed responses computed: false
- weak/strong cross-venue contrast computed: false
- 2025 cross-venue outcomes accessed: false
- 2026 accessed: false
- live trading: false
- orders: false
- exchange mutation: false
- main merge: false

