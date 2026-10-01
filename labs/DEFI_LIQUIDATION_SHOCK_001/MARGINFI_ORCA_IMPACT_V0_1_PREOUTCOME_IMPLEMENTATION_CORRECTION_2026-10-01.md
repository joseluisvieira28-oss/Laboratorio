# MARGINFI ORCA IMPACT V0.1 — PRE-OUTCOME IMPLEMENTATION CORRECTION

Date: 2026-10-01
Branch: dls-marginfi-route-migration-v01
Status: CORRECTED BEFORE JUL-SEP MARKET OUTCOMES

Scientific freeze:
MARGINFI_ORCA_FORCED_FLOW_IMPACT_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md

Canonical PREOUTCOME gate:
- run 36816757093
- artifact ID 11141084742
- digest sha256:4ea4c13a398128021e74b40b6f13d5ff13e368d1368bdb9a003dac3a621b9cfc
- classification MARGINFI_ORCA_IMPACT_PREOUTCOME_READY
- eligible events 7,717
- source cascades 192
- distinct days 36
- F1 cascades 157
- F2 cascades 35

Two implementation defects were found during pre-launch audit, before any Jul-Sep OHLC/return/PnL was
opened by this family:

1. SHORT execution math had LONG-oriented signs:
   old gross = exit/entry - 1
   old execution slippage = entry*(1+slip), exit*(1-slip)

   Correct frozen SHORT implementation:
   gross = 1 - exit/entry
   entry sell execution = entry*(1-slip)
   exit buy-to-cover execution = exit*(1+slip)
   net = (1 - exit_exec/entry_exec) - fee*(1 + exit_exec/entry_exec)

2. Development workflow did not explicitly require the immutable PREOUTCOME_READY receipt.

Corrections:
- commit 13601ba96b54eb9502491951e92e8273c21fb833 fixes SHORT math and requires PREOUTCOME_READY;
- commit 9f670e4c2909332eee3a34d74511659c34a7e036 downloads and binds exact precheck artifact ID 11141084742.

No scientific rule changed:
- source population unchanged;
- cascade construction unchanged;
- side remains SHORT;
- hold remains 1 minute;
- costs unchanged;
- folds unchanged;
- gates unchanged;
- bootstrap unchanged.

At correction time:
jul_sep_market_outcomes_opened=false
oct_dec_2024_opened=false
market_2025_opened=false
market_2026_opened=false
post_outcome_tuning=false
