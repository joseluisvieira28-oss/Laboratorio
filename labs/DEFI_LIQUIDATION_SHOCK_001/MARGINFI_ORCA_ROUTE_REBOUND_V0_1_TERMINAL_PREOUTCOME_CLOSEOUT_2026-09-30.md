# MARGINFI ORCA ROUTE-SPECIFIC REBOUND V0.1 — TERMINAL PRE-OUTCOME CLOSEOUT

Date: 2026-09-30
Branch: dls-marginfi-orca-route-rebound-v01

Family:
DLS-MARGINFI-ORCA-ROUTE-REBOUND-001

Canonical source:
run 36782337541
artifact 11127978050
MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS

Canonical precheck:
run 36782817813
artifact 11128123329
digest sha256:ec9e076c4d9d2a365d2b72f805afec31fd4017098e301e690065290b068168b5

Classification:
MARGINFI_ORCA_ROUTE_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE

Source-only result:
- eligible source events: 2,263
- source cascades: 77
- funding exclusions: 0
- candidates: 77
- distinct UTC days: 14
- F1 Oct-Nov: 61
- F2 December: 16

Frozen gates:
- n >=40: PASS
- days >=8: PASS
- F1 n >=10: PASS
- F2 n >=20: FAIL

No OHLC, returns or PnL were read.

Consequence:
V0.1 closes PRE-OUTCOME.
No market-edge conclusion.

The failure is caused by uneven calendar source density, not by a market result.
A new family may use a source-only pre-frozen chronological balanced split, provided no outcomes are
opened first.

Firewall:
oct_dec_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
