# DEFI-LIQUIDATION-SHOCK-001 — DRIFT HISTORICAL S3 KEY-SPACE PROBE FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-METADATA ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose

Determine whether the public Drift v2 historical-data S3 bucket exposes a dataset family suitable for liquidation-history indexing, without downloading any historical data object bodies.

Bucket:
`https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com`

Frozen program prefix:
`program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/`

Allowed request:
- unsigned S3 ListObjectsV2-style HTTP GET for this exact prefix with delimiter `/`;
- persist HTTP status, XML metadata, immediate CommonPrefixes and object-key names only;
- if truncated, pagination is NOT authorized in V0.1; stop and classify partial.

Forbidden:
- no GET/HEAD of any historical data object body;
- no market prices, funding values, liquidation rows, returns, PnL, direction, economic outcomes;
- no AWS credentials, requester-pays, account creation, spending, protected 2025/2026 market outcomes.

Routing:
- liquidation-like immediate prefix exists: `DRIFT_HISTORICAL_S3_LIQUIDATION_KEYSPACE_PASS`
- bucket list succeeds but no liquidation-like immediate prefix: `DRIFT_HISTORICAL_S3_KEYSPACE_NO_LIQUIDATION_ROUTE`
- listing truncated before decisive inspection: `DRIFT_HISTORICAL_S3_KEYSPACE_PARTIAL`
- HTTP/auth/transport blocked: `DRIFT_HISTORICAL_S3_KEYSPACE_BLOCKED`

Firewall: prices=false; returns=false; pnl=false; direction=false; event_rows=false; object_bodies=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; merge_main=false.
