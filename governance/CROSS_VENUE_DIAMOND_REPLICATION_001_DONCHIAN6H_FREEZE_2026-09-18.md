# CROSS-VENUE-DIAMOND-REPLICATION-001 — DONCHIAN 6H FREEZE — 2026-09-18

Status: FROZEN_BEFORE_CROSS_VENUE_SOURCE_ACCESS_OR_OUTCOMES
Parent campaign: HTF-DIAMOND-HUNT-001
Primary candidate: DH-02-HO1
Parent branch: htf-donchian-shadow-v0.1
Replication branch: cross-venue-diamond-replication-001-donchian6h

## Objective

Test whether the exact promoted Donchian 6H candidate generalizes from Binance USD-M perpetuals to independent perpetual venues without changing signal logic, asset set, direction, horizon, costs, or adjudication after outcomes.

This experiment is research-only and outcome-blind until the source gate passes.

## Frozen parent identity

Symbols:
- BTCUSDT
- ETHUSDT
- SOLUSDT
- BNBUSDT
- XRPUSDT
- DOGEUSDT

Signal timeframe: 6H UTC
Direction: LONG_ONLY
Donchian lookback: 80 complete 6H bars
ATR length: 56
Entry: next 6H open
Stop: signal low minus 0.25 * ATR56
Target: 3.0R
Maximum hold: 160 x 6H bars
One active trade per symbol: true
BASE round-trip cost: 20 bps
STRESS round-trip cost: 30 bps
Funding: actual venue funding cashflows while the position is open
Intrabar execution path: 1-minute trade-price candles, preserving the parent stop/target ambiguity rule
Bootstrap: 5000 repetitions, seed 230911, UTC entry-day blocks, 95% interval

Frozen test window:
- start inclusive: 2023-01-01T00:00:00Z
- end exclusive: 2025-01-01T00:00:00Z
- forbidden in this experiment: 2025 and 2026 outcomes

## Frozen venues

VENUE A — BYBIT
- product: linear USDT perpetual
- public endpoint family: /v5/market/kline
- 6H interval: 360
- 1m interval: 1
- instrument names: exact Binance-style symbols above
- funding endpoint family: /v5/market/funding/history

VENUE B — OKX
- product: USDT-margined perpetual swap
- public endpoint family: /api/v5/market/history-candles
- 6H interval: 6Hutc
- 1m interval: 1m
- instrument mapping:
  - BTCUSDT -> BTC-USDT-SWAP
  - ETHUSDT -> ETH-USDT-SWAP
  - SOLUSDT -> SOL-USDT-SWAP
  - BNBUSDT -> BNB-USDT-SWAP
  - XRPUSDT -> XRP-USDT-SWAP
  - DOGEUSDT -> DOGE-USDT-SWAP
- funding endpoint family: /api/v5/public/funding-rate-history

No venue may be dropped after seeing outcomes.

## Stage A — source coverage gate

Before any signal, return, PnL, expectancy, profit factor, bootstrap, or direction calculation:

1. Verify each of the six frozen instruments exists on each venue.
2. Verify 6H UTC trade-price candles are retrievable around:
   - 2023-01-01
   - 2023-07-01
   - 2024-01-01
   - 2024-07-01
   - 2024-12-31
3. Verify 1m trade-price candles are retrievable around the same anchors.
4. Verify historical funding data are retrievable in the required period.
5. Persist only coverage metadata, row counts, timestamp ranges, endpoint identities, and source fingerprints. Do not persist OHLC or funding values in the Stage-A receipt.
6. If a required source is absent for any frozen symbol/venue, classify that venue as SOURCE_BLOCKED for exact replication. Do not substitute spot, mark price, index price, a different quote currency, a different timeframe, or another symbol after inspection.

## Stage B — exact replication, conditional on Stage A PASS

Only a venue with full source authority may proceed.

The replication must use the exact frozen parent rule above. No retuning, no asset selection, no timeframe substitution, no venue-specific parameter change, no stop/target change, no cost reduction, and no post-outcome rescue.

## Frozen adjudication per venue

Report:
- resolved trades
- BASE expectancy in R
- BASE profit factor
- bootstrap 95% lower bound
- STRESS expectancy in R
- calendar 2023 expectancy
- calendar 2024 expectancy
- max single-symbol share of positive BASE net R
- max single-quarter share of positive BASE net R
- execution-path unresolved count

Cross-venue replication labels:
- CROSS_VENUE_SURVIVES: BASE expectancy > 0, PF > 1, STRESS expectancy > 0, both calendar years > 0, at least 100 resolved trades, concentration <= 70%, and no material source/execution violation.
- CROSS_VENUE_STATISTICAL_FRAGILITY: economics above survive but bootstrap lower 95% <= 0.
- CROSS_VENUE_FAIL: BASE expectancy <= 0, PF <= 1, STRESS <= 0, a calendar year <= 0, or a material frozen economic gate fails.
- SOURCE_BLOCKED: exact source coverage is not available; this is not an economic rejection.

The parent Binance classification is immutable. A Bybit or OKX result cannot rewrite the historical parent result.

## Governance

- research_only: true
- no_live_trading: true
- no_exchange_mutation: true
- no_authenticated_exchange_api: true
- no_orders: true
- no_wallets: true
- no_alerts_webhooks: true
- no_merge_to_main: true
- no_2025_outcomes: true
- no_2026_outcomes: true
- no_post_outcome_tuning: true
- no_asset_selection: true
- no_venue_selection_after_outcomes: true
