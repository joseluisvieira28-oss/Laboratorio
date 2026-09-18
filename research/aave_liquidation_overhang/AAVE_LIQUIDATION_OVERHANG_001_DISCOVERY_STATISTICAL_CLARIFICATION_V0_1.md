# AAVE-LIQUIDATION-OVERHANG-001 — DISCOVERY STATISTICAL CLARIFICATION V0.1

Status: **FROZEN BEFORE 2023 OUTCOMES**
Date: **2026-09-18**

This clarification resolves implementation details left implicit by the already
frozen FINAL_PRE_DISCOVERY_PROTOCOL V0.1. It changes no hypothesis, sample,
stress, outcome, horizon, statistic or pass gate.

## Spearman implementation

Because `log1p(x)` is strictly monotone for all non-negative predictor/outcome
values, Spearman ranks are computed from the exact non-negative integer
notionals before the floating-point log transform. This is mathematically
identical to ranking `log1p(x)` while avoiding artificial floating-point tie
creation for very large integers.

Average ranks are used for exact ties.

## Bootstrap undefined resamples

The stationary bootstrap still executes exactly 10,000 resamples.

If a resample has zero variance in X or Y and Spearman rho is undefined, that
resample is conservatively assigned rho = -1.0 for the lower-bound distribution.
It is not silently discarded or replaced.

The receipt records the count of such resamples.

## Empirical lower 95% bound

The one-sided lower 95% bound is the empirical 5th percentile using the
nearest-rank definition:

- sort all 10,000 bootstrap rho values ascending;
- select rank `ceil(0.05 * 10000)`;
- zero-based index = 499.

No interpolation is used.

These rules are frozen before any 2023 liquidation outcome is opened.
