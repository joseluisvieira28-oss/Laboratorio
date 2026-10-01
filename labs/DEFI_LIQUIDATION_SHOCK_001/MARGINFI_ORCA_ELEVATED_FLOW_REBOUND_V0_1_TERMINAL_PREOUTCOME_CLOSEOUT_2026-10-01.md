# MARGINFI ORCA ELEVATED FLOW REBOUND V0.1 — TERMINAL PRE-OUTCOME CLOSEOUT

Date: 2026-10-01
Branch: dls-marginfi-orca-elevated-flow-rebound-v01

Family:
DLS-MARGINFI-ORCA-ELEVATED-FLOW-REBOUND-001

Frozen Q75:
1.205342817822632e-05

Canonical Q75 calibration:
- run 36817395624
- artifact ID 11141539211
- classification MARGINFI_ORCA_ELEVATED_FLOW_Q75_CALIBRATION_PASS

Canonical precheck:
- run 36817488029
- artifact ID 11141777170
- classification MARGINFI_ORCA_ELEVATED_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE

Feature-only result:
- selected Q75 cascades: 49
- distinct selected UTC days: 7
- F1 Jul-Aug selected: 42
- F2 September selected: 7

Frozen gates:
- selected >= 35: PASS
- distinct days >= 10: FAIL
- F1 >= 20: PASS
- F2 >= 8: FAIL

No Jul-Sep OHLC, returns or PnL were opened.

Terminal consequence:
V0.1 closes at the pre-outcome gate.

No further percentile lowering is authorized as rescue within this family.

Observed structural fact:
selected high-intensity cascades are strongly clustered in a small number of UTC days.
This motivates a separate daily-maximum-shock family that selects at most one cascade per UTC day and
does not depend on an arbitrary percentile threshold.

Firewall:
jul_sep_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
