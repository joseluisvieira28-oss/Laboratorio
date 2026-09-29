# ETH-STAKING-FLOW-001 — XATU HTTP TRANSPORT PROBE V0.2B

Date: 2026-09-18
Branch: `eth-staking-flow-v0.1`
Status: **FROZEN BEFORE EXECUTION / SOURCE-ONLY / OUTCOME-BLIND**

## Why this probe exists

V0.2A corrected the Xatu table partition shape to hourly `YYYY/M/D/H.parquet`, but its runner failed before the first date was probed while initializing the DuckDB HTTP extension. The resulting receipt contained zero date probes.

Therefore V0.2A is classified as a technical runtime failure and does not adjudicate Xatu object availability.

## Exact source and objects

Table:
`canonical_beacon_validators`

Network/database:
`mainnet/default`

Exact four objects:
- `.../2023/4/12/0.parquet`
- `.../2023/9/1/0.parquet`
- `.../2024/6/15/0.parquet`
- `.../2024/12/31/0.parquet`

No alternate date, hour, table, network, mirror or protected-period object may be queried.

## Allowed transport request

For each exact URL:
- HTTP GET with `Range: bytes=0-3`;
- record status, Content-Length, Content-Range, ETag, Last-Modified and returned prefix bytes;
- close the response immediately.

Expected Parquet magic prefix when body bytes are returned: `PAR1`.

No Parquet rows or columns may be opened in V0.2B.

## PASS

`XATU_HTTP_TRANSPORT_PASS` requires all four exact URLs to return HTTP 200 or 206 and, when at least four body bytes are provided, the first four bytes must be `PAR1`.

## Terminal states

- XATU_HTTP_TRANSPORT_PASS
- XATU_SOURCE_PATH_NOT_FOUND
- XATU_HTTP_PROVENANCE_FAILURE
- XATU_SOURCE_ACQUISITION_TECHNICAL_FAILURE

None is an economic verdict.

## Firewalls

No validator values, queue counts, ETH/BTC prices, returns, PnL, 2025/2026 access, trading, wallets, exchange mutation, alerts/webhooks or merge to main.
