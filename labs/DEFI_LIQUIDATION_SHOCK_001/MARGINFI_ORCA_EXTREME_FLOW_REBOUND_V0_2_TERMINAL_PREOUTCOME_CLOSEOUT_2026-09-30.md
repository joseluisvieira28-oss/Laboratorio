# MARGINFI ORCA EXTREME FLOW REBOUND V0.2 — TERMINAL PRE-OUTCOME CLOSEOUT

Date: 2026-09-30
Branch: dls-marginfi-orca-impact-v02

Family:
DLS-MARGINFI-ORCA-EXTREME-FLOW-REBOUND-002

Frozen hypothesis:
Orca forced SOL sell cascades above the original outcome-blind Q90 flow/turnover threshold produce
an immediate one-minute LONG rebound.

Canonical source:
- run 36782337541
- artifact 11127978050
- digest sha256:fab18e89882fb13d5dcbd59ce16fc453f114959688d689d9892d191f8098184a
- MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS
- 2,263 direction-proven exact-amount Orca SOL sell routes

Frozen Q90:
1.0307255992127644e-05

Canonical pre-outcome gate:
run 36782517502
artifact 11127768289
digest sha256:5f6babf4809a67cbf8d77c95c0df151ffc70818e68bd991d4ea8aa9307c2175c

Classification:
MARGINFI_ORCA_EXTREME_REBOUND_V02_PREOUTCOME_INSUFFICIENT_SAMPLE

Pre-outcome result:
- eligible source events: 2,263
- source cascades: 77
- selected at frozen Q90: 14
- selected distinct UTC days: 2
- F1 Oct-Nov selected: 0
- F2 December selected: 14
- market-volume days: 14 / 14 PASS
- missing feature minutes: 0
- hard errors: 0

Frozen sample gates:
- n >=25: FAIL
- days >=8: FAIL
- F1 n >=15: FAIL
- F2 n >=8: PASS

No Oct-Dec OHLC, returns or PnL were read.

Terminal consequence:
V0.2 closes PRE-OUTCOME.
No market-edge conclusion is drawn.

The source result shows a regime shift in the distribution of the previously calibrated Q90 feature.
The threshold is not lowered or recalibrated inside this family.

A separate route-specific hypothesis that does not depend on the old flow-intensity threshold may be
tested only under a new pre-outcome freeze.

Firewall:
oct_dec_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
