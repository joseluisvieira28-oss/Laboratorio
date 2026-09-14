# OPTIONS-EXPIRY-REVERSAL-001 — PRE-OUTCOME EXECUTION SEMANTICS V0.1

STATUS: **FROZEN BEFORE ANY BTC 1-MINUTE OUTCOME ACCESS**

LAB: `OPTIONS-EXPIRY-REVERSAL-001`  
MVE: `OER-BTC-EXPIRY-INTENSITY-30M-001`

This document resolves implementation details left implicit in `FROZEN_PRE_SOURCE_PROTOCOL_V0.1.md`. It does not change the hypothesis, source classifier, clocks, horizon, costs, bootstrap count, promotion criteria, or protected period.

## Exact BTC point-price semantics

Outcome source remains official Binance BTCUSDT Spot 1-minute archive only.

For each source-evaluable UTC date `d`, point prices are the **open price of the Binance one-minute candle whose open timestamp equals the named clock time exactly**:

- `P_0730` = open of the `07:30:00` UTC candle;
- `P_0800` = open of the `08:00:00` UTC candle;
- `P_0801` = open of the `08:01:00` UTC candle;
- `P_0831` = open of the `08:31:00` UTC candle.

Frozen returns:

- `r_pre = P_0800 / P_0730 - 1`;
- `r_post = P_0831 / P_0801 - 1`.

This preserves the already-frozen one-minute post-settlement execution buffer. No nearest-bar, interpolation, forward fill, backward fill, close-price substitution, VWAP substitution, alternative exchange, or timing rescue is authorized. A missing required exact minute is fail-closed `DATA_FAILURE` for the Discovery run.

## Frozen regression design matrix

OLS design:

`r_post = alpha + beta_pre*r_pre + beta_high*HIGH + beta_int*(r_pre*HIGH) + weekday FE + year FE + error`

Coding is frozen as:

- intercept included;
- weekday fixed effects: Tuesday through Sunday dummies, Monday baseline;
- year fixed effects: 2022, 2023, 2024 dummies, 2021 baseline;
- `HIGH` is exactly the source-gate `high_expiry_pressure` field;
- primary coefficient is `beta_int`.

No scaling, winsorization, standardization, clipping, robust regression, nonlinear transform, outlier removal, or extra covariate is authorized.

## Frozen moving-block bootstrap

- block length: 7 consecutive calendar-date rows;
- replications: 20,000;
- RNG seed: `20260914`;
- moving-block candidate starts: every row index for which a full 7-row block exists;
- each replicate samples candidate 7-row blocks with replacement until at least `N` rows are accumulated, then truncates to exactly `N`;
- the same OLS design is refit on each replicate;
- rank-deficient bootstrap replicates are fail-closed technical failures, not silently discarded.

Frozen one-sided bootstrap p-value for `H1: beta_int < 0`:

`p = (1 + count(beta_int_bootstrap >= 0)) / (B + 1)`.

No alternative bootstrap, HAC rescue, parametric p-value rescue, alternative block length, alternate seed, or multiple-testing search is authorized.

## Frozen companion economics

On `HIGH_EXPIRY_PRESSURE == 1` dates only:

- `r_pre > 0` -> short at `P_0801`, exit `P_0831`;
- `r_pre < 0` -> long at `P_0801`, exit `P_0831`;
- `r_pre == 0` -> no trade.

For each executed trade:

- gross return = `-sign(r_pre) * r_post`;
- gross bps = gross return × 10,000;
- NET10 bps = gross bps − 10;
- NET14 bps = gross bps − 14.

Profit factor NET14 = sum of positive NET14 bps / absolute sum of negative NET14 bps. If there are no losses it is `+inf`; if there are no gains it is `0`.

Cumulative NET14 return and max drawdown use multiplicative trade equity in chronological order with per-trade net return `gross_return - 0.0014`. No overlapping position exists because each trade lasts 30 minutes and there is at most one trade per UTC date.

Calendar partitions are 2021 partial, 2022, 2023, 2024. The frozen concentration gate uses each partition's **positive gross PnL contribution** divided by total positive gross PnL across partitions; if total positive gross PnL is zero, the concentration gate fails.

## Data protections

The Discovery implementation must construct/download only Binance BTCUSDT 1-minute files whose covered timestamps lie between 2021-05-02 00:00:00 UTC and 2024-12-31 23:59:59.999 UTC.

- no 2025;
- no 2026;
- no live API price endpoint;
- no live trading;
- no exchange mutation;
- no order creation;
- no alerts/webhooks;
- no post-outcome tuning.
