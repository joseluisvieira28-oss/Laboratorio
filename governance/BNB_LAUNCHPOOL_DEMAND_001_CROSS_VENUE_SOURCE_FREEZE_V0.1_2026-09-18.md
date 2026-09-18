# BNB-LAUNCHPOOL-DEMAND-001 — CROSS-VENUE SOURCE FREEZE V0.1 — 2026-09-18

Status: FROZEN_BEFORE_CROSS_VENUE_MARKET_OUTCOMES
Branch: bnb-launchpool-cross-venue-source-v0.1
Parent branch: bnb-launchpool-demand-v3-readjudication-2026-09-17
Parent status: TIER_2_PROMOTED_CANDIDATE__QUASE_DIAMANTE__HIGH_TAIL_CONCENTRATION_FRAGILITY

## Immutable mechanism

No trading rule changes are authorized.

- signal source: official Binance Launchpool announcement with explicit BNB staking/locking/farming utility;
- direction: LONG;
- market identity: BNBBTC spot;
- entry: first 15-minute open strictly after canonical announcement timestamp;
- hold: 24 hours;
- BASE round-trip cost: 20 bps;
- STRESS round-trip cost: 30 bps;
- maximum one active trade;
- information clustering: <= 60 minutes;
- no stop;
- no target;
- no leverage.

The signal remains Binance-announcement-defined. Cross-venue replication changes only the execution market source.

## Frozen external venues

VENUE A — BYBIT
- product: spot
- exact symbol: BNBBTC
- instrument endpoint family: /v5/market/instruments-info
- 15m trade-price endpoint family: /v5/market/kline
- public unauthenticated data only

VENUE B — OKX
- product: spot
- exact instrument: BNB-BTC
- instrument endpoint family: /api/v5/public/instruments
- 15m trade-price endpoint family: /api/v5/market/history-candles
- historical bulk endpoint family, if needed after a separate binding gate: /api/v5/public/market-data-history
- public unauthenticated data only

No alternate quote currency, synthetic BNB/BTC cross-rate, BNBUSDT substitution, perpetual substitution, mark/index price, or replacement venue is allowed after outcomes.

## Stage A — source-only coverage probe

Before any cross-venue return, PnL, expectancy, PF, win-rate or event-performance calculation:

1. verify exact spot instrument existence;
2. test historical 15m timestamp availability around frozen anchors:
   - 2020-09-01T00:00:00Z
   - 2021-01-01T00:00:00Z
   - 2022-01-01T00:00:00Z
   - 2023-01-01T00:00:00Z
   - 2024-01-01T00:00:00Z
   - 2025-01-01T00:00:00Z
   - 2025-12-01T00:00:00Z
3. persist metadata only: provider code/status, timestamp count/range, anchor presence, transport error and timestamp fingerprints;
4. do not persist OHLC values;
5. do not calculate any strategy outcome.

A source/transport failure is SOURCE_BLOCKED, not NO_EDGE.

## Routing

Per venue:
- EXACT_SOURCE_ANCHOR_PASS: exact instrument exists and every frozen historical anchor is represented by 15m trade-price timestamps.
- SOURCE_PARTIAL: exact instrument exists but one or more historical anchors are unavailable.
- SOURCE_BLOCKED_ENVIRONMENT: transport is blocked from the runner.
- SOURCE_BINDING_BLOCKED: exact instrument or exact source type cannot be established.

Only a separately frozen Stage B may open cross-venue market outcomes.

## Governance

research_only = true
outcome_blind_stage_a = true
no_live_trading = true
no_orders = true
no_exchange_mutation = true
no_authenticated_exchange_api = true
no_wallets = true
no_alerts_webhooks = true
no_merge_main = true
no_post_outcome_tuning = true
no_pair_substitution = true
no_venue_selection_after_outcomes = true
