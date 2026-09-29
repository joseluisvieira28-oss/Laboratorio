# DEFI-LIQUIDATION-SHOCK-001 — BASIS DISLOCATION V0.1 TERMINAL CLOSEOUT

Date: 2026-09-29
Branch: dls-basis-dislocation-v01
Family ID: DLS-BASIS-DISLOCATION-001

## Terminal classification

DLS_BASIS_DEVELOPMENT_NO_EDGE

The frozen liquidation-shock -> perp/spot convergence hypothesis does not survive development after the
pre-frozen two-leg taker execution model.

2023 OOS MUST remain unopened.
2024 holdout MUST remain unopened.

## Freeze authority

DLS_BASIS_DISLOCATION_V0_1_DEVELOPMENT_FREEZE_2026-09-29.md

Freeze commit:
5ff78a86339c8c15e7766fd78f0b2391d8b2bb46

Canonical development run:
36545904900

Canonical artifact:
- name: dls-basis-dislocation-development-v01
- artifact ID: 11021903865
- digest: sha256:c1fec2e4b58f7a367abfda45e4d782a1773e369475cfa259f7f1bafb181fc307

## Source integrity

Canonical liquidation cluster authority:
- run 36465385517
- artifact ID 10988887983
- SOURCE_SAMPLE_GATE_PASS

Frozen SOL-primary development clusters:
2,968

Market data:
- Binance Spot SOLUSDT 1m
- Binance USDT-M Futures SOLUSDT 1m
- 390 UTC days x 2 legs = 780 daily archives
- archive PASS: 780 / 780
- missing minutes: 0
- hard source errors: 0

## Frozen rule

- no signed-flow labels
- 60 complete pre-entry minutes of log(perp_open / spot_open)
- z threshold = +/-2.0
- z >= +2 => SHORT perp / LONG spot
- z <= -2 => LONG perp / SHORT spot
- entry = first full UTC minute after source t0
- hold = 15 minutes
- one pair maximum
- funding-boundary candidates excluded
- spot taker fee = 10 bps/side
- futures taker fee = 8 bps/side
- adverse slippage = 5 bps/side on each leg
- equal gross notional, 0.5 portfolio weight per leg
- nominal modeled portfolio round-trip cost = 28 bps

## Population

Canonical SOL-primary clusters:
2,968

Adjudication:
- below z threshold: 2,272
- collision ignored: 393
- funding-boundary excluded: 104
- analyzable trades: 199

Temporal folds:
- F1: 194 trades
- F2: 5 trades

The extreme F1/F2 trade-count imbalance is itself evidence that the frozen trigger was not temporally
stable enough to satisfy the pre-frozen gate.

## Net result

Overall:
- n = 199
- mean net = -0.002547223042844725 = -25.4722 bps/trade
- median net = -0.002578527474751357 = -25.7853 bps/trade
- win rate = 0.005025125628140704 = 0.5025%
- profit factor = 0.002483478466979237
- cumulative simple net return = -0.5068973855261003

F1:
- n = 194
- mean net = -0.002547136484867614
- median net = -0.0025850631323587323
- profit factor = 0.002547408940821919

F2:
- n = 5
- mean net = -0.002550581492356638
- median net = -0.002546017038996774
- profit factor = 0.0

UTC-day block-bootstrap 95% CI for mean net:
[-0.0025935271299640183, -0.0025037837707497204]

The entire interval is negative.

## Gross-effect audit

A post-run closeout audit recomputed the equal-weight relative-value return from the canonical ledger's
raw spot/futures OPEN prices before the frozen fee/slippage model.

Descriptive gross result:
- mean gross convergence return ~= +0.0002529444670788023 = +2.5294 bps/trade
- median gross convergence return ~= +0.00022615315280238857 = +2.2615 bps/trade

This is descriptive only and does not create a rescue path.

The gross effect is roughly an order of magnitude smaller than the frozen ~28 bps portfolio round-trip
execution cost, explaining the strongly negative net result.

## Gate adjudication

PASS:
- total n >= 100

FAIL:
- overall mean > 0
- overall median > 0
- PF > 1.05
- F2 n >= 30
- F1 mean > 0
- F2 mean > 0
- bootstrap lower > 0

Therefore:

DLS_BASIS_DEVELOPMENT_NO_EDGE

## Terminal guardrail

Forbidden as a rescue of this family:
- lower the frozen costs;
- choose maker fees after seeing this result;
- lower/raise z from 2.0;
- grid-search z;
- change the 15-minute hold;
- select only F1;
- select only a protocol;
- use liquidation event count/size filters after seeing PnL;
- open 2023 OOS;
- open 2024 holdout.

A passive-maker execution thesis would require a NEW execution family with its own pre-outcome fill,
queue, adverse-selection and cancellation model. It is not authorized by this closeout.

## What remains scientifically useful

The canonical ledger suggests a small gross basis-convergence effect after liquidation shocks, but its
magnitude is not economically executable under the frozen taker model.

This family therefore contributes a useful negative result:
relative-value basis convergence is present descriptively but too small/unstable to support this
execution rule.

## Firewall

market_2023_oos_opened=false
market_2024_holdout_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
