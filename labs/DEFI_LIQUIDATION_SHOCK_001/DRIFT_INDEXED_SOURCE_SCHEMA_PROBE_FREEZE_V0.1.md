# DEFI-LIQUIDATION-SHOCK-001 — DRIFT INDEXED SOURCE SCHEMA PROBE FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-SCHEMA ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose

Determine whether the official/public Drift Data API exposes a liquidation-history route suitable for source-only historical boundary work, without requesting any liquidation rows or market outcomes.

Authoritative schema target:
- `https://data.api.drift.trade/playground/json`

Allowed read:
- OpenAPI/schema document only.
- Persist only endpoint paths, methods, parameter names/types and authentication metadata for paths whose path/summary/description contains `liquidat`.

Forbidden:
- no liquidation event rows;
- no user/account history queries;
- no prices, marks, oracles, returns, PnL or direction;
- no 2025/2026 protected market outcomes;
- no credentials, account creation or paid access;
- no live trading/orders/wallets/exchange mutation/main merge.

Classification:
- public schema accessible + usable liquidation-history route discovered: `DRIFT_INDEXED_SOURCE_SCHEMA_PASS`
- schema accessible but only account-scoped/non-global routes: `DRIFT_INDEXED_SOURCE_SCHEMA_PARTIAL_ACCOUNT_SCOPED`
- no liquidation route: `DRIFT_INDEXED_SOURCE_SCHEMA_NO_ROUTE`
- transport/auth/schema unavailable: `DRIFT_INDEXED_SOURCE_SCHEMA_BLOCKED`
