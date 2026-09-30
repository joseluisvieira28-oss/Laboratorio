# MARGINFI ORCA EXTREME FLOW REBOUND V0.1 — TERMINAL PRE-OUTCOME CLOSEOUT

Date: 2026-09-30
Branch: dls-marginfi-orca-impact-v01

Family:
DLS-MARGINFI-ORCA-EXTREME-FLOW-REBOUND-001

Frozen hypothesis:
extreme source-proven Marginfi SOL selling through Orca Whirlpools relative to prior-five-minute
SOLUSDT base turnover -> immediate one-minute LONG exhaustion/rebound.

Pre-outcome freeze:
MARGINFI_ORCA_EXTREME_FLOW_REBOUND_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md

Canonical Orca source PASS:
- run 36780139559
- artifact ID 11127536853
- digest sha256:4cbe2bad99237aee32d1e21c5055b17258897df6c312639678e68f15c4ae8dcb
- classification MARGINFI_ORCA_JULSEP_SIGNED_FLOW_SOURCE_PASS
- population 8,857
- Orca presence 7,744
- direction proven 7,717
- exact input amount proven 7,717

Frozen Q90:
1.0307255992127644e-05

Canonical pre-outcome gate:
- run 36781289721
- artifact ID 11127324942
- digest sha256:8dfa5ef296ea65b4e51b46136cd6387b5d0586748ee081737d1ded101c182c87
- classification MARGINFI_ORCA_EXTREME_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE

Pre-outcome selection:
- eligible source events: 7,717
- source cascades: 192
- selected at Q90: 51
- selected distinct UTC days: 8
- F1 Jul-Aug selected: 44
- F2 September selected: 7
- required market-volume days: 36 / 36 PASS
- missing feature minutes: 0
- hard errors: 0

Frozen sample gates:
- n >= 25: PASS
- distinct days >= 8: PASS
- F1 n >= 15: PASS
- F2 n >= 8: FAIL

No Jul-Sep OHLC, returns or PnL were read.

Terminal consequence:
V0.1 closes PRE-OUTCOME.
No market-edge conclusion is drawn because the frozen sample gate was not met.

Forbidden rescue:
- lowering F2 8 -> 7;
- lowering Q90;
- deleting September;
- changing folds;
- changing hold or side;
- opening Jul-Sep returns anyway.

A later untouched period may host a separately frozen family under unchanged feature/side semantics.

Firewall:
jul_sep_market_outcomes_opened=false
oct_dec_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
