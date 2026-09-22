# DEFI-LIQUIDATION-SHOCK-001 — DRIFT HISTORICAL S3 GET STATUS CONTROL FREEZE V0.3

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-TRANSPORT ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Why this is a technical supersession

V0.1 and V0.2 used HTTP HEAD against historical Drift S3 object paths and received 404, including for the documented control family `fundingRateRecords`.

External reproducibility evidence uses ordinary HTTP GET on the same bucket/path grammar:
- `SainyTK/funding-arb-analysis`, commit `62899f887d197f170244e8116312951132429407`, file `modules/exchanges/drift.py`
- historical Drift documentation mirror `wdotsol/docs`, commit `42efa7e7bbd37041a7b6be1f60daedd17c743dd6`, file `docs/extra/_historicaldata.md`

Those sources independently agree on:
- prefix: `https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`
- market funding: `market/{marketSymbol}/fundingRateRecords/{year}/{YYYYMMDD}`
- market trades: `market/{marketSymbol}/tradeRecords/{year}/{YYYYMMDD}`
- user liquidations: `user/{accountKey}/liquidationRecords/{year}/{YYYYMMDD}`

Critical source correction:
`liquidationRecords` is USER-SCOPED, not MARKET-SCOPED. Prior market-path liquidation probes are invalid for route-existence adjudication and remain preserved only as technical history.

## Frozen V0.3 control URLs

GET-status-only, no body parsing:
1. `.../market/SOL-PERP/tradeRecords/2024/20240101`
   - exact documented example path.
2. `.../market/SOL-PERP/fundingRateRecords/2024/20240101`
   - same documented grammar/control family.
3. `.../market/BTC-PERP/fundingRateRecords/2023/20230801`
   - independent academic-code control during the published Aug-2023 onward collection window.

## Allowed behavior

For each frozen URL:
- issue HTTP GET;
- do NOT call response.read() or otherwise consume body bytes;
- persist only HTTP status and response headers: Content-Length, Content-Type, ETag, Last-Modified, Accept-Ranges, Content-Encoding;
- close response immediately.

No `liquidationRecords` object is queried in V0.3 because no authoritative liquidated user `accountKey` has yet been frozen.

## Adjudication

- >=1 exact documented control GET returns 200/206: `DRIFT_S3_GET_STATUS_CONTROL_PASS`
- all exact documented controls 404: `DRIFT_S3_GET_STATUS_CONTROL_NOT_FOUND`
- transport/auth failure: `DRIFT_S3_GET_STATUS_CONTROL_BLOCKED`
- body bytes consumed or unexpected redirect/domain: fail closed.

## Firewall

response_body_bytes_read=0; event_rows=false; prices=false; funding_values=false; returns=false; pnl=false; direction=false; economic_outcomes=false; protected_2025_2026_market_outcomes=false; credentials=false; account_creation=false; paid_source=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; merge_main=false.
