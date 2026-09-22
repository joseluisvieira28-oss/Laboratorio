# DEFI-LIQUIDATION-SHOCK-001 — DRIFT HISTORICAL S3 HEAD CALIBRATION FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-METADATA ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose

Calibrate exact object-key existence in the public Drift v2 historical-data bucket using HTTP HEAD only. No historical object body may be downloaded.

Bucket root:
`https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/market/`

External published evidence identifies the v2 funding path family:
`market/:symbol/fundingRateRecords/:year/:year:month:day`

## Prospectively frozen HEAD matrix

Symbols:
- `BTC-PERP`
- `SOL-PERP`

Dates selected without viewing object results:
- `2023-08-15`
- `2024-01-15`

Families:
1. control: `fundingRateRecords`
2. candidate from SDK event nomenclature: `liquidationRecords`
3. candidate from historical record nomenclature: `tradeRecords`

Filename suffixes:
- no suffix
- `.csv`

Exactly 2 symbols × 2 dates × 3 families × 2 suffixes = 24 HEAD requests maximum.

## Adjudication

- At least one control fundingRateRecords HEAD 200 is required before candidate-family results are interpretable.
- control absent/blocked => `DRIFT_S3_HEAD_CALIBRATION_CONTROL_BLOCKED`
- control PASS + liquidationRecords exists => `DRIFT_S3_HEAD_LIQUIDATION_ROUTE_PASS`
- control PASS + no liquidationRecords but tradeRecords exists => `DRIFT_S3_HEAD_TRADE_ROUTE_ONLY`
- control PASS + neither candidate exists => `DRIFT_S3_HEAD_NO_CANDIDATE_ROUTE`
- inconsistent HTTP/schema behavior => fail closed.

No GET, Range GET, object body, liquidation event row, price, funding value, return, PnL, direction, protected 2025/2026 outcome, credential, account, paid source, live trading, order, wallet, exchange mutation or main merge is authorized.
