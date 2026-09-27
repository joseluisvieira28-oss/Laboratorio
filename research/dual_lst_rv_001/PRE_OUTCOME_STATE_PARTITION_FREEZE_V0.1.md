# DUAL-LST-RV-001 — PRE-OUTCOME STATE / PARTITION FREEZE V0.1

Frozen: 2026-09-27
Parent: PREDICTOR_ONLY_CENSUS_FREEZE_V0.1
Freeze timing: BEFORE any authoritative V0.1B source result, before the 556-point predictor distribution, and before all future outcomes.

## Predictor

Use only the already-frozen direct relative-NAV predictor:

d_N = direct_market_wstETH_per_rETH / protocol_relative_NAV_wstETH_per_rETH - 1.

No synthetic market construction is allowed.

## Calibration

If and only if:
- authoritative SOURCE_PASS V0.1B; and
- PREDICTOR_CENSUS_PASS with 556/556 exact frozen blocks,

compute nearest-rank quantiles over all 556 signed d_N observations:

q10 = nearest-rank 10th percentile
q90 = nearest-rank 90th percentile

States:
- RETH_CHEAP_EXTREME when d_N <= q10
- RETH_RICH_EXTREME when d_N >= q90
- NEUTRAL otherwise

Both tails are mandatory.

No q05/q95, q20/q80, z-score, raw-price, alternate-pool or volatility-normalized rescue is permitted after any outcome is opened.

## Frozen Discovery predictor grid

Discovery predictor blocks:

N_k = 24,000,000 + 7,200*k

for every integer k with:
24,000,000 <= N_k < 25,000,000.

Expected count:
139.

Boundary predecessor:
23,992,800.

The predecessor is evidence-only and is used solely for transition de-clustering.

## Event de-clustering

An event begins only on transition into a tail:

- current RETH_CHEAP_EXTREME and previous grid state != RETH_CHEAP_EXTREME;
- current RETH_RICH_EXTREME and previous grid state != RETH_RICH_EXTREME.

Consecutive same-tail observations are one episode.

No cooldown parameter may be introduced later.

## Predictor sample gate

DUAL_LST_PREDICTOR_SAMPLE_PASS requires ALL:

- 139/139 Discovery predictor blocks valid;
- boundary predecessor valid;
- total transition-entry events >= 20;
- RETH_CHEAP_EXTREME events >= 6;
- RETH_RICH_EXTREME events >= 6;
- zero source/provenance errors;
- exact same selected direct pool and protocol anchors as calibration.

If source state fails:
DUAL_LST_PREDICTOR_SOURCE_BLOCKED.

If source passes but sample is insufficient:
DUAL_LST_PREDICTOR_INSUFFICIENT_SAMPLE.

Neither classification opens future outcomes.

## Future scientific partitions

Calibration predictor-only:
<= 24,000,000 boundary as already frozen by the census.

Discovery:
24,000,000 <= entry block < 25,000,000.

OOS:
25,000,000 <= entry block < 26,000,000.

Protected holdout:
entry block >= 26,000,000.

OOS and protected holdout remain CLOSED until separately authorized by earlier gates.

## Boundary

This freeze defines predictor states only.

It does not open:
- future d;
- convergence outcomes;
- returns;
- PnL;
- execution;
- live trading.

Promotion credit = 0.
