# UPBIT-KRW-LISTING-SHOCK-001 — COMMON CRAWL URL INDEX TRANSPORT AUTHORITY V0.2.5B

Date: 2026-09-27
Branch: `upbit-krw-listing-shock-commoncrawl-urlindex-v0.2.5b`
Status: FROZEN BEFORE EXECUTION / INDEX-ONLY / OUTCOME-BLIND

## Trigger

V0.2.5A proved that the historical Common Crawl CDX API route used by the prior runner currently returns HTTP 404 for all 30 frozen 2023-2024 queries.

Common Crawl separately publishes the same URL index in a public columnar Parquet table:

`s3://commoncrawl/cc-index/table/cc-main/warc/`

The official schema is partitioned by:
- `crawl`
- `subset`

and contains index metadata fields including:
- url
- url_host_name
- url_path
- url_query
- fetch_time
- fetch_status
- content_digest
- warc_filename
- warc_record_offset
- warc_record_length

No WARC payload is authorized.

## Purpose

Determine whether the public columnar URL Index is technically queryable from the research runtime and whether one frozen 2024 control crawl contains any index rows for the exact first-party Upbit API host.

This is transport/schema only. It does not adjudicate historical coverage.

## Frozen control crawl

Exactly:
`CC-MAIN-2024-10`

Partition:
- crawl = CC-MAIN-2024-10
- subset = warc

No other crawl may be opened in V0.2.5B.

## Frozen host/path filter

Host:
`api-manager.upbit.com`

Retain only rows whose path:
- equals `/api/v1/announcements`;
- starts with `/api/v1/announcements/`;
- equals `/api/v1/notices`;
- starts with `/api/v1/notices/`.

This stage may record URL index metadata only.

## Transport method

1. List the public S3 partition anonymously using `--no-sign-request`.
2. Retain only `.parquet` objects under the exact frozen partition.
3. Query the Parquet objects with a columnar engine capable of predicate pushdown.
4. HTTP/S3 access remains unauthenticated and public.
5. No AWS credentials or requester-pays authority is required or permitted.

Resource cap:
- one frozen crawl only;
- no WARC bytes;
- maximum 500 matched index rows retained;
- stop fail-closed if local temporary storage exceeds 4 GiB;
- stop fail-closed if the query cannot complete within the workflow timeout.

## Evidence

Record only:
- S3 listing HTTP/tool success;
- exact Parquet object count;
- aggregate listed Parquet bytes;
- engine/version;
- matched index-row count capped at 500;
- path-family counts (exact list / numeric-or-other detail);
- HTTP fetch-status counts;
- earliest/latest Common Crawl fetch_time;
- distinct original URL count;
- presence of WARC locator fields;
- query/result SHA-256;
- transport/runtime errors.

For human-readable output, numeric notice IDs in paths/URLs must be redacted.

This stage may retain exact raw URL metadata only inside the private workflow artifact for technical auditing. It must not open any WARC payload body.

## Classification

- `COMMON_CRAWL_URL_INDEX_TRANSPORT_PASS` if the exact partition is publicly listable, the Parquet schema is readable, and a host/path-filter query completes deterministically (zero matched rows is allowed for this transport PASS).
- `COMMON_CRAWL_URL_INDEX_TRANSPORT_FAILURE` otherwise.

A transport PASS does not establish source coverage and does not authorize WARC replay.

## Follow-up

Only after transport PASS may a separate prospective V0.2.5C authority enumerate the frozen 15 crawl partitions and adjudicate archive index coverage.

## Firewalls

No WARC payload.
No event title/body.
No Upbit event timestamp extraction from payload.
No title parser.
No source-gate event qualification.
No Binance.
No OHLCV/returns/PnL.
No 2025/2026 market data.
No strategy changes.
No source-minimum changes.
No main merge.
No post-outcome tuning.
