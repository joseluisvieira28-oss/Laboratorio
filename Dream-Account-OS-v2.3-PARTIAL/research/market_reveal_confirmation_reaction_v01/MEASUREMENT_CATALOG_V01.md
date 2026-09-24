# MRCR V0.1 — Continuous Measurement Catalog

Status: PRE-TARGET / CONTINUOUS FEATURES ONLY

This catalog defines economically interpretable decision-time measurements. It does not define a future-outcome classifier.

## Measurements

1. Signed aggressive-flow imbalance:
`(buy_notional - sell_notional) / (buy_notional + sell_notional)`

2. Decision-time price displacement:
log mid-price change from a frozen pre-impulse anchor to the decision timestamp, in basis points.

3. Price response per unit flow:
`decision_return_bps / flow_imbalance`

4. Flow/price alignment sign:
+1 aligned, 0 indeterminate, -1 opposed.

5. Retracement fraction, using only the extreme observed by the decision timestamp:
- positive impulse: `(extreme_mid - decision_mid)/(extreme_mid - pre_mid)`
- negative impulse: `(decision_mid - extreme_mid)/(pre_mid - extreme_mid)`

6. Spread state:
- `spread_now / spread_pre_baseline`
- `spread_now / max_spread_observed_to_decision`

7. Depth replenishment state:
`depth_now / depth_pre_baseline`
The exact depth definition must be frozen independently before target capture.

8. Effort-versus-result:
`aggressive_notional / abs(decision_return_bps)`

A large flow with small contemporaneous displacement is consistent with absorption/resiliency, but no cutoff is authorized.

## Required provenance

Each state vector must preserve venue, native symbol, event/impulse identity, anchor timestamp, decision timestamp, timestamp semantics, raw-segment hashes, missingness, and sequence/reconstruction diagnostics where available.

## Explicit boundary

V0.1 defines no future-return horizon, no acceptance/rejection cutoff, no economic score, and no action rule.

Final state: MEASURE FIRST; CLASSIFICATION REMAINS UNDEFINED.
