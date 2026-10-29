# Event Futures ATI 3-minute signed-flow historical proxy V0.1 — PRE-OUTCOME FREEZE
29 October 2026 UTC; SOURCE_GATE_PASS established by run 40864318462 BEFORE this model evaluation. Prior source hashes BTC 7926f51d0d6d8cf4b83e735552920972b2b50e8a7fc593ecde4d39bd5666482e and ETH 02aad71a3c78d9d1ae28d5ed185d117cfaa33c5c053cb73dc8d59fd3d1f84a03.

## Fixed causal hypothesis
For BTCUSDT and ETHUSDT, separately, a continuous signed aggressive trade imbalance over the last THREE strictly completed UTC minute bins predicts the same directional sign in MEXC index over 10 or 30 minutes. Freeze ONE sign-only rule: buy notional > sell notional -> UP; less -> DOWN; equal -> ABSTAIN. No thresholds, no logistic fit, no optimization, no conditioning on result, no subset selection. Baseline: ALWAYS UP on same timestamps. Start UTC 2026-04-01 00:20 and stride EXACT expiry horizon per symbol/horizon to avoid overlapping decisions. Missing data skipped with counts and never imputed.

## Explicitly NOT a new independent OOS
April 2026 was already exposed in prior MEXC Event Futures 18-cell index-only Discovery. This diagnostic is post-prior-outcome information, thus exploratory, not a preregistered untouched hypothesis, even though its own concrete code and parameters are frozen before this run. No June/Sept protected data, no live or forward outcomes.

## Payout and price proxy
Index source is public MEXC standard futures index Min5, price OPEN(t) and OPEN(t+H). These are optimistic theoretical proxies; MEXC Event Futures server order openPrice, expiry tick and actual payout are NOT established. Report accuracy and fixed payout sensitivity q=0.40,0.80,0.85 assuming symmetric q and TIE=0, NEVER actual PnL or EV. No price feature from after t is used to choose a prediction.

## Hard boundaries and verdict
Results cannot promote to LIVE, SURVIVES or independently verified edge; if one cell appears positive, DO NOT retune thresholds or choose only winners. Need independently collected features with receive timestamps, new future freeze and protected holdout governance before real shadow. No orders, keys, private APIs, accounts, payments or main merge.
