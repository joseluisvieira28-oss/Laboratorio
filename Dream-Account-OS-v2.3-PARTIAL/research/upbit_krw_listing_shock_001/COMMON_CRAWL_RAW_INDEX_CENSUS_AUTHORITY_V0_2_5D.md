# UPBIT-KRW-LISTING-SHOCK-001 — COMMON CRAWL RAW INDEX CENSUS AUTHORITY V0.2.5D

Date: 2026-09-27
Branch: `upbit-krw-listing-shock-commoncrawl-census-v0.2.5d`
Status: FROZEN BEFORE V0.2.5C TERMINAL RESULT / INDEX-ONLY / OUTCOME-BLIND

## Trigger gate

This census may execute only if V0.2.5C terminal receipt states:

`COMMON_CRAWL_RAW_INDEX_TRANSPORT_PASS`

Any other V0.2.5C classification keeps V0.2.5D CLOSED.

## Purpose

If raw-CDX transport is proven, enumerate index metadata for the same frozen 2023-2024 Common Crawl universe used by V0.2.5/V0.2.5A and determine whether Common Crawl contains useful first-party Upbit API captures.

No WARC response body is authorized.

## Frozen crawls

Exactly:

2023:
- CC-MAIN-2023-06
- CC-MAIN-2023-14
- CC-MAIN-2023-23
- CC-MAIN-2023-40
- CC-MAIN-2023-50

2024:
- CC-MAIN-2024-10
- CC-MAIN-2024-18
- CC-MAIN-2024-22
- CC-MAIN-2024-26
- CC-MAIN-2024-30
- CC-MAIN-2024-33
- CC-MAIN-2024-38
- CC-MAIN-2024-42
- CC-MAIN-2024-46
- CC-MAIN-2024-51

No 2025/2026 crawl.

## Frozen source/selection

For each crawl:
- fetch exact `cluster.idx`;
- use the exact deterministic V0.2.5C SURT/shard-selection algorithm;
- target host SURT `com,upbit,api-manager)/`;
- maximum 6 CDX primary shards per crawl;
- retain only exact host `api-manager.upbit.com`;
- retain only:
  - /api/v1/announcements
  - /api/v1/announcements/*
  - /api/v1/notices
  - /api/v1/notices/*

No other host/path.

## Resource caps

- <= 6 selected CDX shards per crawl;
- <= 4 GiB total compressed bytes across all crawls;
- <= 10,000 matched index rows total;
- timeout <= 120 minutes;
- fail closed on any crawl whose cluster/shard transport cannot be deterministically audited.

No manual crawl/shard rescue.

## Evidence

For each crawl and aggregate:
- cluster.idx SHA-256 / row count;
- selected shard names and hashes;
- compressed byte totals;
- matched row count;
- exact-list and detail path counts by family;
- fetch-status counts;
- earliest/latest capture timestamp;
- distinct original URL count;
- WARC-locator-complete count.

Aggregate separately for:
- MODERN announcements family;
- LEGACY notices family;
- 2023;
- 2024.

Human-visible numeric IDs redacted.

## Index-census classifications

`COMMON_CRAWL_MODERN_2023_CANDIDATE` if at least one 2023 crawl contains an HTTP-success capture of exact modern list path `/api/v1/announcements`.

`COMMON_CRAWL_ARCHIVE_CANDIDATE` if no modern-2023 candidate exists but any frozen crawl contains an HTTP-success exact list capture in either family.

`COMMON_CRAWL_NO_EXACT_LIST_CAPTURE` only if all 15 crawl index audits complete successfully and no HTTP-success exact list capture exists.

`COMMON_CRAWL_CENSUS_TECHNICAL_FAILURE` if any required crawl cannot be deterministically audited under the caps.

These are index-coverage classifications only. None implies source equivalence or SOURCE_DATA_PASS.

## Follow-up requirements

Any WARC payload replay requires a separate prospective authority freezing:
- exact captures selected;
- HTTP payload extraction;
- decompression;
- schema;
- de-duplication;
- completeness;
- archive-selection-bias controls.

Historical event enumeration remains CLOSED.

## Firewalls

No WARC payload/body.
No event titles/bodies.
No event payload timestamps.
No frozen title parser.
No qualified-event count.
No Binance.
No OHLCV/returns/PnL.
No 2025/2026 market data.
No strategy changes.
No source-minimum changes.
No main merge.
No post-outcome tuning.
