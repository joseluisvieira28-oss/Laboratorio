# UPBIT-KRW-LISTING-SHOCK-001 — WAYBACK NUMERIC DETAIL CENSUS AUTHORITY V0.2.8

Date: 2026-09-27
Status: FROZEN BEFORE EXECUTION / INDEX-ONLY / OUTCOME-BLIND

## Purpose

Test one final source-recovery route without opening titles, announcement payloads, Binance data, or outcomes.

The Internet Archive CDX index is queried for numeric first-party Upbit detail URLs:

- `/api/v1/notices/{ID}`
- `/api/v1/announcements/{ID}`

during 2023-01-01 through 2024-12-31.

The question is whether archived numeric detail IDs are sufficiently continuous to support a complete first-party event census independently of sparse archived list pages.

## Frozen CDX queries

Exactly:

1. `api-manager.upbit.com/api/v1/notices/*`
2. `api-manager.upbit.com/api/v1/announcements/*`

Parameters:
- output=json
- from=2023
- to=2024
- filter=statuscode:200
- fields=timestamp,original,statuscode,mimetype,digest,length
- limit=20000

No archive payload replay in this stage.

## Accepted URL grammar

A row is accepted only if the original URL path matches exactly:

- `^/api/v1/notices/[0-9]+$`
- `^/api/v1/announcements/[0-9]+$`

Query parameters on detail URLs are ignored only for URL identity after the exact numeric path passes.

## Per-family index metrics

Record:
- accepted capture count
- distinct numeric ID count
- min/max numeric ID
- numeric span size = max_id - min_id + 1
- numeric coverage fraction = distinct_id_count / span_size
- missing numeric ID count within min..max
- maximum internal numeric-ID gap
- earliest/latest archive capture
- distinct digest count
- status/mimetype counts

Do not emit the ID list itself.

## Completeness candidate gate

A family may be classified `NUMERIC_DETAIL_CENSUS_CANDIDATE` only if ALL are true:

1. distinct numeric detail IDs >= 100
2. numeric coverage fraction == 1.0
3. missing IDs within min..max == 0
4. max internal gap <= 1
5. earliest archive capture <= 2023-01-07T23:59:59Z
6. latest archive capture >= 2024-12-25T00:00:00Z
7. all accepted rows are HTTP 200 index rows
8. no transport/index parsing failure

These gates are intentionally strict because partial archive coverage may not define an unbiased event universe.

If neither family passes:
`WAYBACK_NUMERIC_DETAIL_COVERAGE_INSUFFICIENT`.

If one passes:
`WAYBACK_NUMERIC_DETAIL_CENSUS_CANDIDATE`.

A candidate still does NOT open event values. A separate authority would be required before payload replay and title parsing.

## Firewalls

No archived payload replay.
No title / notice body / event timestamp values.
No Binance archives.
No OHLCV.
No returns/PnL.
No 2025/2026 market outcomes.
No source-minimum changes.
No title-parser changes.
No strategy changes.
No main merge.
