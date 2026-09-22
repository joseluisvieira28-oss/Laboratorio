# DEFI-LIQUIDATION-SHOCK-001 — DRIFT USER PREFIX INDEX PROBE FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-METADATA ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Source structure authority

Historical Drift v2 records are user-scoped for liquidations:

`user/{accountKey}/liquidationRecords/{year}/{YYYYMMDD}`

The S3 bucket root is:
`https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/`

Program prefix:
`program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/`

## Purpose

Test whether unsigned S3 ListObjectsV2 metadata can enumerate user sub-account prefixes under the Drift v2 program, without downloading any historical object body or event row.

Frozen request:
- prefix = `program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/user/`
- delimiter = `/`
- max-keys = `1000`
- exactly one page only in V0.1
- no continuation token use in V0.1

Persist only:
- HTTP status
- IsTruncated
- KeyCount
- NextContinuationToken presence boolean
- count of CommonPrefixes
- SHA256 of sorted CommonPrefixes
- first/last lexicographic prefix
- no account-level event content

Routing:
- one or more valid user prefixes => `DRIFT_USER_PREFIX_INDEX_PASS`
- successful list with zero prefixes => `DRIFT_USER_PREFIX_INDEX_EMPTY`
- transport/auth/list failure => `DRIFT_USER_PREFIX_INDEX_BLOCKED`
- malformed prefix outside frozen namespace => fail closed

This probe does not establish liquidation availability or event completeness. If PASS and truncated, a separate prospective pagination freeze is required before enumerating the full user universe.

Firewall: object_bodies=false; event_rows=false; prices=false; returns=false; pnl=false; direction=false; protected_2025_2026_market_outcomes=false; credentials=false; account_creation=false; paid_source=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; merge_main=false.
