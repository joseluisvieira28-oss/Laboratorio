# DEFI-LIQUIDATION-SHOCK-001 — DRIFT DATA API SCHEMA TRANSPORT REMEDIATION FREEZE V0.2

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-SCHEMA ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Parent blocker

Prior schema probe classification:
`DRIFT_INDEXED_SOURCE_SCHEMA_BLOCKED`

Prior target:
`https://data.api.drift.trade/playground/json`

Prior reason:
`URLError`

This V0.2 is a pure transport remediation. The scientific question and allowed information are unchanged.

## Purpose

Determine whether the official Drift Data API OpenAPI/schema document is accessible through a transport different from Python urllib, and if accessible enumerate liquidation-related API route metadata only.

## Frozen transport sequence

1. `curl -4` GET exact schema URL with TLS verification enabled.
2. If IPv4 fails, `curl` default-stack GET exact schema URL.
3. No alternate host and no credential.
4. Maximum downloaded schema bytes: 25 MiB.
5. Redirects may be followed only within `drift.trade` subdomains; otherwise fail closed.

## Allowed content

OpenAPI/schema document only.

Persist only:
- transport used;
- HTTP status/final host;
- schema SHA256/byte count;
- title/version when present;
- route paths/methods whose path, summary, description, tags, or operationId contain `liquidat`;
- parameter names, locations, required flags, primitive schema types/formats;
- route-level security metadata.

Do NOT call any discovered route in this mission.

## Classification

- schema accessible + at least one liquidation-related route: `DRIFT_DATA_API_SCHEMA_LIQUIDATION_ROUTE_PASS`
- schema accessible + zero liquidation-related routes: `DRIFT_DATA_API_SCHEMA_NO_LIQUIDATION_ROUTE`
- schema accessible but malformed/uninterpretable: `DRIFT_DATA_API_SCHEMA_FAIL_CLOSED`
- both allowed transports fail: `DRIFT_DATA_API_SCHEMA_TRANSPORT_BLOCKED`

A route PASS is source-route feasibility only. It is not historical coverage PASS and not economic evidence.

## Firewall

event_rows=false; liquidation_rows=false; prices=false; funding_values=false; returns=false; pnl=false; direction=false; protected_2025_2026_market_outcomes=false; credentials=false; account_creation=false; paid_source=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; merge_main=false.
