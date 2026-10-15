# CROSS-VENUE-DIAMOND-REPLICATION-001 — SOURCE TRANSPORT REMEDIATION CORRECTION 01C — 2026-09-18

Status: FROZEN_BEFORE_DATE_AGGREGATION_DIAGNOSTIC_AND_BEFORE_ANY_SIGNAL_OR_OUTCOME_CALCULATION

Established source facts before this correction:
- OKX server accepts numeric historical-market-data modules 1 through 6; modules 7 through 10 return "Parameter module error".
- With modules 1 through 6, the same request advances to "Parameter dateAggrType error".
- No archive payload, signal, return, PnL, expectancy, profit factor, or trading outcome has been opened.

Authorized metadata-only diagnostic:
- modules are fixed to 1..6;
- dateAggrType candidates are bounded to: 1D, 1W, 1M, 1, 2, 3, 4, 5;
- inspect only HTTP status, provider code/message, response metadata keys, archive file names/URLs, instrument identifiers, and declared date ranges;
- do not follow/download any returned archive URL;
- once an accepted combination identifies the candlestick and funding-rate modules, persist the exact binding before opening payload bytes.

No scientific trading rule, universe, window, cost, direction, execution rule, venue, or promotion criterion is changed.
2025 and 2026 remain forbidden.
