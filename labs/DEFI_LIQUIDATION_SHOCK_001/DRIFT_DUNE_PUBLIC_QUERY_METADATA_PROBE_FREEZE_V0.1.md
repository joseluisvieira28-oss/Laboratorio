# DEFI-LIQUIDATION-SHOCK-001 — DRIFT DUNE PUBLIC QUERY METADATA PROBE FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-METADATA ONLY / OUTCOME-BLIND / FAIL-CLOSED

Purpose: determine whether public Dune query pages identified by title expose reproducible SQL/source metadata for Drift liquidation instruction indexing, without executing any query or reading result rows.

Frozen public query pages:
- 4226524 — DRIFT - liquidation - borrowForPerpPnl
- 2680764 — drift liquidateSpot
- 3739506 — Drift V2 - Liquidation Txs V3

Allowed:
- unauthenticated GET of the three public query pages only;
- inspect HTML/embedded JSON for title, query ID, SQL text or SQL-bearing metadata;
- persist page SHA256, byte count, HTTP status and any SQL/source metadata found.

Forbidden:
- no Dune query execution;
- no API key;
- no result endpoint;
- no result rows;
- no prices, returns, PnL, direction or economic outcomes;
- no account creation or paid access.

Classification:
- SQL/source metadata recovered for at least one relevant frozen class: DRIFT_DUNE_PUBLIC_QUERY_METADATA_PASS
- pages reachable but SQL not public in page payload: DRIFT_DUNE_PUBLIC_QUERY_METADATA_NO_SQL
- transport/auth failure: DRIFT_DUNE_PUBLIC_QUERY_METADATA_BLOCKED
- malformed/inconsistent payload: fail closed.

A PASS is only source-index feasibility. Every eventual candidate signature still requires official Solana RAW verification.

Firewall: query_execution=false; result_rows=false; prices=false; returns=false; pnl=false; direction=false; protected_2025_2026_market_outcomes=false; credentials=false; account_creation=false; paid_source=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; merge_main=false.
