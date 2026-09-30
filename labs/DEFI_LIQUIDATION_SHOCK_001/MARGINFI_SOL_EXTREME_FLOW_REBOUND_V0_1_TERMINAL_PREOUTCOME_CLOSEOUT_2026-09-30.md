# MARGINFI SOL EXTREME FLOW REBOUND V0.1 — TERMINAL PRE-OUTCOME CLOSEOUT

Date: 2026-09-30
Branch: dls-marginfi-flow-turnover-rebound-v01

Family:
DLS-MARGINFI-SOL-EXTREME-FLOW-REBOUND-001

Frozen hypothesis:
extreme source-proven forced SOL selling relative to prior-five-minute SOLUSDT base turnover -> immediate
one-minute LONG exhaustion/rebound.

Pre-outcome freeze:
MARGINFI_SOL_EXTREME_FLOW_REBOUND_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md

Frozen Q90:
1.0307255992127644e-05

Canonical Jul-Sep source PASS:
- run 36769242124
- artifact ID 11123027458
- digest sha256:ce0627614a9fdc3b5acb7d8dac3d8c189b88024a31e038b069d3c8aa375dc38d
- classification MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_PASS
- SOL population 8,857
- route members 782
- direction proven 780
- source complete rate 0.9974424552429667
- ambiguity 0
- contradictions 0
- duplicates 0

Canonical feature-only pre-outcome gate:
- run 36769403065
- artifact ID 11123223133
- digest sha256:303c3daab584d6ec694c1991de2afc105b9b7ae023b03225e21a70f0d99bbd89
- classification MARGINFI_SOL_EXTREME_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE

Pre-outcome selection result:
- eligible source events: 780
- source cascades: 79
- selected at frozen Q90: 33
- selected distinct UTC days: 8
- F1 Jul-Aug selected: 31
- F2 September selected: 2

Frozen sample gates:
- n >= 25: PASS
- distinct days >= 8: PASS
- F1 n >= 15: PASS
- F2 n >= 8: FAIL

No Jul-Sep OHLC, returns or PnL were read by the pre-outcome gate.

Terminal classification:
MARGINFI_SOL_EXTREME_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE

Consequence:
V0.1 closes without opening Jul-Sep market outcomes.
No market-edge conclusion is drawn because the frozen Development sample requirement was not met.

Observed source-only structural result:
- July route members / SOL population = 487 / 865
- August = 277 / 7,677
- September = 18 / 315

The sharp route-share change is descriptive source evidence and motivates a separate route-migration
source investigation. It is not itself a trading edge claim.

Forbidden rescue:
- lowering F2 n threshold;
- deleting September;
- lowering Q90;
- changing folds;
- opening Jul-Sep returns anyway;
- selecting another hold/side from unseen outcomes inside this family.

Firewall:
jul_sep_market_outcomes_opened=false
oct_dec_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
