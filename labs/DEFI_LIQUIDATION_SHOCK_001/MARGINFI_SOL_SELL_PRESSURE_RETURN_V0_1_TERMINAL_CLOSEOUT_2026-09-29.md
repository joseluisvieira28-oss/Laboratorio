# MARGINFI SOL SELL-PRESSURE RETURN V0.1 — TERMINAL DEVELOPMENT CLOSEOUT

Date: 2026-09-29
Branch: dls-marginfi-signed-return-v01

Frozen hypothesis:
source-proven Marginfi native-SOL collateral selling through Jupiter -> 5-minute short SOLUSDT continuation.

Freeze commit:
d138b6d63d43e032bd5520fd4668d7461c38d963

Canonical run:
36563889195

Artifact:
dls-marginfi-sol-sell-pressure-development-v01
artifact ID 11030374236
digest sha256:1781a8e247d9226c157989c038a7d3ce91597e77f2f13c3e7453807c9a013a41

Terminal classification:
MARGINFI_SOL_SELL_PRESSURE_DEVELOPMENT_NO_EDGE

## Population and execution

Eligible source-proven native-SOL collateral sell events:
591

Operational frozen overlap handling:
- 533 later events ignored while an existing 5-minute position was open;
- 1 trade excluded for crossing a funding timestamp;
- 57 non-overlapping analyzable trades;
- 10 distinct UTC entry days.

Primary cost model:
- 8 bps MEXC API taker fee per side;
- 2 bps slippage per side;
- approximately 20 bps modeled round trip.

Stress:
approximately 26 bps round trip.

## Gross result before fees/slippage

n = 57
mean = -0.0003322657679767029
median = +0.000540519291625019
win_rate = 0.5263157894736842
profit_factor = 0.802063965413667
cumulative_simple_return = -0.018939148774672065

The frozen short-continuation hypothesis therefore has negative mean and PF < 1 even before modeled execution costs.
This is not a fee-driven death.

## Nominal net result

n = 57
mean = -0.002333064699847159
median = -0.0014592319489901335
win_rate = 0.2807017543859649
profit_factor = 0.17510242574122636
cumulative_simple_return = -0.13298468789128806

## Stress result

mean = -0.002934164928845713
median = -0.0020598077209486583
win_rate = 0.19298245614035087
profit_factor = 0.10817428931245691
cumulative_simple_return = -0.16724740094420565

## Temporal robustness

F1:
n = 13
mean nominal net = -0.001070406448730134
median = -0.0011282742959740214
PF = 0.5488036530954308
win_rate = 0.38461538461538464

F2:
n = 44
mean nominal net = -0.002706122819495371
median = -0.00161831312207679
PF = 0.0866999742643788
win_rate = 0.25

Both frozen temporal folds are negative.

## Bootstrap

UTC-day block bootstrap:
- 20,000 replicates
- 10 day blocks
- seed 26092901
- 95% CI lower = -0.0030578113136475247
- 95% CI upper = -0.0013042558133557222

The entire bootstrap interval is negative.

## Gate adjudication

PASS:
- n >= 40
- distinct UTC days >= 5
- F1 n >= 10
- F2 n >= 20

FAIL:
- overall mean > 0
- overall median > 0
- PF > 1.10
- F1 mean > 0
- F2 mean > 0
- bootstrap lower > 0

## Terminal consequence

V0.1 is closed as NO_EDGE.

The frozen Feb-Mar 2024 OOS MUST remain unopened.
The Apr-Jun 2024 holdout MUST remain unopened.
2025/2026 market outcomes MUST remain unopened.

Forbidden rescue includes:
- flipping SHORT to LONG after seeing this result;
- changing the 5-minute horizon;
- selecting only large flows;
- choosing only specific liability mints;
- filtering days/time-of-day/hop count;
- changing costs to manufacture a PASS.

A reversal/mean-reversion thesis, amount-conditioned thesis, different horizon, or different collateral asset is a materially new family and requires a new pre-outcome freeze.

## Firewall

oos_2024_feb_mar_opened=false
holdout_2024_apr_jun_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
