# DEFI-LIQUIDATION-SHOCK-001 — DRIFT S3 RANGE CONTROL PROBE FREEZE V0.3

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-TRANSPORT ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose

Resolve whether the Drift historical S3 control path is still retrievable when HTTP HEAD returns 404, without reading or interpreting historical funding values.

Authoritative control path shape from public Drift-data consumer code:
`program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/market/{MARKET}/fundingRateRecords/{YYYY}/{YYYYMMDD}`

Bucket:
`https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com`

## Frozen matrix

Markets:
- BTC-PERP
- SOL-PERP

Dates:
- 2023-08-15
- 2023-09-15
- 2024-01-15
- 2024-04-01

Exactly 8 requests maximum.

## Transport rule

For each exact control URL:
- send unsigned HTTP GET with `Range: bytes=0-0`;
- do not parse, print, persist, decode, or interpret the returned byte;
- immediately discard response body;
- persist only HTTP status and response metadata headers (Content-Range, Content-Length, Content-Type, ETag, Last-Modified);
- no redirects to unrelated hosts;
- no credentials.

## Adjudication

- any 206/200 control response => `DRIFT_S3_RANGE_CONTROL_PASS`
- all exact controls 404 => `DRIFT_S3_RANGE_CONTROL_PATH_OR_AVAILABILITY_BLOCKED`
- auth/requester-pays/403 => `DRIFT_S3_RANGE_CONTROL_ACCESS_BLOCKED`
- transport/schema inconsistency => fail closed.

A PASS validates transport/path existence only. It does NOT authorize downloading historical funding values, liquidation rows, prices, returns, PnL or direction. A BLOCKED result is not NO_EDGE.

Firewall: body_bytes_interpreted=0; funding_values=false; liquidation_rows=false; prices=false; returns=false; pnl=false; direction=false; protected_2025_2026_market_outcomes=false; credentials=false; account_creation=false; paid_source=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; merge_main=false.
