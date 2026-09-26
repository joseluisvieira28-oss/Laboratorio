# RETH-NAV-DISLOCATION-001 — DISCOVERY PREDICTOR SAMPLE GATE FREEZE V0.1

Frozen: 2026-09-26
Parent: PRE_OUTCOME_STATE_AND_PARTITION_FREEZE_V0.1
Freeze timing: BEFORE calibration quantile values and BEFORE all Discovery outcomes.

## Purpose

After and only after:
1. PREDICTOR_SOURCE_CENSUS_PASS (556/556), and
2. PREDICTOR_STATE_CALIBRATION_PASS,

construct predictor states in the already-frozen Discovery region and determine whether the frozen mechanism test has enough events to be scientifically admissible.

This stage opens NO future outcome.

## Frozen Discovery predictor grid

Entry-state blocks:
N_k = 24,000,000 + 7,200 * k

for every integer k such that:
24,000,000 <= N_k < 25,000,000.

Expected count:
139 predictor-state blocks.

No substitute block or date is allowed.

## Fixed source

Use exactly:
- rETH protocol source from prior freezes;
- Uniswap V3 rETH/WETH fee-100 pool;
- block-pinned getExchangeRate, getTotalCollateral, slot0, liquidity;
- exact signed dislocation formula.

100% of the 139 state blocks must be valid.
No imputation or pool switching.

## State application

Use the exact q05 and q95 rational thresholds from:
RETH_STATE_CALIBRATION_RECEIPT_V0.1.json

Classify each valid Discovery block:
- DISCOUNT_EXTREME if d_N <= q05;
- PREMIUM_EXTREME if d_N >= q95;
- NEUTRAL otherwise.

## Frozen event counting

A valid entry event occurs only on transition into an extreme tail:
- current = DISCOUNT_EXTREME and previous grid state != DISCOUNT_EXTREME; or
- current = PREMIUM_EXTREME and previous grid state != PREMIUM_EXTREME.

The first Discovery grid point may count as an entry only if it is extreme because the immediately prior state belongs to the calibration region and must be checked at block 23,992,800 using the same source and frozen thresholds.

This boundary predecessor is evidence-only and is not a Discovery observation.

No cool-down, spacing, or de-clustering parameter may be changed after outcomes.

## Predictor sample gate

DISCOVERY_PREDICTOR_SAMPLE_PASS requires:
- 139/139 Discovery predictor states valid;
- boundary predecessor valid;
- total transition-entry events >= 30;
- DISCOUNT_EXTREME entries >= 10;
- PREMIUM_EXTREME entries >= 10;
- zero source errors / latest fallback.

If source coverage fails:
DISCOVERY_PREDICTOR_SOURCE_BLOCKED.

If source passes but sample minimum fails:
DISCOVERY_PREDICTOR_INSUFFICIENT_SAMPLE.

Neither classification opens outcomes.

Only DISCOVERY_PREDICTOR_SAMPLE_PASS may permit the separately frozen +7,200-block mechanism outcome to be constructed.

## Outcome firewall

This gate opens no:
- future d values;
- future returns;
- direction PnL;
- fees/slippage;
- OOS;
- protected holdout;
- live trading.

Promotion credit = 0.
