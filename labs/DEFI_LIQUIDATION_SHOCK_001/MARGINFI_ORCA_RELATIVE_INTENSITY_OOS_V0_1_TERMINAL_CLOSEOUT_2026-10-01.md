# MARGINFI ORCA ROLLING RELATIVE-INTENSITY OOS V0.1 — TERMINAL CLOSEOUT

Date: 2026-10-01
Branch: dls-marginfi-orca-relative-intensity-oos-v01

Family:
DLS-MARGINFI-ORCA-RELATIVE-INTENSITY-OOS-001

Discovery authority:
- run 36814416648
- artifact 11140333264
- classification MARGINFI_ORCA_FLOW_RESPONSE_DISCOVERY_PASS
- discovered sign POSITIVE_REBOUND

Frozen OOS precheck:
- run 36815529203
- artifact 11141660030
- digest sha256:b5a151079b7da61a457ba5d9634bf7abe0fe2befb628649b36b97648d1da64dc
- classification MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_PREOUTCOME_READY
- selected 31
- distinct days 8
- F1 Oct-Nov 18
- F2 Dec 13
- funding excluded 0

Canonical OOS run:
36815654911

Canonical OOS artifact:
dls-marginfi-orca-relative-intensity-oos-v01
artifact ID 11140249924
digest sha256:dcf074bd8711b6d45c61cb8413132ab2b5985a08726b49e69cc38dd4cdd2568f

Terminal classification:
MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_NO_EDGE

## Frozen rule

Feature:
flow_turnover_intensity =
source-proven Orca cascade sold SOL / prior-five-minute Binance SOLUSDT base turnover

Normalization:
- exactly 30 immediately preceding feature-valid cascades
- rolling nearest-rank 75th percentile
- rank 23 of prior 30
- current cascade excluded from its own threshold

Execution:
- side LONG SOLUSDT
- entry OPEN(A)
- exit OPEN(A+1m)
- primary costs 8 bps taker fee/side + 2 bps slippage/side
- approximately 20 bps round trip
- stress approximately 26 bps round trip

## OOS result

N = 31
distinct UTC entry days = 8

Gross before fees/slippage:
- mean = +0.001030948785579418
- median = +0.0012346288705615827
- win rate = 0.6451612903225806
- profit factor = 2.7923123604599636
- cumulative simple return = +0.03195941235296196

This is approximately:
- +10.3095 bps mean gross per trade
- +12.3463 bps median gross per trade

Nominal net at frozen ~20 bps round trip:
- mean = -0.0009698880206502065
- median = -0.0007664522703143472
- win rate = 0.2903225806451613
- profit factor = 0.36876020640423385
- cumulative simple return = -0.030066528640156402

Stress ~26 bps round trip:
- mean = -0.0015696062323460648
- median = -0.001366292506865219
- win rate = 0.25806451612903225
- profit factor = 0.2019905603539161
- cumulative simple return = -0.048657793202728006

## Temporal robustness

F1 — October + November:
- n = 18
- nominal mean = -0.0020734126182605306
- nominal median = -0.0016816998794397476
- nominal PF = 0.011535567968242965
- nominal win rate = 0.05555555555555555
- nominal cumulative = -0.03732142712868955

Gross F1:
- mean approximately -0.00007390
- approximately -0.739 bps/trade
- gross result is slightly negative even before execution cost

F2 — December:
- n = 13
- nominal mean = +0.0005580691145025496
- nominal median = +0.0013739657832902328
- nominal PF = 1.7347521922663138
- nominal win rate = 0.6153846153846154
- nominal cumulative = +0.0072548984885331454

Gross F2:
- mean approximately +0.00256074
- approximately +25.607 bps/trade
- median approximately +33.776 bps
- gross PF approximately 10.929
- gross win rate approximately 84.62%

Thus the positive aggregate gross OOS result is concentrated in the December regime.
October-November gross is slightly negative.

## Day-block bootstrap

20,000 replicates
seed = 26100104
8 UTC day blocks

Nominal 95% CI:
lower = -0.0022293352329682973
upper = +0.0003127924662332471

The interval crosses zero.

## Gate adjudication

PASS:
- n >= 25
- distinct days >= 8
- F1 n >= 15
- F2 n >= 8
- F2 nominal mean > 0

FAIL:
- overall nominal mean > 0
- overall nominal median > 0
- nominal PF > 1.10
- F1 nominal mean > 0
- bootstrap lower > 0

## Scientific interpretation

V0.1 is terminal NO_EDGE under the frozen execution model.

This family may NOT be rescued by:
- lowering fees after observing outcomes
- selecting December only
- deleting October-November
- changing rolling lookback or percentile
- changing hold horizon
- changing side
- changing filters

Critically, fee reduction alone is not sufficient scientific rescue because the frozen F1 Oct-Nov gross
mean is already slightly negative.

However, December exhibits a materially different positive gross regime.
That observation may motivate a separate SOURCE/FEATURE-ONLY regime investigation.
Any future trading hypothesis derived from it requires a new pre-outcome family and untouched market period.

## Firewall

market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
