# UPBIT-KRW-LISTING-SHOCK-001 — COMMON CRAWL RAW INDEX RANGE IMPLEMENTATION V0.2.5D1

Date: 2026-09-27
Parent authority: COMMON_CRAWL_RAW_INDEX_CENSUS_AUTHORITY_V0_2_5D
Status: FROZEN BEFORE 15-CRAWL CENSUS EXECUTION / TRANSPORT-ONLY

## Trigger evidence

V0.2.5C proved:
- raw `cluster.idx` transport PASS;
- the Common Crawl secondary index is lexicographically ordered;
- Common Crawl primary CDX shards are technically accessible.

The official ZipNum secondary-index format is:
`urlkey, part, offset, length, lineno`.

Therefore full-shard download is unnecessary and wasteful.

## Permitted implementation

For each frozen crawl:

1. Download exact `cluster.idx`.
2. Parse each line as:
   - urlkey
   - part
   - offset
   - length
   - optional lineno
3. Validate:
   - >=4 fields;
   - offset integer >=0;
   - length integer >0;
   - part matches `cdx-XXXXX.gz`;
   - urlkeys non-decreasing.
4. Define target prefix:
   `com,upbit,api-manager)/`
5. Define upper bound as the smallest lexical range strictly after all strings beginning with the target prefix.
6. Using binary search over secondary-index urlkeys, select:
   - the greatest block-start key <= target prefix;
   - every following block whose block-start key remains within the target-prefix range.
7. Maximum selected compressed blocks per crawl: 20.
8. Request each exact primary-index byte range:
   `Range: bytes={offset}-{offset+length-1}`
9. Require HTTP 206 or an HTTP 200 body whose byte count equals the requested range length.
10. SHA-256 every returned compressed block.
11. Decompress each block as gzip and parse CDXJ lines.
12. Apply the unchanged exact host/path filters from V0.2.5D.

No full WARC or archived page payload is opened.

## Resource caps

Supersedes only the full-shard transport accounting in V0.2.5D:

- <=20 compressed ZipNum blocks per crawl;
- <=300 total blocks across 15 crawls;
- <=1 GiB total compressed range bytes;
- <=10,000 matched CDXJ rows;
- timeout <=120 minutes.

The crawl universe, SURT target, path filters, classifications and scientific firewalls remain unchanged.

## Evidence

Instead of full-shard SHA:
- selected part names;
- exact byte offsets/lengths;
- compressed block SHA-256;
- per-crawl and aggregate compressed range bytes.

All other V0.2.5D evidence/classification rules remain unchanged.

## Scientific effect

None.

This is a deterministic transport optimization using the official ZipNum random-access fields already present in `cluster.idx`.

No source/event/outcome rule changes.
