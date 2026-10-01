# DLS — MARGINFI ORCA V0.2 GOVERNANCE FACTUAL CORRECTION

Date: 2026-10-01
Branch: dls-marginfi-route-migration-v01

The V0.2 clean-period freeze states that Jul-Sep V0.1 market metrics were not inspected.

Repository chronology now establishes that this statement is not a reliable description of the complete
historical record.

The later terminal V0.1 closeout records inspected Jul-Sep metrics, including:
- gross mean +9.6396 bps/trade;
- gross median +5.5131 bps/trade;
- gross PF 2.6584;
- nominal mean -10.3680 bps/trade.

Therefore Jul-Sep MUST be treated as observed/contaminated for all future scientific purposes.

This correction does not alter V0.2 scientific parameters.

V0.2 remains legitimate only as a forward clean-period replication because:
- its SHORT one-minute hypothesis predates the clean Oct-Dec outcomes;
- side remains SHORT;
- hold remains one minute;
- source semantics remain unchanged;
- no amount/event-count/instruction/time filter is added;
- nominal costs remain 8 bps taker fee/side + 2 bps slippage/side;
- Oct-Dec outcomes remain unopened at this correction point.

Interpretation rule:
Oct-Dec V0.2 is an independent replication of the fixed Orca SHORT 1m rule, not an outcome-blind
discovery of that rule.

No Jul-Sep metric may be used to modify any V0.2 parameter.

Firewall:
julsep_observed=true
oct_dec_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
