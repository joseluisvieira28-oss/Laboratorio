# CBBTC-ETH-MINT-BURN-FLOW-001 — PRE-OUTCOME FLOW STATE / PARTITION FREEZE V0.1

Frozen: 2026-09-26
Freeze timing: BEFORE full census distribution and BEFORE all price outcomes.

## Frozen predictor

Primary predictor:
daily signed cbBTC Ethereum zero-address net flow divided by prior-day circulating supply.

Exact rational:
f_t = (mint_t - burn_t) / prior_supply_t

Days with prior_supply_t <= 0 are invalid for state calibration.

## Calendar partitions

Burn-in / source-only:
2024-09-12 through 2024-09-30 inclusive.

Calibration:
2024-10-01 through 2025-06-30 inclusive.

Discovery predictor-sample region:
2025-07-01 through 2025-12-31 inclusive.

Protected holdout:
2026-01-01 onward.

2026 remains unopened.

## Frozen state thresholds

If and only if PREDICTOR_FLOW_CENSUS_PASS:

Compute nearest-rank quantiles over all valid calibration f_t values:

q10 = 10th percentile
q90 = 90th percentile

States:
- NEGATIVE_EXTREME when f_t <= q10
- POSITIVE_EXTREME when f_t >= q90
- NEUTRAL otherwise

Both tails are mandatory.

Calibration fails if:
- q10 >= q90;
- any required calibration day lacks a valid prior supply;
- supply reconciliation did not pass.

No q05/q95, q20/q80, z-score or raw-amount rescue is permitted after outcomes.

## Frozen event de-clustering

Discovery entry event occurs only on transition into a tail:
- current NEGATIVE_EXTREME and previous UTC-day state != NEGATIVE_EXTREME;
- current POSITIVE_EXTREME and previous UTC-day state != POSITIVE_EXTREME.

The 2025-06-30 predecessor state must be classified using the same thresholds.

Consecutive same-tail days form one episode.

## Outcome-blind sample gate

Before any BTC/cbBTC price is opened, classify all 2025-07-01 through 2025-12-31 days.

FLOW_PREDICTOR_SAMPLE_PASS requires:
- all calendar days present;
- exact supply-normalized state available every day;
- >=20 transition-entry events total;
- >=6 NEGATIVE_EXTREME entries;
- >=6 POSITIVE_EXTREME entries;
- zero source/reconciliation errors.

If source fails:
FLOW_PREDICTOR_SOURCE_BLOCKED.

If source passes but sample fails:
FLOW_PREDICTOR_INSUFFICIENT_SAMPLE.

Neither state opens price outcomes.

## No direction yet

This freeze does not assert that positive issuance is bullish or negative issuance is bearish.

A separate mechanism/outcome freeze is mandatory before any BTC return is opened.

## No promotion credit

Source/census/calibration/sample-gate work earns zero trading-edge promotion credit.
