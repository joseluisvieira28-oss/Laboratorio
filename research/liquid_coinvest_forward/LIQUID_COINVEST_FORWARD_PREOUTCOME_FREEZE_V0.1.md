# LIQUID CO-INVEST FORWARD EXPERIMENT — PRE-OUTCOME FREEZE V0.1
Date: 2026-10-05
Branch: liquid-coinvest-forward-v0.1-prereg-2026-10-05
Status: ACTIVE / FORWARD-ONLY / PRE-OUTCOME

## Scientific boundary

This experiment is prospective only. No historical Co-Invest positioning or liquidation fields may be reconstructed after observing outcomes. No post-outcome threshold tuning is permitted.

No live trading, orders, account mutation, deposits, withdrawals, wallets, or exchange mutation are authorized by this experiment.

## Source gate result

Co-Invest exposes, for supported markets:
- mark price
- funding
- open interest
- positioning by size tier
- position counts by size tier
- total and long position value by size tier
- valueCloseToLiquidation
- smart-money vs losing-crowd positioning when available
- a source-side createdAt timestamp

Observed source limitation before this freeze:
- market price / OI can advance while the proprietary positioning snapshot remains unchanged;
- historical proprietary positioning access was not demonstrated;
- semantics of pastPositionCount / pastTotalPositionValue cadence are undocumented;
- methodology behind valueCloseToLiquidation is proprietary/undocumented.

Therefore:
- historical backtest using proprietary positioning/liquidation snapshots: BLOCKED;
- prospective collection before outcomes: AUTHORIZED.

## Universe

Frozen initial universe:
- BTC
- ETH
- SOL

No symbol may be added to the confirmatory dataset without a new pre-outcome amendment.

## Observation payload

For every accepted observation, persist:
- observation_id
- observed_at_utc
- source_created_at_utc
- source_age_seconds
- symbol
- mark_price
- funding
- open_interest_usd
- day_notional_volume
- smart_money_long_pct (nullable)
- losing_crowd_long_pct (nullable)
- cohort_divergence_pp (nullable)
- per-size-tier:
  - size label
  - min_size
  - max_size
  - position_count
  - total_position_value
  - total_position_value_long
  - value_close_to_liquidation
  - bias
- liq_near_total_usd
- whale_liq_near_usd, defined as sum of valueCloseToLiquidation for tiers >= $250k
- whale_total_position_value_usd, defined as sum of totalPositionValue for tiers >= $250k
- whale_long_share, defined as whale totalPositionValueLong / whale totalPositionValue
- raw source receipt / exact source payload when available

## Freshness calibration phase

The first phase is SOURCE CADENCE CALIBRATION.

No predictive verdict may be issued until cadence is characterized prospectively.

During calibration, every snapshot is stored regardless of staleness, but is tagged:
- FRESHNESS_UNKNOWN
- DUPLICATE_SOURCE_SNAPSHOT when source_created_at and proprietary positioning payload are unchanged from prior capture
- ADVANCED_SOURCE_SNAPSHOT when source_created_at or proprietary positioning payload advances

The freshness acceptance threshold is NOT frozen yet. It may be set only from source cadence observations and before any outcome-conditioned analysis.

## Outcomes

Outcomes are resolved only after the observation receipt exists.

Frozen horizons:
- +1h
- +4h

A +15m horizon is deferred because the current automation surface cannot collect more frequently than hourly and the observed positioning source may refresh more slowly than market data.

Outcome fields:
- outcome_price
- simple_return_pct
- absolute_return_pct
- max favorable excursion when defensibly recoverable from pre-specified market data
- max adverse excursion when defensibly recoverable from pre-specified market data

Primary market outcome source should be the same Liquid/Co-Invest market-data surface when available.

## Candidate families

Two distinct families are frozen for prospective data collection:

### LIQUIDATION-FLOW-FWD-001-LIQUID-V0.1
Candidate explanatory variables:
- liq_near_total_usd
- liq_near_total_usd / total positioning value
- whale_liq_near_usd
- whale_liq_near_usd / whale_total_position_value_usd
- open interest
- funding

### COHORT-DIVERGENCE-FWD-001-LIQUID-V0.1
Candidate explanatory variables:
- smart_money_long_pct
- losing_crowd_long_pct
- cohort_divergence_pp = smart_money_long_pct - losing_crowd_long_pct
- whale_long_share
- open interest
- funding

These are separate families. They must not be merged into a feature soup unless a new pre-outcome model freeze explicitly authorizes it.

## Prohibited

- opening outcomes before an observation is durably recorded;
- selecting thresholds after seeing forward returns;
- changing horizons after seeing results;
- deleting losing observations;
- using undocumented past* fields as predictive deltas;
- claiming smart money / liquidation methodology beyond what the source documents;
- treating duplicate/stale proprietary snapshots as independent information events;
- live trading or automatic order placement.

## Verdict labels

Permitted final labels:
- SOURCE_BLOCKED
- FORWARD_INSUFFICIENT
- NO_EDGE
- SURVIVES_FORWARD
- NEEDS_CONFIRMATION

No DIAMOND / GO / MICRO-LIVE label may be assigned from this experiment alone.
