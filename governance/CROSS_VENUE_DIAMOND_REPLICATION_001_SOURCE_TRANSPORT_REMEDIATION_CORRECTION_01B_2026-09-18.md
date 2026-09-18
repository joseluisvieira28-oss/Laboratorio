# CROSS-VENUE-DIAMOND-REPLICATION-001 — SOURCE TRANSPORT REMEDIATION CORRECTION 01B — 2026-09-18

Status: FROZEN_BEFORE_NUMERIC_MODULE_DIAGNOSTIC_AND_BEFORE_ANY_SIGNAL_OR OUTCOME CALCULATION
Supersedes the module-enum restriction in Correction 01A.

New authoritative evidence:
The current official OKX API changelog records, under Historical Market Data, that module `11` (Borrowing rate) was added to the request parameter `module` for GET / Get historical market data. This establishes that the server-side module enum is numeric even though the Python SDK wrapper accepts an unvalidated generic string.

Therefore:
- bounded metadata-only enumeration of module values 1..10 is authorized;
- this restores the original Amendment-01 discovery method;
- only provider response codes/messages and archive metadata may be inspected;
- archive payload bytes remain forbidden;
- signals, returns, PnL and outcomes remain forbidden;
- after identifying candlestick/funding modules, exact values must be persisted before any payload is opened.

All parent candidate, symbol, period, execution, cost and governance rules remain unchanged.
