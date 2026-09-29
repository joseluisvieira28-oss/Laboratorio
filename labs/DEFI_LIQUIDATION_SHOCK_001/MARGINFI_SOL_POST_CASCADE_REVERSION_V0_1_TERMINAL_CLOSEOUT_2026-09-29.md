# MARGINFI SOL POST-CASCADE TRANSIENT REVERSION V0.1 — TERMINAL DEVELOPMENT CLOSEOUT

Date: 2026-09-29
Branch: dls-marginfi-transient-reversion-v01

Frozen family:
DLS-MARGINFI-SOL-POST-CASCADE-REVERSION-001

Frozen hypothesis:
After a source-proven Marginfi native-SOL collateral sell cascade ends, SOL rebounds sufficiently over
the next 15 minutes to survive realistic automated execution costs.

Development freeze:
MARGINFI_SOL_POST_CASCADE_REVERSION_V0_1_DEVELOPMENT_FREEZE_2026-09-29.md

Canonical source authority:
MARGINFI_SOL_FEBMAR_SIGNED_FLOW_SOURCE_PASS
run 36589912203 attempt 2
artifact ID 11053637340
digest sha256:8100803148ead42807322446fcbf9f7c678b6a6589e0c4509f4ddcf930afab3d

Canonical Development run:
36612235487

Canonical Development artifact:
dls-marginfi-sol-post-cascade-reversion-development-v06-win
artifact ID 11054255647
digest sha256:de45248efeab8c94214b5f2b067d8e092198170e8b476a9e924efa4732ce62b5

Terminal classification:
MARGINFI_SOL_REVERSION_DEVELOPMENT_NO_EDGE

## Source population

Eligible source-proven SOL sell events:
1,360

Frozen 5-minute source-only cascade construction:
203 cascades

Operational execution:
- 154 analyzable trades
- 40 later cascade candidates ignored due open-position collision
- 9 candidates excluded for crossing a funding timestamp
- 34 distinct UTC entry days

## Market-data integrity

Authority:
Binance public USDT-M SOLUSDT perpetual 1-minute daily archives

Required days:
35

Checksum/integrity PASS:
35 / 35

Missing minutes:
0

Hard errors:
0

## Gross result before fees/slippage

n = 154
mean = -0.00036095817372750204
median = -0.00009876590225710302
win rate = 0.4805194805194805
profit factor = 0.8553240859959431
cumulative simple return = -0.055587558754035316

The frozen post-cascade LONG mean-reversion hypothesis is negative even before modeled execution costs.
This is not a fee-driven death.

## Nominal net result

Frozen primary execution model:
- MEXC API taker fee: 8 bps per side
- slippage: 2 bps per side
- approximately 20 bps round trip

n = 154
mean = -0.0023601252482574006
median = -0.002098247502656747
win rate = 0.2922077922077922
profit factor = 0.3634769948472223
cumulative simple return = -0.3634592882316397

## Stress result

Approximately 26 bps round trip:

mean = -0.00295900956770096
median = -0.0026972889016395785
win rate = 0.2532467532467532
profit factor = 0.2866222588397817
cumulative simple return = -0.45568747342594784

## Temporal folds

F1 — February:
n = 91
mean = -0.001858510097591382
median = -0.0021884310434281485
profit factor = 0.4115069678925347
win rate = 0.2967032967032967
cumulative = -0.16912441888081578

F2 — March:
n = 63
mean = -0.0030846804658860943
median = -0.00204615877477102
profit factor = 0.31480962739928814
win rate = 0.2857142857142857
cumulative = -0.19433486935082395

Both independently frozen temporal folds are negative.

## Day-block bootstrap

20,000 replicates
34 UTC day blocks
seed 26092915

95% CI:
lower = -0.003528260490963206
upper = -0.0010499400209668798

The entire bootstrap interval is negative.

## Gate adjudication

PASS:
- n >= 30
- distinct UTC days >= 8
- F1 n >= 10
- F2 n >= 10

FAIL:
- overall nominal mean > 0
- overall nominal median > 0
- nominal PF > 1.10
- F1 nominal mean > 0
- F2 nominal mean > 0
- bootstrap lower > 0

## Terminal consequence

V0.1 post-cascade transient reversion is closed as NO_EDGE.

Apr-Jun 2024 MUST remain unopened for this family.
2025 and 2026 market outcomes MUST remain unopened.

Forbidden rescue:
- changing LONG to SHORT after seeing outcomes;
- changing the 5-minute cascade linkage;
- changing the 15-minute hold;
- selecting only large cascades;
- selecting event-count thresholds;
- selecting liability mint;
- selecting hop count;
- filtering losing hours/days;
- optimizing entry delay or exit horizon;
- changing execution costs;
- using January 2024 as validation;
- opening Apr-Jun as a rescue holdout.

Any materially different hypothesis requires a new pre-outcome family and an untouched validation period.

## Operational history

Run 36611871210 was SOURCE_BLOCKED before market data because the broad-source V0.1 executor was
incorrectly bound to the SOL-only source artifact filenames.

Run 36612031985 inherited the same incorrect binding and was superseded before scientific adjudication.

Run 36612235487 used the corrected pre-outcome SOL-only binding and is canonical.

## Firewall

apr_jun_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
