# LIQUID CO-INVEST FORWARD — OUTCOME RESOLUTION FREEZE V0.1

Date: 2026-10-05
Branch: liquid-coinvest-forward-v0.1-prereg-2026-10-05
Status: ACTIVE / FROZEN BEFORE FIRST OUTCOME

This freeze is subordinate to LIQUID_COINVEST_FORWARD_PREOUTCOME_FREEZE_V0.1.md and exists only to define deterministic market outcomes before any +1h or +4h outcome is opened.

## Canonical outcome source

Public, unauthenticated Binance USDⓈ-M perpetual 1-minute klines.

Endpoint family:
- base: https://fapi.binance.com
- path: /fapi/v1/klines
- interval: 1m

Frozen symbol mapping:
- BTC -> BTCUSDT
- ETH -> ETHUSDT
- SOL -> SOLUSDT

No API key, account read, order endpoint, wallet, private endpoint or exchange mutation is permitted.

## Price clock

For each durable Co-Invest observation with observed_at_utc = Tobs:

1. Compute entry_minute_utc as the NEXT exact whole UTC minute strictly after Tobs.
2. Entry price is the OPEN of the Binance USD-M 1m kline whose open time equals entry_minute_utc.
3. +1h outcome price is the OPEN of the 1m kline whose open time equals entry_minute_utc + 60 minutes.
4. +4h outcome price is the OPEN of the 1m kline whose open time equals entry_minute_utc + 240 minutes.

A horizon is never queried before its target minute has fully begun. If the exact required kline is unavailable, malformed, duplicated, or has a mismatched open timestamp, the horizon is SOURCE_BLOCKED and must not be imputed.

## Frozen return definitions

For horizon H:
- simple_return_pct = 100 * (exit_open / entry_open - 1)
- absolute_return_pct = abs(simple_return_pct)

No fees, slippage or trading PnL are applied because this experiment is testing predictive information, not an executable trading strategy.

## Event population

All monitor captures remain durable.

However, confirmatory information events are restricted to proprietary positioning source advances:

- The first post-freeze observation for each symbol is BASELINE_ONLY.
- A later row is EVENT_ELIGIBLE only when its source_created_at_utc is strictly later than the previous durable post-freeze source_created_at_utc for that symbol AND the proprietary size-tier payload advances.
- DUPLICATE_SOURCE_SNAPSHOT rows are never independent events.
- If source timestamp advances but the proprietary payload is byte-equivalent, classify SOURCE_TIMESTAMP_ONLY and do not count it as an information event.
- If payload changes while source timestamp does not, classify SOURCE_INTEGRITY_CONFLICT and fail closed pending audit.

This event-population rule is frozen before the first outcome.

## Feature isolation

Two families remain separate.

LIQUIDATION-FLOW-FWD-001-LIQUID-V0.1 may use only:
- liq_near_total_usd
- liq_near_total_usd / total_positioning_usd
- whale_liq_near_usd
- whale_liq_near_usd / whale_total_position_value_usd
- open_interest_usd
- funding_pct

COHORT-DIVERGENCE-FWD-001-LIQUID-V0.1 may use only:
- smart_money_long_pct
- losing_crowd_long_pct
- cohort_divergence_pp
- whale_long_share
- open_interest_usd
- funding_pct

No feature-family fusion is authorized.

## No threshold fishing

During source-cadence calibration:
- collect and resolve outcomes, but do not select predictive thresholds;
- do not rank candidate thresholds by realized returns;
- do not change horizons;
- do not drop losing events.

After cadence calibration is frozen, any threshold/model activation must receive a NEW pre-outcome activation freeze using only outcome-blind source-distribution information where possible.

## Outcome receipts

Outcome receipts must be append-only under:
research/liquid_coinvest_forward/outcomes/

Each outcome receipt must include:
- source observation_id
- symbol
- observed_at_utc
- entry_minute_utc
- horizon
- target_minute_utc
- resolved_at_utc
- Binance symbol
- exact raw kline rows used for entry and exit
- entry_open
- exit_open
- simple_return_pct
- absolute_return_pct
- source endpoint identity
- status

No outcome receipt may overwrite an existing receipt.
