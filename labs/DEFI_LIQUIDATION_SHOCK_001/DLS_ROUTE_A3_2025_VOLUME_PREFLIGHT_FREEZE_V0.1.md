# DLS ROUTE A3 — 2025 VOLUME PREFLIGHT FREEZE V0.1

Date: 2026-10-02
Status: FROZEN SOURCE-TRANSPORT PREFLIGHT

Prerequisite: Route A3 gTFA equivalence run 36969189081 = PASS.

Purpose: measure only the number of successful 2025 transactions referencing each frozen program before any full-payload backfill.

Exact window: 2025-01-01T00:00:00Z through 2025-12-31T23:59:59Z.
Programs: existing Marginfi, Solend, Kamino IDs only.
Method: getTransactionsForAddress, transactionDetails=signatures, sortOrder=asc, limit=1000, exact blockTime filter, status=succeeded.
Follow paginationToken to null. Maximum 100 pages per program. Repeated/nonadvancing token, schema error, transport exhaustion, or page ceiling is BLOCKED.

This preflight may count transport rows only. It may not decode events, prices, returns, PnL, amounts, oracle values, or 2026 data.
It changes no scientific rule.
