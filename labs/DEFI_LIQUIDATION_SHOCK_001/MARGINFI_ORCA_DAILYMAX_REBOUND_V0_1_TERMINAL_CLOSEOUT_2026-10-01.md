# MARGINFI ORCA DAILY-MAX SHOCK REBOUND V0.1 — TERMINAL DEVELOPMENT CLOSEOUT

Date: 2026-10-01
Branch: dls-marginfi-orca-dailymax-rebound-v01

Family:
DLS-MARGINFI-ORCA-DAILYMAX-REBOUND-001

Frozen hypothesis:
the single largest source-proven Marginfi -> Orca forced-SOL flow shock of each UTC day exhibits an
immediate one-minute LONG exhaustion/rebound.

Pre-outcome freeze:
MARGINFI_ORCA_DAILYMAX_REBOUND_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md

Canonical precheck:
- run 36817661717
- artifact ID 11142440771
- classification MARGINFI_ORCA_DAILYMAX_REBOUND_PREOUTCOME_READY
- selected UTC days 36
- F1 selected 26
- F2 selected 10
- no Jul-Sep OHLC/returns/PnL opened during precheck

Canonical Development run:
36817790608

Canonical Development artifact:
dls-marginfi-orca-dailymax-rebound-development-v01
artifact ID 11141757462
digest sha256:b61bfe1b4eb495a05d342cf0a54b8605fee8468e3ab99146f1ef246465fbdaf3

Terminal classification:
MARGINFI_ORCA_DAILYMAX_REBOUND_DEVELOPMENT_NO_EDGE

## Execution sample

Precheck-selected daily candidates:
36

Funding-boundary exclusions:
1

Analyzable trades:
35

Distinct UTC entry days:
35

F1 Jul-Aug:
n = 26

F2 September:
n = 9

## Gross result before fees/slippage

n = 35
mean = -0.0001150524324691934
median = +0.00020424301776911236
win rate = 0.5428571428571428
profit factor = 0.8602325782818442
cumulative simple return = -0.004026835136421769

Despite a positive median and >50% gross win rate, the mean is negative and PF < 1.
Larger adverse moves dominate the small positive majority.
This is not a fee-driven edge.

## Nominal net

Primary frozen execution model:
- MEXC Futures API taker fee 8 bps per side
- slippage 2 bps per side
- ~20 bps round trip

n = 35
mean = -0.0021145144955459472
median = -0.0017956020721553222
win rate = 0.11428571428571428
profit factor = 0.05465006446896843
cumulative simple return = -0.07400800734410815

## Stress

~26 bps round trip:

mean = -0.0027135461372592225
median = -0.0023948250039548652
win rate = 0.05714285714285714
profit factor = 0.023029811790535547
cumulative simple return = -0.09497411480407279

## Frozen folds

F1 Jul-Aug:
n = 26
mean nominal = -0.0023773857579892895
median = -0.002110828483037212
PF = 0.06473490464222921
win rate = 0.15384615384615385
cumulative = -0.06181202970772153

F2 September:
n = 9
mean nominal = -0.00135510862626518
median = -0.0015994366944258442
PF = 0.0
win rate = 0.0
cumulative = -0.012195977636386619

Both frozen folds are negative.

## Day-block bootstrap

20,000 replicates
35 UTC day blocks
seed 26100104

95% CI:
lower = -0.0029532094493546113
upper = -0.0013860280639651705

The entire nominal bootstrap interval is negative.

## Gate adjudication

PASS:
- n >= 25
- distinct UTC days >= 25
- F1 n >= 15
- F2 n >= 8

FAIL:
- nominal mean > 0
- nominal median > 0
- nominal PF > 1.10
- F1 nominal mean > 0
- F2 nominal mean > 0
- bootstrap lower > 0

## Terminal conclusion

V0.1 closes as NO_EDGE.

This result also closes the immediate one-minute directional-rebound interpretation of the daily-max
Orca liquidation shock under the frozen execution model.

Forbidden rescue:
- stop-loss / take-profit added after seeing these outcomes
- selecting only gross winners
- excluding losing days
- changing hold horizon
- changing side
- filtering by amount, liability, hop count or time
- changing costs
- using 2025 as rescue without separate authorization

## Structural result worth preserving

The most important new source discovery from this research sequence is not a 1-minute trading edge:

Marginfi SOL liquidation execution migrated materially from Jupiter to Orca Whirlpools in 2024.

Full source authority:
- Jul-Sep Orca direction-proven: 7,717
- Oct-Dec Orca direction-proven: 2,263
- Jul-Sep Orca source completeness: 100%
- Oct-Dec Orca source completeness: 100%

This establishes Orca as a dominant historical external execution route for Marginfi SOL liquidations
during the migration regime and materially expands source-proven liquidation-flow coverage.

No live-trading conclusion follows from this source result.

## Firewall

market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
