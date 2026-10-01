# DLS — MARGINFI ORCA EXTREME FLOW REBOUND V0.1 — PRE-OUTCOME FREEZE

Date: 2026-10-01
Branch: dls-marginfi-orca-extreme-rebound-v01
Status: FROZEN BEFORE JUL-SEP 2024 MARKET OUTCOMES

Family:
DLS-MARGINFI-ORCA-EXTREME-FLOW-REBOUND-001

## Motivation

Two distinct pre-frozen SHORT continuation families have produced gross-negative results:
- Jupiter flow-turnover Apr-Jun 2024
- Orca flow-turnover Oct-Dec 2024

This motivates a materially new exhaustion/rebound hypothesis.

Jul-Sep 2024 Orca market outcomes remain unopened and are the first validation period.

## Frozen source + feature authority

Orca Jul-Sep signed-flow source:
- run 36780139559
- artifact ID 11127536853
- digest sha256:4cbe2bad99237aee32d1e21c5055b17258897df6c312639678e68f15c4ae8dcb
- classification MARGINFI_ORCA_JULSEP_SIGNED_FLOW_SOURCE_PASS
- direction proven 7,717
- exact input amount proven 100%

Feature-only Orca calibration:
- run 36816611039
- artifact ID 11141731925
- digest sha256:a87c854c4ea4f35653f21929c1d9ec302f2e38a6dfc3721fccde6f383ce82a72
- classification MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_PASS
- Q90 = 0.00013563525170134794
- 192 cascades
- OHLC/returns/PnL unopened

Frozen signal:
flow_turnover_intensity >= 0.00013563525170134794

Feature definition:
cascade_sold_sol / Binance SOLUSDT prior-five-complete-minute base volume.

No recalibration.
No alternate percentile.

## Frozen execution

Development period:
[2024-07-01T00:00:00Z, 2024-10-01T00:00:00Z)

For each selected source cascade:
- side = LONG SOLUSDT
- entry = OPEN of first full UTC minute strictly after cascade end
- exit = OPEN exactly 1 minute later
- no pyramiding
- one trade per cascade
- funding-boundary exclusion unchanged: 00:00 / 08:00 / 16:00 UTC

This is the exact directional mirror of the frozen 1-minute continuation test.
No other hold is authorized.

## Frozen pre-outcome sample gate

Before opening OHLC/returns, feature-only selected sample must satisfy ALL:
1. selected cascades >= 15
2. distinct UTC selected cascade-end days >= 8
3. F1 selected count >= 10
4. F2 selected count >= 5

F1:
[2024-07-01T00:00:00Z, 2024-09-01T00:00:00Z)

F2:
[2024-09-01T00:00:00Z, 2024-10-01T00:00:00Z)

If any gate fails:
MARGINFI_ORCA_EXTREME_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE

No Jul-Sep OHLC/return may be opened.

If all gates pass:
MARGINFI_ORCA_EXTREME_REBOUND_PREOUTCOME_READY

## Frozen costs

Primary:
- MEXC Futures API taker fee 8 bps/side
- slippage 2 bps/side
- approx 20 bps round trip

Stress:
- same fee
- slippage 5 bps/side
- approx 26 bps round trip

## Frozen Development gates

Only if pre-outcome READY:

MARGINFI_ORCA_EXTREME_REBOUND_DEVELOPMENT_SURVIVES iff ALL:
1. n >= 15
2. distinct UTC entry days >= 8
3. nominal mean > 0
4. nominal median > 0
5. nominal PF > 1.10
6. F1 n >= 10
7. F2 n >= 5
8. F1 nominal mean > 0
9. F2 nominal mean > 0
10. UTC-day block-bootstrap 95% CI lower > 0

Bootstrap:
- 20,000 replicates
- UTC entry-day blocks
- seed = 26100102

Otherwise:
MARGINFI_ORCA_EXTREME_REBOUND_DEVELOPMENT_NO_EDGE

## Future boundary

Only if Development SURVIVES:
Oct-Dec 2024 cannot be used as OOS because its outcomes have already been opened in the prior SHORT family.

Next eligible OOS would require a separately authorized protected 2025 source/outcome window.

No 2025 outcome is authorized by this freeze.

## Forbidden rescue

After Jul-Sep outcomes open:
- no Q90 change
- no percentile alternatives
- no LONG->SHORT change
- no hold alternatives
- no amount/event/hop/liability/time filters
- no cost changes
- no use of Oct-Dec as OOS
- no 2025 opening without separate authorization

## Firewall

jul_sep_market_outcomes_opened=false
oct_dec_not_valid_oos=true
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
