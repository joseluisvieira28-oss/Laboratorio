# ETH-BLOCKSPACE-DEMAND-001 — DISCOVERY IMPLEMENTATION BINDING V0.1A

Date: 2026-09-19
Status: **FROZEN PRE-MARKET-OUTCOME / NON-DISCRETIONARY IMPLEMENTATION BINDING**

Parent protocol:
`ETH_BLOCKSPACE_DEMAND_001_FINAL_PRE_DISCOVERY_PROTOCOL_V0_1.md`
commit: `5b6e3c3d3204aa192ff3eac5f8cb78a303d5db42`

No ETHUSDT market archive was accessed before this binding.

## Percentile implementation

The frozen phrase “prior-90 empirical 80th percentile” is bound to the exact source-only census implementation used before the protocol was frozen:

1. sort the 90 prior values ascending;
2. position = `(n - 1) * 0.80`;
3. linearly interpolate between floor(position) and ceil(position);
4. current source day is excluded from the 90-day reference window.

This definition reproduces the pre-market frozen census exactly:
- Discovery signal dates 2022-01-01 through 2023-12-29: **112**
- Discovery signal-date list SHA-256, newline-delimited UTC dates: **b655923a78696538decbeb261734c003d868704c7ac3e7dd3017d5c8734100db**
- 2024 source-only holdout signal dates: **43**
- 2024 source-only holdout signal-date list SHA-256: **241807d84dca3826dfba5d77d3f0b51f63ce88d3a8c34a1f2d7352b2af277191**

The 2024 signal census contains no market outcomes and remains outcome-locked.

## Bootstrap implementation

UTC calendar-week block bootstrap:
- event grouping key = ISO calendar `(year, week)` of **entry UTC date**;
- sample the observed event-bearing week keys with replacement, drawing exactly the same number of week keys as observed;
- concatenate all events belonging to each sampled week occurrence;
- statistic = mean BASE net bps;
- 10,000 repetitions;
- Python deterministic PRNG seed 20260919;
- lower/upper 95% = linear interpolation empirical 2.5th / 97.5th percentiles;
- one-sided support p = `(count(draw_mean <= 0) + 1) / (10000 + 1)`.

## Profit factor

`PF = sum(positive net bps) / abs(sum(negative net bps))`.

## Max additive drawdown

Sort events chronologically by entry UTC date.
Cumulative equity is additive BASE net bps.
Max drawdown is the most negative `equity - prior_running_peak`.

No scientific gate, threshold, cost, direction, horizon, asset, window or holdout boundary is changed by this binding.
