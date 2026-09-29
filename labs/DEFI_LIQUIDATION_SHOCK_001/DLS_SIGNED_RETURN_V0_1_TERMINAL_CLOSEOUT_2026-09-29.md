# DEFI-LIQUIDATION-SHOCK-001 — SIGNED RETURN V0.1 TERMINAL CLOSEOUT

Date: 2026-09-29
Branch: dls-signed-return-v01

## Terminal classification

SIGNED_RETURN_DEVELOPMENT_NO_EDGE

This is terminal for the frozen DLS Signed Return V0.1 hypothesis:
- Drift liquidate_perp
- marketIndex 0 = SOL-PERP
- SIGNED_BUY_PRESSURE_PROVEN => LONG
- SIGNED_SELL_PRESSURE_PROVEN => SHORT
- next-minute entry
- 5-minute hold
- one position maximum
- primary cost = 8 bps taker fee + 5 bps adverse slippage per side

Per the pre-outcome freeze, OOS and holdout MUST NOT be opened after this development failure.

## Freeze authority

DLS_SIGNED_RETURN_V0_1_DEVELOPMENT_FREEZE_2026-09-29.md

Freeze commit:
325b76ab55e9308e223837d3e3760769efa1a220

No signed-return market outcome had been opened before this freeze.

## Operational correction history

Initial workflow run:
36544378055

It failed before market-data acquisition because the executor parsed the canonical source receipt field
`family` as an object even though the canonical receipt stores the string
`drift/liquidate_perp`.

This was a plumbing-only parser defect.

Correction commit:
9c1f75c96403c15e80982cf832c39e361bc4f28c

No scientific rule, population rule, signal mapping, horizon, cost, gate or outcome boundary changed.

Canonical development workflow run:
36544549596

Workflow conclusion:
SUCCESS

Canonical artifact:
- name: dls-signed-return-development-v01
- artifact ID: 11021507139
- digest: sha256:ee543a715831ff6339d2e0382c6e6d2805c4015801c4f27f9575a77571b07ffa

## Source integrity

Binance USDT-M SOLUSDT daily 1-minute archives:
- archive days checked: 31
- archive days PASS: 31
- missing minutes: 0
- hard source errors: 0

Canonical signed-flow source:
- run 36525438771
- artifact ID 11014134904
- classification DRIFT_LIQUIDATE_PERP_SIGNED_FLOW_AUTHORIZED

Execution source gate:
V02_EXECUTION_SOURCE_PASS

## Frozen signal population

Drift marketIndex 0 candidate rows:
1,933

Source adjudication:
- proven BUY rows: 1,407
- proven SELL rows: 22
- proven-not-realized rows: 483
- source-incomplete rows: 21

Minute aggregation:
- source-incomplete minutes excluded: 4
- signed signal minutes: 102
- LONG signal minutes: 101
- SHORT signal minutes: 1

Execution overlap/funding:
- ignored while prior position open: 52
- funding-boundary excluded: 1
- analyzable non-overlapping trades: 49

No amount threshold or direction-side filter was introduced.

## Primary 26 bps nominal round-trip result

Trades:
49

Mean net return:
0.00033943811118439086
= +0.0339438111%

Median net return:
-0.004791699110382715
= -0.4791699110%

Win rate:
0.3673469387755102
= 36.7347%

Profit factor:
1.05203495734688

Cumulative simple net return:
0.016632467448035152

Frozen day-block bootstrap:
- UTC-day blocks: 12
- replicates: 10,000
- seed: 260929
- 95% CI lower: -0.011026003870910558
- 95% CI upper: 0.007386411161598397

## Gate adjudication

Required:
1. n >= 30
2. mean net return > 0
3. profit factor > 1.05
4. day-block bootstrap 95% CI lower bound > 0

Observed:
- n >= 30: PASS
- mean net > 0: PASS
- PF > 1.05: PASS
- bootstrap lower > 0: FAIL

Therefore:

SIGNED_RETURN_DEVELOPMENT_NO_EDGE

The positive point estimate is not sufficiently robust under the pre-frozen dependence-aware uncertainty gate.

## Cost sensitivity — descriptive only

2 bps slippage per side:
- mean +0.0009402373171719118
- PF 1.1528532163919054

5 bps slippage per side — PRIMARY:
- mean +0.00033943811118439086
- PF 1.05203495734688

10 bps slippage per side:
- mean -0.0006611262002070775
- PF 0.9078598644353574

Sensitivity cannot select or rescue the primary rule.

## Terminal guardrail

Forbidden as a rescue of this family:
- open the pre-frozen OOS window 2023-02-01 through 2023-03-31;
- open the 2024 holdout;
- switch to BUY-only because January contained mostly BUY pressure;
- remove or reduce the frozen 26 bps primary cost;
- choose 2 bps sensitivity as primary;
- change the 5-minute horizon;
- test 15/30/60-minute horizons as a continuation of V0.1;
- reverse BUY/SELL mapping;
- add magnitude thresholds;
- alter minute aggregation;
- alter overlap handling;
- select another Drift market based on this result.

Any materially different signed-flow hypothesis requires:
- a new family ID;
- a new pre-outcome freeze;
- a scientifically distinct rationale not derived from rescuing this result.

## What remains valid

The upstream source result remains valid:
Drift January-2023 liquidate_perp signed-flow source authority = PASS.

This closeout rejects only the frozen 5-minute executable continuation hypothesis after costs and uncertainty.

It does not invalidate:
- the V0.1 absolute-volatility result;
- the protocol-native signed-flow semantics;
- independent source-authority work for other protocols/classes.

## Firewall

oos_outcomes_opened=false
holdout_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
