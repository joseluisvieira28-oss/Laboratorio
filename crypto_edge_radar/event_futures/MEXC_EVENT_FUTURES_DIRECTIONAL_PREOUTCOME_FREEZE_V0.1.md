# MEXC EVENT FUTURES — DIRECTIONAL PRE-OUTCOME SCIENCE FREEZE V0.1

Date: 2026-10-02
Status: FROZEN BEFORE BULK DIRECTIONAL OUTCOMES
Mode: RESEARCH ONLY — NO LIVE TRADING — NO EVENT FUTURES ORDERS

## Purpose

Test whether simple, fully pre-specified price-direction signals have reproducible predictive power for the exact MEXC index families used by Event Futures.

This is a DIRECTIONAL PROXY study only. It is NOT a historical Event Futures PnL study because timestamped historical payout-at-entry has not been proven.

## Assets

Canonical public MEXC index symbols established by the source gate:

- BTCUSDT -> BTC_USDT
- ETHUSDT -> ETH_USDT
- NVDAUSDT -> NVIDIA_USDT
- MUUSDT -> MUSTOCK_USDT
- SPCXUSDT -> SPCXSTOCK_USDT

No symbol substitution after outcomes are opened.

## Common historical window

To give all five assets the same calendar regime and avoid asset-specific listing-date optimization:

Warm-up only:
- 2026-06-25 00:00:00 UTC through 2026-07-01 00:00:00 UTC exclusive

Development:
- 2026-07-01 00:00:00 UTC through 2026-08-01 00:00:00 UTC exclusive

OOS validation:
- 2026-08-01 00:00:00 UTC through 2026-09-01 00:00:00 UTC exclusive

Protected final holdout:
- 2026-09-01 00:00:00 UTC through 2026-10-01 00:00:00 UTC exclusive

2026-10-01 and later are CLOSED for this experiment.

The bulk acquisition may fetch the warm-up plus all three frozen partitions in one immutable corpus, but analysis must preserve the partition labels. No rule may be changed after any Development outcomes are read.

## Base data

Primary outcome/source series:
- MEXC public index-price 1-minute klines.
- All higher lookbacks are derived from the same 1-minute close series.
- Entry and expiry are evaluated on exact UTC minute-grid observations.

This is named:
MINUTE_GRID_DIRECTIONAL_PROXY

It is an approximation to the actual Event Futures submission/settlement price process. It must never be described as exact product execution.

## Event settlement horizons

Frozen horizons:
- 10 minutes
- 30 minutes
- 60 minutes
- 1440 minutes (1 day)

Primary entries are non-overlapping UTC grids:

- H=10: minute divisible by 10
- H=30: minute divisible by 30
- H=60: top of each UTC hour
- H=1440: 00:00 UTC

This avoids counting every minute as an independent Event Future for the primary test.

## Chart/lookback horizons

Frozen chart-equivalent trailing returns:
- 1 minute
- 5 minutes
- 15 minutes
- 60 minutes
- 240 minutes
- 1440 minutes

At entry t:

r_L(t) = close(t) / close(t-L) - 1

No future information may enter r_L(t).

## Signal families

Exactly two mirrored families are frozen:

1. MOMENTUM_L
   - predict UP if r_L(t) > 0
   - predict DOWN if r_L(t) < 0
   - no prediction if r_L(t) = 0 or required data are absent

2. REVERSAL_L
   - predict DOWN if r_L(t) > 0
   - predict UP if r_L(t) < 0
   - no prediction if r_L(t) = 0 or required data are absent

No RSI, EMA, MACD, candlestick pattern, threshold, volatility filter, session filter, news filter, or parameter search is allowed in V0.1.

Those require a new prospective freeze after V0.1 closes.

## Target

For settlement horizon H:

- UP if close(t+H) > close(t)
- DOWN if close(t+H) < close(t)
- TIE if close(t+H) == close(t)

Ties are reported separately and are not counted as wins or losses for directional accuracy.

## Metrics

Per asset × partition × settlement horizon × lookback × signal family:

- eligible predictions
- UP target count
- DOWN target count
- ties
- wins
- losses
- directional accuracy
- Wilson 95% confidence interval
- exact two-sided binomial p-value versus 50%
- mean directional margin in basis points as descriptive only

The primary metric is directional accuracy.

## Multiple testing

The Development screen contains:
5 assets × 4 settlement horizons × 6 lookbacks × 2 signal families = 240 cells.

Development p-values are corrected across the complete 240-cell family with Benjamini-Hochberg FDR q=0.05.

No cell may be promoted based on an uncorrected Development p-value alone.

## Frozen progression rule

A cell becomes DEVELOPMENT_SURVIVOR only if all are true:

- n >= 100 for H in {10,30,60}
- n >= 20 for H=1440
- directional accuracy > 0.50
- BH-FDR-adjusted p <= 0.05

The exact same frozen rule is then evaluated in August OOS without changing polarity/lookback/horizon.

A cell becomes OOS_SURVIVOR only if:

- it was a DEVELOPMENT_SURVIVOR;
- August accuracy > 0.50;
- exact two-sided p <= 0.05;
- sign/polarity remains identical.

Only OOS_SURVIVORS may be opened on the September holdout.

A cell becomes DIRECTIONAL_HOLDOUT_SURVIVOR only if:

- it was an OOS_SURVIVOR;
- September accuracy > 0.50;
- September exact two-sided p <= 0.05;
- no scientific rule changed after Development was opened.

This status is NOT an Event Futures trading authorization.

## Economic sensitivity

Because historical payout-at-entry is NOT proven, only an explicit sensitivity table is allowed.

For payout r, break-even win probability is:

p_break_even = 1 / (1 + r)

Frozen payout sensitivity grid:
- 70%
- 75%
- 80%
- 85%
- 90%

For reference, 80% payout requires 55.555...% wins before any other product-specific friction.

A directional survivor may be tagged:
- ABOVE_80PCT_PAYOUT_BREAKEVEN_POINT_ESTIMATE

only if its point estimate exceeds 55.555...%.

This tag is NOT a claim of historical Event Futures profitability.

## Integrity requirements

- No raw 2026-10 outcomes.
- No change to rules after Development output is produced.
- No selective deletion of losing assets/cells.
- Missing source rows remain missing; no forward-fill across missing minutes.
- Exact source-response/corpus hashes recorded.
- Acquisition errors are BLOCKED, never NO_EDGE.
- Product payout unavailability is PRODUCT_ECONOMICS_NOT_PROVEN, never NO_EDGE.
- Live/order/API execution remains prohibited in this branch.
