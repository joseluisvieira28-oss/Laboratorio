# MARGINFI ORCA ROUTE REBOUND V0.2 — PRE-OUTCOME READY CLOSEOUT

Date: 2026-09-30
Branch: dls-marginfi-orca-route-rebound-v02

Family:
DLS-MARGINFI-ORCA-ROUTE-REBOUND-002

Frozen authority:
MARGINFI_ORCA_ROUTE_REBOUND_V0_2_BALANCED_TEMPORAL_FREEZE_2026-09-30.md

Canonical source:
- run 36782337541
- artifact 11127978050
- digest sha256:fab18e89882fb13d5dcbd59ce16fc453f114959688d689d9892d191f8098184a
- MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS

Canonical pre-outcome run:
36783063662

Canonical pre-outcome artifact:
dls-marginfi-orca-route-rebound-v02-precheck
artifact ID 11128253922
digest sha256:d41c784117cdffad614980a74530254de5a15b1c13094f1d017e26087ea41b69

Classification:
MARGINFI_ORCA_ROUTE_REBOUND_V02_PREOUTCOME_READY

Source-only selection:
- eligible source events: 2,263
- source cascades: 77
- funding exclusions: 0
- candidates: 77
- distinct UTC candidate days: 14
- balanced chronological split K = 38
- F1 candidates: 38
- F2 candidates: 39

Frozen pre-outcome gates:
- N >=60: PASS
- distinct days >=8: PASS
- F1 >=30: PASS
- F2 >=30: PASS

No OHLC, return or PnL was read.

Consequence:
The exact 77-candidate pre-outcome artifact is authorized as the immutable Development candidate/fold
manifest. Development may now open only the required Oct-Dec 2024 entry/exit market prices under the
already frozen LONG 1-minute rule and cost model.

2025/2026 remain closed.

Firewall:
oct_dec_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
