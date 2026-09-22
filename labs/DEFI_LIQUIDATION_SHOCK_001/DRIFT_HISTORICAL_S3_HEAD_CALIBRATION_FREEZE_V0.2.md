# DEFI-LIQUIDATION-SHOCK-001 — DRIFT HISTORICAL S3 HEAD CALIBRATION FREEZE V0.2

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-METADATA ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Reason for technical supersession

V0.1 used a dashed daily object key (`YYYY-MM-DD`) and therefore produced 404 even for the known control family `fundingRateRecords`.

A public implementation using the same Drift v2 historical bucket shows the exact daily key pattern as:
`.../fundingRateRecords/{YYYY}/{YYYYMMDD}`

V0.2 changes only the filename formatting from `YYYY-MM-DD` to `YYYYMMDD`. No scientific identity, candidate family, date, symbol, transport, or interpretation changes.

## Frozen HEAD matrix

Bucket root:
`https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/market`

Symbols:
- `BTC-PERP`
- `SOL-PERP`

Dates:
- `2023-08-15` -> key `2023/20230815`
- `2024-01-15` -> key `2024/20240115`

Families:
1. control: `fundingRateRecords`
2. candidate: `liquidationRecords`
3. candidate: `tradeRecords`

Exactly 12 HEAD requests. No suffix variants.

## Adjudication

- control hit required;
- control hit + liquidationRecords hit => `DRIFT_S3_HEAD_LIQUIDATION_ROUTE_PASS`;
- control hit + no liquidationRecords + tradeRecords hit => `DRIFT_S3_HEAD_TRADE_ROUTE_ONLY`;
- control hit + neither candidate => `DRIFT_S3_HEAD_NO_CANDIDATE_ROUTE`;
- no control => `DRIFT_S3_HEAD_CALIBRATION_CONTROL_BLOCKED`.

No GET/object body/event rows/prices/funding values/returns/PnL/direction/protected 2025/2026 outcomes/credentials/accounts/paid source/live trading/orders/wallets/exchange mutation/main merge.
