# MARGINFI ORCA FLOW-TURNOVER CALIBRATION V0.1 — PASS CLOSEOUT

Date: 2026-10-01
Branch: dls-marginfi-orca-flow-turnover-v01

Canonical run:
36816611039

Canonical artifact:
dls-marginfi-orca-flow-turnover-calibration-v01
artifact ID 11141731925
digest sha256:a87c854c4ea4f35653f21929c1d9ec302f2e38a6dfc3721fccde6f383ce82a72

Classification:
MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_PASS

Feature-only calibration:
- eligible Orca direction-proven source events: 7,717
- frozen 5-minute cascades: 192
- distinct UTC cascade-end days: 36
- required Binance volume days: 36
- hard errors: 0
- missing required pre-entry volume minutes: 0
- OHLC read: false
- returns read: false
- PnL read: false

Nearest-rank 90th percentile:
- N = 192
- rank = 173
- Q90 = 0.00013563525170134794

Observed feature range:
- min = 4.6848325369387625e-09
- max = 0.003745285723997163

Frozen numeric threshold:

ORCA_FLOW_TURNOVER_INTENSITY_Q90 = 0.00013563525170134794

No alternative percentile is authorized.
No threshold tuning is authorized.

This threshold may only be used with the exact feature definition frozen in
MARGINFI_ORCA_FLOW_TURNOVER_IMPACT_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md.

Firewall:
jul_sep_market_outcomes_opened=false
oct_dec_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
