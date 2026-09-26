# RETH-NAV-DISLOCATION-001 — PRE-OUTCOME STATE AND PARTITION FREEZE V0.1

Frozen: 2026-09-26
Parent: PREDICTOR_ONLY_CENSUS_FREEZE_V0.1
Freeze timing: BEFORE reading the completed 556-point predictor-census distribution or any market-return outcome.
Governance: RESEARCH-ONLY / OUTCOME-BLIND.

## Purpose

Pre-register how predictor states and later scientific partitions will be defined so neither the completed predictor distribution nor future returns can be used to choose a favorable threshold or split.

## Predictor state rule

Use the signed predictor already frozen:

d_N = market_weth_per_reth / nav_weth_per_reth - 1.

The calibration census is the frozen 556-point grid from block 20,000,000 through block 23,996,000 inclusive.

If and only if the predictor census passes 556/556, compute nearest-rank quantiles over all 556 signed d_N values:

- q05 = nearest-rank 5th percentile;
- q95 = nearest-rank 95th percentile.

Freeze both tails symmetrically:

- DISCOUNT_EXTREME when d_N <= q05;
- PREMIUM_EXTREME when d_N >= q95;
- NEUTRAL otherwise.

No sign may be discarded because later outcomes are weak.
No q01/q10/q90/q99 rescue is permitted after outcomes.
No z-score or volatility-normalized threshold may replace the frozen quantile rule for this exact lab.

The quantile values themselves are calibration outputs; the selection rule q05/q95 is frozen before those values are read.

## Event de-clustering

For a future event/outcome experiment, a new extreme event begins only when:
1. the previous census/observation state was not the same extreme state; and
2. the current state satisfies the relevant frozen tail.

Consecutive same-tail extreme observations are one episode and do not create repeated entries.

No post-outcome cool-down optimization is permitted.

## Future outcome partitions

No market return is opened by this freeze.

When a later outcome experiment is explicitly authorized and its horizon/cost definition is frozen, use chronological scientific partitions based on Ethereum block number:

- CALIBRATION / predictor-only: <= 23,996,000. No outcome testing from this region for promotion credit.
- DISCOVERY: blocks >= 24,000,000 and < 25,000,000.
- OOS: blocks >= 25,000,000 and < 26,000,000.
- PROTECTED HOLDOUT: blocks >= 26,000,000.

The protected holdout may not be opened until a separately frozen Discovery/OOS gate authorizes it.

Because current chain state is already above 26,000,000, any historical outcome data in the protected region remains closed despite being technically accessible.

## Direction firewall

This freeze defines state labels only.

It does NOT define:
- long or short direction;
- convergence/reversion payoff sign;
- holding horizon;
- execution venue;
- fee/slippage model;
- PnL.

A separate pre-outcome hypothesis freeze must define those before any market-return series is opened.

## Failure rules

This exact state definition is blocked if:
- predictor census is not 556/556 PASS;
- quantiles cannot be computed deterministically from the exact census row set;
- q05 >= q95;
- any source row used for calibration is invalid or imputed.

## No promotion credit

Predictor census PASS and state freeze earn zero trading-edge promotion credit.
