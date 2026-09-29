# MARGINFI JUPITER SWAP DIRECTION V0.1 — TERMINAL SOURCE CLOSEOUT

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01

Canonical run:
36549220851

Artifact:
dls-marginfi-jupiter-swap-direction-cal-v01
artifact ID 11024192973
digest sha256:0ce021f40c26d73f1f3c42449a9f1c6194114ab472ad6c7acdb5de26d6f902ce

Membership gate:
MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_PASS
population_member_count = 2605

Calibration:
sample_count = 64
direction_proven = 37
direction_ambiguous = 0
source_evidence_incomplete = 27
contradictions = 0
direction_rate_complete = 1.0
incomplete_rate = 0.421875

Terminal classification:
MARGINFI_JUPITER_SWAP_DIRECTION_CALIBRATION_PARTIAL

The V0.1 PASS rule required:
- incomplete rate <= 5%;
- deterministic direction among complete >= 90%;
- contradictions = 0.

V0.1 therefore does not authorize the frozen full Jan-2024 census.

Failure diagnosis:
all 27 incomplete rows were classified swap_event_count_2.
No V0.1 bank mapping, direction ambiguity or contradiction caused the threshold failure.

V0.1 decoder and exactly-one-SwapEvent rule remain frozen and must not be changed or reinterpreted.

Any multi-event route semantics must be evaluated as a new source-semantic version with:
- a new pre-decode freeze;
- a disjoint calibration population;
- no market prices, returns or PnL.

Firewall:
full_v01_census_authorized=false
prices=false
returns=false
pnl=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
