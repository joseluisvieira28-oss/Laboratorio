# MARGINFI -> ORCA SIGNED-FLOW CALIBRATION V0.1 — PASS CLOSEOUT

Date: 2026-09-30
Branch: dls-marginfi-route-migration-v01

Canonical run:
36770954139

Canonical artifact:
dls-marginfi-orca-signed-flow-calibration-v01
artifact ID 11124145615
digest sha256:be6d0fe8c6c91dd7d7183af91b4f408e2829f763c4c790cced9b9fa8f67d627a

Classification:
MARGINFI_ORCA_SIGNED_FLOW_CALIBRATION_PASS

Frozen sample:
- August 2024: 32
- September 2024: 32
- total: 64

Results:
- exact transactions recovered: 64 / 64
- source complete: 64 / 64
- direction proven: 64 / 64
- direction ambiguous: 0
- contradictions: 0
- exact route input amount proven: 64 / 64
- transaction transport errors: 0
- identity conflicts: 0

Decoded official Orca instruction types:
- swap: 9
- swap_v2: 38
- two_hop_swap_v2: 17

Route semantic:
- COLLATERAL_TO_LIABILITY_ORCA_PROVEN: 64 / 64

Thus every frozen calibration transaction proves:
Marginfi SOL collateral liquidation -> post-liquidation Orca Whirlpools swap route ->
source-proven SOL sell pressure -> liability-token buy pressure.

This is source semantics only.
No price, OHLC, return or PnL was used.

Consequence:
A separately frozen full Jul-Sep Orca source census is authorized.

Firewall:
prices=false
ohlc=false
returns=false
pnl=false
market_2024_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_decode_tuning=false
