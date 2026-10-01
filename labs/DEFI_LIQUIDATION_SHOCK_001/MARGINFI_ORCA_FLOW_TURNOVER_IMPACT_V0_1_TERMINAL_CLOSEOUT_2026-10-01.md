# MARGINFI ORCA FLOW-TO-TURNOVER IMPACT V0.1 — TERMINAL DEVELOPMENT CLOSEOUT

Date: 2026-10-01
Branch: dls-marginfi-orca-flow-turnover-v01

Family:
DLS-MARGINFI-ORCA-FLOW-TURNOVER-IMPACT-001

Frozen hypothesis:
exceptionally large source-proven Marginfi SOL selling through Orca Whirlpools relative to prior-five-minute
SOLUSDT perpetual base turnover -> immediate 1-minute SHORT continuation.

Pre-outcome freeze:
MARGINFI_ORCA_FLOW_TURNOVER_IMPACT_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md

Feature calibration:
- run 36816611039
- artifact ID 11141731925
- digest sha256:a87c854c4ea4f35653f21929c1d9ec302f2e38a6dfc3721fccde6f383ce82a72
- classification MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_PASS
- Q90 = 0.00013563525170134794
- 192 calibration cascades
- 36 distinct cascade-end days
- OHLC/returns/PnL unopened during calibration

Oct-Dec source authority:
- run 36816791726
- artifact ID 11141209600
- digest sha256:38afe35db245dfb0304b4414d250f051941dae9a01af45d430a65a67ba7b9cb1
- classification MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS
- canonical SOL population 2,688
- Orca direction-proven 2,263
- source completeness 100%
- ambiguity 0
- contradictions 0
- duplicates 0

Canonical Development run:
36816994866

Canonical Development artifact:
dls-marginfi-orca-flow-turnover-development-v01
artifact ID 11141553255
digest sha256:75fd4200b8f3313a53bf2816554fd78a0a91892b62c05e3307c8cfe687c8f843

Terminal classification:
MARGINFI_ORCA_FLOW_TURNOVER_DEVELOPMENT_NO_EDGE

## Frozen selection

Eligible source events:
2,263

Frozen cascades:
77

Below Q90:
69

Selected Q90:
8

Analyzable trades:
8

Distinct UTC entry days:
2

All selected trades occurred in F2 / December.
F1 Oct-Nov selected trades = 0.

## Gross before fees/slippage

n = 8
mean = -0.0017623550217594486
median = -0.0020613176896874252
win rate = 0.25
profit factor = 0.19211395734537387
cumulative simple return = -0.014098840174075589

The frozen SHORT continuation hypothesis is negative before modeled execution costs.
This is not a fee-driven death.

## Nominal net

Primary frozen model:
- MEXC Futures API taker fee 8 bps per side
- slippage 2 bps per side
- ~20 bps round trip

n = 8
mean = -0.0037648706328845595
median = -0.004064192175623047
win rate = 0.125
profit factor = 0.015397902821887004
cumulative simple return = -0.030118965063076476

## Stress

~26 bps round trip:

mean = -0.004366830203331358
median = -0.004666331392907487
win rate = 0.0
profit factor = 0.0
cumulative simple return = -0.034934641626650866

## Bootstrap

20,000 UTC-day block replicates
2 entry-day blocks
seed 26100101

95% CI:
lower = -0.005321471209800772
upper = -0.002830910286734832

Entire bootstrap interval is negative.

## Gate adjudication

PASS:
- F2 n >= 8

FAIL:
- n >= 30
- distinct UTC entry days >= 8
- F1 n >= 20
- overall mean > 0
- overall median > 0
- PF > 1.10
- F1 mean > 0
- F2 mean > 0
- bootstrap lower > 0

## Terminal consequence

V0.1 closes as NO_EDGE.

2025 market outcomes remain closed.
2026 remains protected.

Forbidden rescue:
- lowering Q90
- changing SHORT to LONG inside this family
- changing 1-minute hold
- changing turnover denominator
- selecting only December ex post
- adding amount/event/hop/liability/time filters
- changing costs
- opening 2025 as rescue

A LONG exhaustion/rebound hypothesis is a materially new family and may only be tested under a new freeze
against market outcomes that remain unopened.

## Firewall

market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
