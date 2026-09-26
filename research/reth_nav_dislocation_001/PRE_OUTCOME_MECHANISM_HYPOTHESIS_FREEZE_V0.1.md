# RETH-NAV-DISLOCATION-001 — PRE-OUTCOME MECHANISM HYPOTHESIS FREEZE V0.1

Frozen: 2026-09-26
Parent: PRE_OUTCOME_STATE_AND_PARTITION_FREEZE_V0.1
Freeze timing: BEFORE completed predictor-census quantiles and BEFORE any future outcome series is opened.
Stage: MECHANISM TEST DESIGN ONLY.

## Economic hypothesis

If the rETH/WETH market price enters an extreme discount or premium relative to Rocket Pool's protocol exchange-rate anchor, the signed market/NAV dislocation should subsequently move toward zero.

This is a convergence hypothesis, not yet a PnL hypothesis.

## Frozen event direction

For an entry event at block N with signed dislocation d_N:

- DISCOUNT_EXTREME (d_N <= q05): expected convergence is an INCREASE in d toward zero.
- PREMIUM_EXTREME (d_N >= q95): expected convergence is a DECREASE in d toward zero.

Both tails are mandatory. Neither tail may be dropped because its outcomes are weaker.

## Frozen primary horizon

Primary horizon:
N + 7,200 Ethereum blocks.

This matches the already-frozen predictor census cadence and is an operational approximately-one-day mechanism horizon.

No alternative primary horizon may replace it after outcomes are opened.

Secondary diagnostic horizon:
N + 21,600 blocks.

The secondary horizon is descriptive only and may not rescue a failed primary result.

## Frozen primary outcome

Let:

delta_d_7200 = d_(N+7200) - d_N

signed_closure_7200 =
- for DISCOUNT_EXTREME: +delta_d_7200
- for PREMIUM_EXTREME: -delta_d_7200

Positive signed_closure means movement toward the protocol anchor.

Also retain:

closure_fraction_7200 = signed_closure_7200 / abs(d_N)

when d_N != 0.

No price/PnL transformation is primary in this mechanism test.

## Event construction

Use only events created by the previously frozen state-transition/de-clustering rule.

An event is valid only if:
- entry predictor state is source-valid;
- future predictor state at the exact N+7,200 block is source-valid;
- same frozen fee-100 pool and rETH protocol source are used;
- no nearest-date or nearest-block substitution occurs.

Invalid outcomes are not imputed.

## Discovery region

Discovery entry blocks:
24,000,000 <= N < 25,000,000.

No entry outside this region contributes to the Discovery verdict.

OOS and protected holdout remain sealed during Discovery.

## Frozen minimum sample

Discovery is INSUFFICIENT_SAMPLE unless:
- total valid extreme-entry events >= 30;
- DISCOUNT_EXTREME valid events >= 10;
- PREMIUM_EXTREME valid events >= 10.

No sample-count rescue by changing quantiles is permitted.

## Frozen primary statistical gate

If sample minimum passes, compute across all valid Discovery events:

1. mean signed_closure_7200;
2. 10,000 deterministic bootstrap resamples of event rows, seed = 20260926;
3. percentile 95% confidence interval of the mean;
4. separate mean signed_closure_7200 for discount and premium tails.

MECHANISM_DISCOVERY_PASS requires ALL:
- pooled mean signed_closure_7200 > 0;
- bootstrap 95% lower bound > 0;
- discount-tail mean > 0;
- premium-tail mean > 0.

Otherwise:
MECHANISM_DISCOVERY_FAIL.

The 21,600-block diagnostic cannot alter this verdict.

## OOS / holdout firewall

Only MECHANISM_DISCOVERY_PASS may authorize a separate OOS opening document.

OOS:
25,000,000 <= N < 26,000,000.

Protected holdout:
N >= 26,000,000.

Protected holdout remains closed until a separately frozen OOS gate passes.

## Trading firewall

Even MECHANISM_DISCOVERY_PASS is NOT trading edge.

This stage does not open:
- trade returns;
- execution direction as a real order;
- fee/slippage model;
- PnL;
- position sizing;
- live trading.

A later executable-economics freeze would be required before any PnL test.
