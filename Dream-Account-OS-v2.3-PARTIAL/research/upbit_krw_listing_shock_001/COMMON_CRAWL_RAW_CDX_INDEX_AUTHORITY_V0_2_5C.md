# UPBIT-KRW-LISTING-SHOCK-001 — COMMON CRAWL RAW CDX INDEX AUTHORITY V0.2.5C

Date: 2026-09-27
Branch: `upbit-krw-listing-shock-commoncrawl-rawindex-v0.2.5c`
Status: FROZEN BEFORE EXECUTION / INDEX-ONLY / OUTCOME-BLIND

## Trigger

The legacy Common Crawl CDX API route currently returns HTTP 404 for the frozen historical queries, and the public URL Index Parquet S3 partition could not be anonymously listed from the research runtime.

Common Crawl also publishes the underlying raw CDXJ ZipNum URL index over HTTPS under:

`https://data.commoncrawl.org/cc-index/collections/{CRAWL}/indexes/`

The official raw index consists of:
- a sorted secondary index `cluster.idx`;
- sharded gzip primary index files `cdx-*.gz`.

No WARC payload is authorized.

## Purpose

Determine whether the raw Common Crawl URL Index is technically accessible and whether one frozen 2024 control crawl contains URL-index metadata for the exact first-party Upbit API host.

This stage is transport/schema/index-only. It does not adjudicate 2023-2024 completeness.

## Frozen control crawl

Exactly:
`CC-MAIN-2024-10`

No other crawl may be opened in V0.2.5C.

## Frozen URL-index source

Secondary index:
`https://data.commoncrawl.org/cc-index/collections/CC-MAIN-2024-10/indexes/cluster.idx`

Primary shards:
`https://data.commoncrawl.org/cc-index/collections/CC-MAIN-2024-10/indexes/cdx-XXXXX.gz`

Only shard names obtained from the frozen `cluster.idx` may be requested.

## Frozen SURT target

Host SURT prefix:
`com,upbit,api-manager)/`

Retain only CDXJ rows whose original URL host is exactly:
`api-manager.upbit.com`

and whose path:
- equals `/api/v1/announcements`;
- starts with `/api/v1/announcements/`;
- equals `/api/v1/notices`;
- starts with `/api/v1/notices/`.

No other Upbit hostname or path may be added after execution begins.

## Deterministic shard selection

1. Download the complete `cluster.idx`.
2. Parse every non-empty secondary-index row.
3. Validate lexicographic SURT ordering.
4. Determine all primary shard filenames associated with secondary-index keys beginning with the target host SURT prefix.
5. Additionally include the primary shard associated with the greatest secondary-index key strictly less than the target host prefix, if distinct, because the target range may begin inside that indexed block.
6. Additionally include the primary shard associated with the first secondary-index key strictly greater than all keys beginning with the target prefix, if distinct, because the target range may end inside that indexed block.
7. Sort/dedupe selected shard names.
8. Fail closed if more than 6 unique primary shards are selected.

No manual shard selection after observing data.

## Primary-index parsing

For each selected `cdx-*.gz`:
- download exact bytes;
- record SHA-256 and compressed byte length;
- decompress as concatenated gzip members using standard gzip support;
- parse line-by-line as CDXJ:
  `SURT_KEY TIMESTAMP JSON_METADATA`;
- accept only exact target-host/path rows;
- retain index metadata only.

Maximum:
- 6 primary shards;
- 1 GiB total compressed download;
- 2,000 matched index rows retained;
- workflow timeout 30 minutes.

## Evidence

Record:
- cluster.idx HTTP status / bytes / SHA-256;
- secondary-index row count;
- ordering validation;
- selected shard count/names;
- per-shard compressed bytes and SHA-256;
- total compressed bytes;
- matched index-row count;
- exact-list vs detail path counts;
- fetch/status counts;
- earliest/latest crawl timestamp;
- distinct original URL count;
- presence of WARC locator metadata;
- deterministic SHA-256 of retained index rows.

For human-visible output:
- numeric notice IDs in URLs/paths must be redacted.

Exact URLs/index metadata may exist only in the private workflow artifact for auditability.

## Classification

- `COMMON_CRAWL_RAW_INDEX_TRANSPORT_PASS` if cluster.idx and selected CDX shard(s) are technically accessible and parse deterministically. Zero matching rows is permitted for transport PASS.
- `COMMON_CRAWL_RAW_INDEX_TRANSPORT_FAILURE` otherwise.

This stage does not establish source coverage.

## Follow-up

Only after transport PASS may a separate prospective authority scan the frozen 15 Common Crawl 2023-2024 crawls and adjudicate list/detail capture coverage.

Any WARC payload replay requires another prospective authority.

## Firewalls

No WARC payload.
No archived HTTP response body.
No event title/body.
No event timestamp extraction from payloads.
No title parser.
No source-gate event qualification.
No Binance.
No OHLCV.
No returns/PnL.
No 2025/2026 market data.
No strategy changes.
No source-minimum changes.
No main merge.
No post-outcome tuning.
