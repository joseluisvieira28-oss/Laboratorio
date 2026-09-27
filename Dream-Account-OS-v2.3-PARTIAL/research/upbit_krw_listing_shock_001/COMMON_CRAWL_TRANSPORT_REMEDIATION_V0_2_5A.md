# UPBIT-KRW-LISTING-SHOCK-001 — COMMON CRAWL TRANSPORT REMEDIATION V0.2.5A

Date: 2026-09-27
Branch: `upbit-krw-listing-shock-commoncrawl-transport-v0.2.5a`
Status: FROZEN BEFORE EXECUTION / INDEX-ONLY / OUTCOME-BLIND

## Trigger

V0.2.5 emitted:
- selected crawls = 15
- frozen queries = 30
- query_successes = 0
- exact list captures = 0
- classification = COMMON_CRAWL_NO_LIST_COVERAGE

A zero-success index transport result cannot distinguish true zero coverage from index transport failure.

## Purpose

Repeat the exact same Common Crawl index query universe and correct only the terminal classification semantics.

No WARC payload may be opened.

## Frozen crawl universe

Same V0.2.5 rule:
- use collinfo.json;
- select 2023 and 2024 crawl IDs only / crawls intersecting the 2023-2024 interval.

## Frozen URL queries

For every selected crawl, query exactly:
1. `https://api-manager.upbit.com/api/v1/announcements` with `matchType=prefix`
2. `https://api-manager.upbit.com/api/v1/notices` with `matchType=prefix`

Output JSON index metadata only.

No query grammar change after execution begins.

## Transport

Ordinary unauthenticated HTTPS only.

For each index query:
- timeout 90 seconds;
- max 4 attempts;
- retry only 408, 425, 429, 500, 502, 503, 504 and transport timeout;
- deterministic backoff 2, 4, 8 seconds.

Record:
- HTTP status;
- body bytes;
- body SHA-256;
- transport error;
- parsed index-row count;
- status-200 capture-row count.

No WARC body.
No event payload.

## Terminal classification

- `COMMON_CRAWL_INDEX_TRANSPORT_FAILURE` if zero frozen queries return HTTP 200.
- `COMMON_CRAWL_LIST_COVERAGE_CANDIDATE` if at least one HTTP-200 query contains an exact list-path capture:
  - `/api/v1/announcements`
  - or `/api/v1/notices`
- `COMMON_CRAWL_NO_LIST_COVERAGE` only if at least one frozen query returns HTTP 200 and zero exact list-path captures exist across all successful queries.

## Evidence

Same aggregate index metadata as V0.2.5 plus:
- HTTP-status counts;
- successful-query count;
- technical-failure-query count.

No notice payload values.
No title/ID/timestamp payload values.
No Binance.
No outcomes.

## Firewalls

Index-only.
No WARC payload.
No historical event enumeration.
No title parser.
No source-gate qualification.
No Binance.
No OHLCV/returns/PnL.
No strategy changes.
No main merge.
