# MEXC-LAUNCHPOOL-MX-DEMAND-001 — V0.1 AUTHORITATIVE FAMILY CLOSEOUT
Date: 2026-10-07
Status: CLOSED FOR CURRENT SPEC

## Source census
Authoritative complete census:
- workflow: MLMXD V0.1.7 Complete Source Census
- run: 37637471773
- official MEXC public announcements + official article bodies
- frozen calendar: 2024-10-18 through 2026-09-30
- launchpool title rows: 25
- eligible explicit-MX Launchpool events: 18
- independent <=60m clusters: 18
- calendar years represented: >=2
- additional market outcomes opened by census: false

Frozen source minimum required:
- >=20 eligible events
- >=12 independent clusters
- >=2 years

Adjudication:
- events >=20: FAIL (18)
- clusters >=12: PASS (18)
- years >=2: PASS
- source provenance/timestamps: PASS

Source classification:
SOURCE_INSUFFICIENT_SAMPLE

The source gate is not lowered.

## Activation-time pilot
A separate source-bounded pilot was frozen before opening its market outcomes for 14 official events with exact Launchpool activation T0.

Authoritative workflow:
- MLMXD Activation Pilot V0.1.5 UTC8 History Files
- run: 37636852086
- 14/14 analyzable using official MEXC public historical 15m CSV files

Frozen primary:
- MX/USDT relative to BTC/USDT
- entry: first 15m open at/after exact Launchpool activation T0
- exit: exact +24h open
- expected sign: positive

Observed:
- N: 14
- wins: 7
- mean relative 24h log return: -0.0024508339603943716
- median relative 24h log return: -0.0004906813124367256
- positive fraction: 0.50
- one-sided exact sign-test p: 0.604736328125
- bootstrap 90% CI mean: [-0.007553875411941132, 0.0026348590544360375]
- leave-one-out minimum mean: -0.0037869863105163023

Frozen pilot gate:
- N >=10: PASS
- median >0: FAIL
- positive fraction >0.50: FAIL
- sign p <0.10: FAIL
- leave-one-out minimum mean >0: FAIL

Pilot classification:
PILOT_NO_SIGNAL

## Family verdict

MEXC Launchpool is NOT promoted as a trading candidate under the current frozen analogue.

Authoritative state:
SOURCE_INSUFFICIENT_SAMPLE
+
ACTIVATION_TIME_PILOT_NO_SIGNAL
=
NO_PROMOTION_CURRENT_SPEC

Interpretation:
- This is negative evidence against the exact hypothesis:
  explicit MX-staking Launchpool activation -> long MX relative to BTC for 24h.
- It is not a universal proof that every MEXC Launchpool effect is absent.
- The announcement-time source gate itself did not reach its frozen N>=20 requirement.
- No sign inversion, 1h/6h selection, alternate T0, event filtering, reward-size filter or horizon rescue is permitted from the observed pilot.

## Reopen conditions
This exact family may be reopened only by:
1. naturally accumulating enough new eligible events to satisfy the original source minimum without lowering it; or
2. a genuinely economically distinct hypothesis frozen before its outcomes are opened.

Neither condition authorizes rescue of the failed 24h activation-time long-MX pilot.

## Governance
Research-only closeout.
No live trading.
No orders.
No exchange mutation.
No account access.
No wallet.
No spending.
No main merge.
