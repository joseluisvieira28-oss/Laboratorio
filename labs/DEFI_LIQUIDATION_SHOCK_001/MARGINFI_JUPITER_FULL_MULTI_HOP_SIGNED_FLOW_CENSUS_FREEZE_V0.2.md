# MARGINFI JUPITER FULL MULTI-HOP SIGNED-FLOW CENSUS FREEZE V0.2

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01
Status: FROZEN BEFORE V0.2 CALIBRATION RESULT

Run only if:
MARGINFI_JUPITER_MULTI_HOP_DIRECTION_CALIBRATION_PASS

Population:
- every member from the immutable Jan-2024 membership PASS population;
- no sampling;
- no direction, amount, token or return filter.

Source semantics:
- exactly MARGINFI_JUPITER_MULTI_HOP_DIRECTION_CALIBRATION_FREEZE_V0.2.md;
- same transport decoder;
- same route-root ownership;
- same ordered simple-path rule;
- same endpoint-to-bank direction rule.

Full source PASS requires all:
1. non-incomplete source evidence rate >= 95%;
2. deterministic direction among non-incomplete members >= 90%;
3. contradictions = 0.

PASS:
MARGINFI_JUPITER_MULTI_HOP_SIGNED_FLOW_SOURCE_PASS

Threshold miss:
MARGINFI_JUPITER_MULTI_HOP_SIGNED_FLOW_SOURCE_PARTIAL

Source/layout/identity failure:
MARGINFI_JUPITER_MULTI_HOP_SIGNED_FLOW_SOURCE_BLOCKED

PASS authorizes only a separately frozen market-return experiment.
It does not authorize live trading or any market outcome opening by itself.

Firewall:
prices=false
returns=false
pnl=false
usd_notional=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_calibration_rule_change=false
