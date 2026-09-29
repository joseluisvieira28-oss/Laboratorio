# CROSS-VENUE-DIAMOND-REPLICATION-002 — AVAX20 FREEZE — 2026-09-18

Status: FROZEN_BEFORE_CROSS_VENUE_SOURCE_ACCESS_OR_OUTCOMES
Parent candidate: CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1
Parent branch: ced-1d-v3-byte-recovery-2026-09-17
Replication branch: cross-venue-diamond-replication-002-avax20

## Objective

Test whether the exact promoted CED1D-0031 candidate generalizes from Binance USD-M AVAXUSDT to independent perpetual venues without changing the parent signal implementation, direction, lookback, horizon, execution semantics, costs, sample rules, or adjudication after outcomes.

## Immutable parent authority

The venue replication MUST consume the exact frozen parent implementation and semantics already recovered on the parent branch:
- V0.3 runner ZIP SHA256: df625d0d4a05c55ba34ca51514d31fd61636ff0a823567585c2d02afa0877958
- hypotheses.py SHA256: dc52cdc16aee0ba586ec7081a39ce68d62c5544e9bd27186255b4d9a87368693
- candidate: CED1D-0031
- family: A_MOMENTUM
- symbol: AVAXUSDT
- lookback: 20 calendar days
- horizon: 1 day
- direction: CONTINUATION
- BASE nonfunding cost: 14 bps round trip
- STRESS nonfunding cost: 20 bps round trip
- funding: actual venue funding cashflows under the same parent position direction and holding interval
- one active trade semantics and overlap handling: identical to parent V0.3 implementation
- no reconstruction of signal_for or execution rules from memory is allowed

The venue adapter may only translate venue raw data into the exact parent daily-series input semantics. It may not change the signal or execution algorithm.

## Frozen historical block

Warmup source window:
- 2024-09-01T00:00:00Z through 2024-12-31T23:59:59Z

Replication block:
- 2025-01-01T00:00:00Z through 2025-12-31T23:59:59Z

2026+ is forbidden.

## Frozen venues

VENUE A — BYBIT
- product: linear USDT perpetual
- instrument: AVAXUSDT
- 1m trade-price endpoint family: /v5/market/kline
- funding endpoint family: /v5/market/funding/history
- public unauthenticated data only

VENUE B — OKX
- product: USDT-margined perpetual swap
- instrument: AVAX-USDT-SWAP
- 1m trade-price endpoint family: /api/v5/market/history-candles
- funding endpoint family: /api/v5/public/funding-rate-history
- public unauthenticated data only

No venue may be dropped after outcomes.

## Stage A — source coverage gate

Before any signal, return, PnL, expectancy, PF, bootstrap, win-rate, direction-performance, or outcome calculation:

1. Verify the frozen instrument exists on each venue.
2. Verify 1m trade-price history around frozen anchors spanning warmup and 2025.
3. Verify funding history around the same historical block.
4. Persist metadata only: endpoint identity, timestamp counts/ranges, anchor presence, errors, and source fingerprints.
5. Do NOT persist OHLC values or funding-rate values in the Stage-A receipt.
6. A missing required source produces SOURCE_BLOCKED for that venue. Do not substitute spot, mark/index candles, another quote currency, another exchange, another timeframe, synthetic prices, or interpolated data.

## Stage B — exact replication, conditional on Stage A PASS

Only a venue that passes Stage A may proceed.

The Stage-B implementation must import/use the exact frozen V0.3 hypothesis implementation. Any venue adapter must reproduce the parent daily-series requirements, including complete-day handling and execution-time semantics, before outcomes are opened.

No retuning, no threshold change, no direction flip, no calendar subperiod selection, no venue-specific rule change, no cost reduction, no event deletion, no post-outcome rescue.

## Frozen cross-venue reporting

Per venue report at minimum:
- inference event count
- BASE funded mean bps/event
- BASE PF
- STRESS funded mean bps/event
- positive active months / total active months
- positive quarters
- leave-one-month-out status
- concentration diagnostics
- source/execution unresolved count

Replication labels:
- CROSS_VENUE_SURVIVES: BASE mean > 0, PF > 1, STRESS mean > 0, at least half of active months positive, and no material source/execution violation.
- CROSS_VENUE_FRAGILE_SURVIVAL: base/stress economics survive but statistical/block-stability fragilities remain.
- CROSS_VENUE_FAIL: BASE mean <= 0, PF <= 1, STRESS <= 0, or a material frozen economic gate fails.
- SOURCE_BLOCKED: exact source coverage unavailable; not an economic rejection.

The historical Binance V3 classification remains immutable regardless of replication outcome.

## Governance

- research_only: true
- outcome_blind_stage_a: true
- no_live_trading: true
- no_exchange_mutation: true
- no_authenticated_exchange_api: true
- no_orders: true
- no_wallets: true
- no_alerts_webhooks: true
- no_merge_to_main: true
- no_2026_outcomes: true
- no_post_outcome_tuning: true
- no_venue_selection_after_outcomes: true
