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

A large flow with small contemporaneous displacement is consistent with absorption/resiliency.

9. Spread-normalized decision displacement:
`abs(decision_return_bps) / pre_spread_bps`
This expresses the observed move in units of the pre-announcement bid-ask spread.

10. Side-specific depth replenishment:
- `bid_depth_now / bid_depth_pre`
- `ask_depth_now / ask_depth_pre`

For a frozen directional state, "resistance-side depth" means ask depth for positive
aggressive-flow direction and bid depth for negative aggressive-flow direction.

No post-target cutoff tuning is authorized.

## Required provenance

Each state vector must preserve venue, native symbol, event/impulse identity, anchor timestamp, decision timestamp, timestamp semantics, raw-segment hashes, missingness, and sequence/reconstruction diagnostics where available.

## H02 transition

Under the separately issued H02_DESIGN_FREEZE authority, a frozen classifier may
reference these continuous measurements. The measurement formulas themselves
remain deterministic and outcome-blind.

Target observation remains separately locked until the final protocol/calendar/
implementation binding and TARGET_OBSERVATION_OPEN authority exist.

Final state: MEASURE FIRST; INTERPRET ONLY THROUGH A PRE-TARGET FROZEN RULE.
