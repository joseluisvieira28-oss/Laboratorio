# MARGINFI SOL EXCEPTIONAL-FLOW EXHAUSTION / REBOUND V0.1 — TERMINAL DEVELOPMENT CLOSEOUT

Date: 2026-10-01
Branch: dls-marginfi-flow-exhaustion-rebound-v01

Family:
DLS-MARGINFI-SOL-FLOW-EXHAUSTION-REBOUND-001

Freeze:
MARGINFI_SOL_FLOW_EXHAUSTION_REBOUND_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md

Source authority:
- run 36894911218
- artifact 11179284141
- digest sha256:bf7f02ce666df79f78b17d289fc22d1eaa87a3a1022f8ba4ee52022270fef170
- MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_PASS
- 780 direction-proven source-complete eligible SOL sell events

Canonical Development:
- run 36897023928
- artifact 11179553976
- digest sha256:0119316a4bbae75ac6c11edc0d6453c39ac5ee05ade1dca63c645c3e6e448f5f

Terminal classification:
MARGINFI_SOL_EXHAUSTION_REBOUND_DEVELOPMENT_NO_EDGE

Frozen rule:
- flow-turnover Q90 = 1.0307255992127644e-05
- LONG SOLUSDT
- entry first full minute after cascade end
- 1-minute hold
- MEXC frozen primary cost model ~20 bps round trip
- stress ~26 bps round trip

Selection:
- eligible source events: 780
- frozen cascades: 79
- below Q90: 46
- selected Q90: 33
- analyzable trades: 33
- distinct UTC entry days: 8

## Gross before modeled fees/slippage

n = 33
mean = 0.0012435279700426188 = +12.4353 bps/trade
median = 0.00036213617740421533 = +3.6214 bps
win rate = 0.5454545454545454
profit factor = 3.3800796926045704
cumulative simple return = 0.04103642301140642 = +4.1036%

This is materially different from prior dead Marginfi directional families:
the signal is positive before modeled execution cost.

## Frozen nominal net

n = 33
mean = -0.0007575638461936605 = -7.5756 bps/trade
median = -0.0016378983211670737 = -16.3790 bps
win rate = 0.24242424242424243
profit factor = 0.5436813598028772
cumulative = -0.024999606924390797 = -2.5000%

## Stress

mean = -13.5741 bps/trade
PF = 0.3580
cumulative = -4.4795%

## Folds

F1 Jul-Aug:
- n 31
- nominal mean -7.1122 bps
- PF 0.5746

F2 Sep:
- n 2
- nominal mean -14.7594 bps
- F2 minimum sample gate fails

## Day-block bootstrap

20,000 reps
8 day blocks
seed 26100101

95% CI nominal mean:
[-21.3691 bps, +6.6828 bps]

## Gate

PASS:
- n >= 25
- distinct days >= 8
- F1 n >= 15

FAIL:
- nominal mean > 0
- nominal median > 0
- nominal PF > 1.10
- F2 n >= 8
- F1 mean > 0
- F2 mean > 0
- bootstrap lower > 0

## Scientific interpretation

V0.1 is NO_EDGE under its frozen execution-cost model and may not be rescued by retrospectively reducing
fees/slippage on Jul-Sep.

However, unlike prior families, the gross signal is positive:
+12.44 bps mean and gross PF 3.38.

Therefore a separate execution-feasibility investigation is scientifically justified, but it must:
1. establish a venue/account cost model independently of Jul-Sep outcomes;
2. freeze that model before any untouched market period is opened;
3. use a new family / fresh OOS period;
4. preserve the exact source signal, Q90, LONG direction and 1-minute hold if the purpose is pure cost validation.

Jul-Sep cannot be reclassified under a cheaper post-outcome cost assumption.

2025 and 2026 remain protected.

Firewall:
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
