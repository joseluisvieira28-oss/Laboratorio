# MARGINFI ORCA TOP-QUARTILE REBOUND OOS V0.1 — TERMINAL PRE-OUTCOME CLOSEOUT

Date: 2026-10-01
Branch: dls-marginfi-orca-rebound-oos-v01

Family:
DLS-MARGINFI-ORCA-TOPQ-REBOUND-OOS-001

Discovery authority:
MARGINFI_ORCA_FLOW_RESPONSE_DISCOVERY_PASS
run 36814416648
artifact 11140333264
digest sha256:df7e37d1b2ea23052589802cda1d0b0dc37921bae3a1c23fe6dd3bd2fd614162

Canonical Oct-Dec SOL population:
run 36814752093
artifact 11140604962
classification MARGINFI_SOL_OCTDEC_POPULATION_PASS
SOL population = 2,688
duplicates = 0
unmapped liability mints = 0

Canonical Oct-Dec Orca source:
run 36814861360
artifact 11140129257
digest sha256:8d8b1b9fdf84dcc234e46012a39cc5126fa5b3068e739daf1f5d7e83ee42a4d7
classification MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS
- canonical SOL population = 2,688
- Orca presence = 2,263
- source complete = 2,263 / 2,263 = 100%
- direction proven = 2,263
- direction ambiguous = 0
- contradictions = 0
- exact route input amount proven = 2,263 / 2,263

Frozen absolute threshold:
1.252336612578286e-05

Canonical feature-only precheck:
run 36815199005
artifact 11140992589
digest sha256:b452730607f3db4c7f983ce748c74be1ee7f7a51301a1f3876e7d62698cac470

Classification:
MARGINFI_ORCA_TOPQ_REBOUND_OOS_INSUFFICIENT_SAMPLE

Pre-outcome result:
- eligible source events = 2,263
- source cascades = 77
- selected signals = 14
- distinct selected days = 2
- F1 Oct-Nov selected = 0
- F2 December selected = 14
- market-volume days = 14 / 14 PASS
- missing feature minutes = 0
- hard errors = 0

No Oct-Dec OHLC, returns or PnL were read.

Feature-only monthly regime evidence:
October:
- cascades 24
- selected 0
- median intensity 6.420591487009397e-08
- max 3.754927633515869e-06

November:
- cascades 37
- selected 0
- median intensity 3.282627886328106e-07
- max 6.377596702108489e-06

December:
- cascades 16
- selected 14
- median intensity 6.857361858623473e-05
- max 0.001273993821578461

Structural interpretation:
the absolute Jul-Sep top-quartile boundary is not sample-portable into Oct-Dec because the feature
distribution changes by orders of magnitude across months.

This is a feature-regime result only.
No market-edge conclusion is drawn.

Forbidden rescue inside V0.1:
- lower the frozen absolute threshold
- delete Oct-Nov
- lower sample gates
- open Oct-Dec outcomes anyway

A new causal rolling-normalization family may be tested because Oct-Dec market outcomes remain unopened.

Firewall:
oct_dec_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
