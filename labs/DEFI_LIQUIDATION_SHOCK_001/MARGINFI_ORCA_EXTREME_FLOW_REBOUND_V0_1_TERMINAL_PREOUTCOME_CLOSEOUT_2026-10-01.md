# MARGINFI ORCA EXTREME FLOW REBOUND V0.1 — TERMINAL PRE-OUTCOME CLOSEOUT

Date: 2026-10-01
Branch: dls-marginfi-orca-extreme-rebound-v01

Family:
DLS-MARGINFI-ORCA-EXTREME-FLOW-REBOUND-001

Frozen Q90:
0.00013563525170134794

Canonical feature-only precheck:
- run 36817210630
- artifact ID 11141219889
- digest sha256:7c64fef1f3d55e9e57ff3ce940e5f75174fa56a06ba5c6041b3e94149e411f9a
- classification MARGINFI_ORCA_EXTREME_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE

Feature-only result:
- calibration cascades: 192
- selected Q90 cascades: 20
- distinct selected days: 6
- F1 Jul-Aug selected: 17
- F2 September selected: 3

Frozen sample gates:
- selected >= 15: PASS
- distinct days >= 8: FAIL
- F1 >= 10: PASS
- F2 >= 5: FAIL

No Jul-Sep OHLC, returns or PnL were opened.

Terminal consequence:
V0.1 closes at pre-outcome sample gate.

No market-edge conclusion is drawn.

Forbidden rescue within V0.1:
- lower Q90
- weaken day/fold gates
- delete September
- open Jul-Sep outcomes anyway

A materially new elevated-flow family may use a different pre-frozen feature quantile only if it is
defined and numerically frozen before opening Jul-Sep market outcomes.

Firewall:
jul_sep_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
