# MARGINFI SOL FLOW-TO-TURNOVER CALIBRATION V0.1 — PASS CLOSEOUT

Date: 2026-09-30
Branch: dls-marginfi-flow-turnover-impact-v01

Canonical run:
36686002313

Canonical artifact:
dls-marginfi-sol-flow-turnover-calibration-v01
artifact ID 11083738178
digest sha256:6cacadfffce7225984258a634d0df0ac5685c0a7915bedc9e0a0e595fabc1327

Classification:
MARGINFI_SOL_FLOW_TURNOVER_CALIBRATION_PASS

Feature-only calibration:
- eligible source events: 1,360
- frozen 5-minute cascades: 203
- distinct UTC cascade-end days: 34
- required Binance volume days: 34
- hard errors: 0
- missing required pre-entry minutes: 0
- OHLC read: false
- returns read: false
- PnL read: false

Nearest-rank 90th percentile:
- N = 203
- rank = 183
- Q90 = 1.0307255992127644e-05

Observed feature range:
- min = 2.090969589189209e-08
- max = 0.000582530484516869

Frozen numeric threshold for all later V0.1 tests:

FLOW_TURNOVER_INTENSITY_Q90 = 1.0307255992127644e-05

No alternative percentile is authorized.
No threshold tuning is authorized.

This threshold may be used only with the exact feature definition frozen in
MARGINFI_SOL_FLOW_TURNOVER_IMPACT_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md:
cascade_sold_sol / prior-five-complete-minute Binance USDT-M SOLUSDT base volume.

Firewall:
apr_jun_market_outcomes_opened=false
jul_sep_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
