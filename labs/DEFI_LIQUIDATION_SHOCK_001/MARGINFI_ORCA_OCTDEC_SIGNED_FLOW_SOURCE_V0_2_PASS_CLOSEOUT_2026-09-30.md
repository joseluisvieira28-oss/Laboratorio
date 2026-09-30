# MARGINFI ORCA OCT-DEC SIGNED-FLOW SOURCE V0.2 — PASS CLOSEOUT

Date: 2026-09-30
Branch: dls-marginfi-orca-impact-v02

Canonical population run:
36781624393
artifact 11128590550
digest sha256:7c1461af71d38c3705a76f9308858bdc0732538d858d0f647bd688848f78169c

Canonical merge run:
36782337541

Canonical terminal source artifact:
dls-marginfi-orca-octdec-signed-flow-source-v021
artifact ID 11127978050
digest sha256:fab18e89882fb13d5dcbd59ce16fc453f114959688d689d9892d191f8098184a

Classification:
MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS

Results:
- canonical SOL population: 2,688
- adjudication count: 2,688
- Orca presence: 2,263
- not-Orca: 425
- source complete: 2,263 / 2,263 = 100%
- direction proven: 2,263
- direction ambiguous: 0
- contradictions: 0
- exact input amount proven: 2,263 / 2,263 = 100%
- missing identities: 0
- extra identities: 0
- duplicates: 0
- errors: 0

Monthly:
October: population 64, Orca/direction 61
November: population 275, Orca/direction 162
December: population 2,349, Orca/direction 2,040

Decoded instructions:
- swap 805
- swap_v2 1,258
- two_hop_swap_v2 200

Route semantic:
COLLATERAL_TO_LIABILITY_ORCA_PROVEN = 2,263

The original merge in run 36781844349 was operationally blocked only by a stale Jul-Sep receipt filename.
All 16 source shards had already passed.
The merge-only V0.2.1 hotfix changed that filename only and reused the immutable shards.

No Oct-Dec market outcomes were opened.

Consequence:
V0.2 may proceed to its mandatory feature-only pre-outcome Q90 gate.

Firewall:
oct_dec_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
