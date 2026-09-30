# MARGINFI SOL FLOW-TO-TURNOVER IMPACT V0.1 — TERMINAL DEVELOPMENT CLOSEOUT

Date: 2026-09-30
Branch: dls-marginfi-flow-turnover-impact-v01

Family:
DLS-MARGINFI-SOL-FLOW-TURNOVER-IMPACT-001

Frozen hypothesis:
Exceptionally large source-proven Marginfi forced SOL selling relative to prior-five-minute SOLUSDT
perpetual base turnover produces an immediate 1-minute continuation effect.

Pre-outcome freeze:
MARGINFI_SOL_FLOW_TURNOVER_IMPACT_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md

Feature calibration:
- run 36686002313
- artifact ID 11083738178
- digest sha256:6cacadfffce7225984258a634d0df0ac5685c0a7915bedc9e0a0e595fabc1327
- classification MARGINFI_SOL_FLOW_TURNOVER_CALIBRATION_PASS
- N = 203 source-only calibration cascades
- 34 distinct cascade-end days
- nearest-rank Q90 = 1.0307255992127644e-05
- OHLC/returns/PnL not opened during calibration

Apr-Jun source authority:
- canonical merge run 36688264174
- artifact ID 11083994743
- digest sha256:1d71290fff88c66423e46f1a4b17cb82e58d815feaf47de5ef30c1870103def5
- classification MARGINFI_SOL_APRJUN_SIGNED_FLOW_SOURCE_PASS
- SOL population 10,164
- Jupiter route members 2,893
- source-complete 2,888
- source completeness 0.9982716902868994
- direction proven 2,888
- ambiguous 0
- contradictions 0
- duplicate identities 0

Canonical Development run:
36706322025

Canonical Development artifact:
dls-marginfi-sol-flow-turnover-development-v02
artifact ID 11091643355
digest sha256:80e776f7ab8f6cae0b3b759e9c1b7b54171cbf87a774bee15e498bf64fafe72a

Terminal classification:
MARGINFI_SOL_FLOW_TURNOVER_DEVELOPMENT_NO_EDGE

## Frozen selection

Eligible source events:
2,888

Frozen 5-minute cascades:
305

Below frozen Q90:
230

Selected at or above Q90:
75

Analyzable trades:
75

Distinct UTC entry days:
19

## Market-data integrity

Authority:
Binance public USDT-M SOLUSDT perpetual 1-minute daily archives

Required days:
39

Checksum/integrity PASS:
39 / 39

Missing minutes:
0

Hard errors:
0

## Gross result before fees/slippage

n = 75
mean = -0.0006105371278388638
median = -0.0007095441572981809
win rate = 0.3466666666666667
profit factor = 0.4365004924868731
cumulative simple return = -0.04579028458791479

The frozen immediate SHORT continuation hypothesis is negative before any modeled execution cost.
This is not a fee-driven death.

## Nominal net result

Primary frozen execution model:
- MEXC API taker fee: 8 bps per side
- slippage: 2 bps per side
- approximately 20 bps round trip

n = 75
mean = -0.0026116700966719152
median = -0.002710795974177219
win rate = 0.10666666666666667
profit factor = 0.04378475678708861
cumulative simple return = -0.19587525725039365

## Stress result

Approximately 26 bps round trip:

mean = -0.003212937539089343
median = -0.0033121229099750066
win rate = 0.06666666666666667
profit factor = 0.020871571143164756
cumulative simple return = -0.24097031543170072

## Frozen temporal folds

F1 — Apr-May:
n = 45
mean nominal = -0.002473249893584444
median = -0.002604051239095788
PF = 0.0720129827120523
win rate = 0.15555555555555556
cumulative = -0.11129624521129998

F2 — June:
n = 30
mean nominal = -0.002819300401303122
median = -0.002767598613908979
PF = 0.003913813871712695
win rate = 0.03333333333333333
cumulative = -0.08457901203909367

Both frozen folds are negative.

## Day-block bootstrap

20,000 replicates
19 UTC day blocks
seed 26093001

95% CI:
lower = -0.002957583457986243
upper = -0.002120853499448307

The entire bootstrap interval is negative.

## Gate adjudication

PASS:
- n >= 25
- distinct UTC days >= 8
- F1 n >= 15
- F2 n >= 8

FAIL:
- nominal mean > 0
- nominal median > 0
- nominal PF > 1.10
- F1 nominal mean > 0
- F2 nominal mean > 0
- bootstrap lower > 0

## Terminal consequence

V0.1 is closed as NO_EDGE.

Jul-Sep 2024 MUST remain unopened for this family.
2025 and 2026 market outcomes remain protected.

Forbidden rescue:
- changing Q90;
- inspecting Q80/Q85/Q95 and selecting a favorable percentile;
- changing prior-five-minute turnover denominator;
- changing 1-minute hold;
- flipping SHORT to LONG inside this family;
- adding event-count, amount, hop-count or liability filters;
- changing costs;
- opening Jul-Sep as OOS after Development failed.

A rebound hypothesis derived from this outcome is materially new and may only be tested under a new
pre-outcome family in a still-untouched market period.

## Operational history

Run 36688377641 was SOURCE_BLOCKED before Apr-Jun market outcomes because it downloaded the pre-hotfix
blocked source artifact from the original monthly source run.

Source-binding correction was frozen before outcomes.

Run 36706322025 bound the exact canonical source PASS artifact and exact frozen calibration artifact,
then executed the unchanged frozen Development rule. It is canonical.

## Firewall

jul_sep_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
