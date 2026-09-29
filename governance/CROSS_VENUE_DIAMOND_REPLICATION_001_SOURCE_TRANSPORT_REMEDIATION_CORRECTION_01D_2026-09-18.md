# CROSS-VENUE-DIAMOND-REPLICATION-001 — SOURCE TRANSPORT REMEDIATION CORRECTION 01D — 2026-09-18

Status: FROZEN_BEFORE_SEMANTIC_DATE_AGGREGATION_DIAGNOSTIC_AND_BEFORE_ANY_SIGNAL_OR_OUTCOME_CALCULATION

Observed before this correction:
- modules 1..6 are server-valid;
- dateAggrType candidates 1D, 1W, 1M, 1, 2, 3, 4, 5 were rejected;
- official OKX changelog describes Get historical market data ranges as "daily" and "monthly";
- no archive payload or trading outcome has been opened.

Final bounded semantic dateAggrType diagnostic:
- use module=1 only;
- candidates fixed before execution: D, M, day, month, daily, monthly, 1d, 1m, DAY, MONTH, 0, 6;
- inspect only HTTP status/provider code/message/metadata;
- no archive URL may be followed;
- stop broad enumeration after this list. If no candidate is accepted, the bulk archive endpoint remains SOURCE_BINDING_UNRESOLVED and another official source route must be used.

All trading rules, symbols, window, costs, execution, and governance remain unchanged.
