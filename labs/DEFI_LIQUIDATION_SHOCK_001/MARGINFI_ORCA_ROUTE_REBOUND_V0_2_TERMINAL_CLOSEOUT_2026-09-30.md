# MARGINFI ORCA ROUTE-SPECIFIC REBOUND V0.2 — TERMINAL DEVELOPMENT CLOSEOUT

Date: 2026-09-30
Branch: dls-marginfi-orca-route-rebound-v02

Family:
DLS-MARGINFI-ORCA-ROUTE-REBOUND-002

Frozen hypothesis:
every source-proven Marginfi SOL sell cascade executed through Orca Whirlpools exhibits an immediate
one-minute LONG cross-venue rebound.

Frozen authority:
MARGINFI_ORCA_ROUTE_REBOUND_V0_2_BALANCED_TEMPORAL_FREEZE_2026-09-30.md

Canonical source:
- run 36782337541
- artifact 11127978050
- MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS

Canonical pre-outcome READY:
- run 36783063662
- artifact 11128253922
- digest sha256:d41c784117cdffad614980a74530254de5a15b1c13094f1d017e26087ea41b69
- 77 candidates
- 14 UTC days
- balanced temporal folds F1=38 / F2=39
- no OHLC/return/PnL read before READY

Canonical Development run:
36783263812

Canonical Development artifact:
dls-marginfi-orca-route-rebound-development-v02
artifact ID 11127764849
digest sha256:36b993b15f4e3300395ffa5ccd4b08f59ac1054d3193afd9c7fd0f1b0968e526

Terminal classification:
MARGINFI_ORCA_ROUTE_REBOUND_V02_DEVELOPMENT_NO_EDGE

## Market data integrity

Binance public USDT-M SOLUSDT 1m:
- required days 14
- manifest 14
- checksum/integrity PASS 14 / 14
- missing minutes 0
- hard errors 0

## Gross result before modeled fees/slippage

n = 77
mean = +0.000899605834041115
= +8.99605834041115 bps / trade

median = -0.00004786521156419088
= -0.4786521156419088 bps

win rate = 0.4935064935064935
profit factor = 2.5961408071676493
cumulative simple return = +0.06926964922116585

This is the first materially positive gross market response in the Marginfi/Orca route investigation.

## Gross temporal halves — descriptive

F1 — first 38 chronological candidates:
- gross mean = +0.00019768097212318728
- +1.9768097212318728 bps/trade
- gross median = -0.0004058215809474297
- gross PF = 1.3784893274094183
- gross win rate = 0.3684210526315789
- gross cumulative = +0.007511876940681117

F2 — last 39 chronological candidates:
- gross mean = +0.0015835326225765317
- +15.835326225765317 bps/trade
- gross median = +0.0014101720409889218
- +14.101720409889218 bps
- gross PF = 3.622276091190672
- gross win rate = 0.6153846153846154
- gross cumulative = +0.061757772280484735

These gross fold statistics are descriptive only.
The frozen scientific classification uses nominal net metrics.

## Frozen nominal execution result

Primary model:
- MEXC API taker 8 bps per side
- slippage 2 bps per side
- approximately 20 bps round-trip

n = 77
mean = -0.0011010734131733097
= -11.010734131733097 bps/trade

median = -0.00204740787243648
profit factor = 0.3983356476704097
win rate = 0.22077922077922077
cumulative simple return = -0.08478265281434486

F1 nominal:
- n 38
- mean -0.0018021562459707306
- PF 0.1524450608840451

F2 nominal:
- n 39
- mean -0.00041796706326813063
- PF 0.7288372073965913

## Stress result

Approx. 26 bps round-trip:
- mean -0.001700712937232103
- PF 0.2644478894973437
- cumulative -0.13095489616687192

## Frozen day-block bootstrap

20,000 replicates
14 UTC day blocks
seed 26093006

Nominal mean 95% CI:
- lower = -0.0019931473758954305
- upper = -0.000012727029963887969

The entire frozen nominal interval is negative.

## Gate adjudication

PASS:
- n >=60
- distinct days >=8
- F1 n >=30
- F2 n >=30

FAIL:
- nominal mean >0
- nominal median >0
- nominal PF >1.10
- F1 nominal mean >0
- F2 nominal mean >0
- bootstrap lower >0

## Interpretation boundary

The family is terminal NO_EDGE under its pre-frozen execution model.

The positive gross result does NOT authorize:
- retroactively lowering fees/slippage;
- reclassifying the family as SURVIVES;
- opening 2025 as rescue;
- choosing a favorable cost model after seeing the result.

Descriptively, the observed gross mean implies that an execution path would need total average
round-trip drag materially below about 9 bps merely to preserve positive mean expectancy.
That is an execution-feasibility clue, not a scientific promotion.

A distinct execution-cost/venue family would require:
- a new pre-outcome freeze;
- independently justified executable fees/slippage;
- an untouched validation period;
- no reuse of this Development as validation.

## Firewall

market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
