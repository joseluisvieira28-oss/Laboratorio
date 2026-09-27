# UPBIT-KRW-LISTING-SHOCK-001 — COMMON CRAWL INDEX AUTHORITY V0.2.5

Date: 2026-09-27
Status: FROZEN BEFORE EXECUTION / INDEX-ONLY / OUTCOME-BLIND

## Purpose

Search Common Crawl URL indices for captures of the exact first-party Upbit announcement API surfaces during 2023-2024, to assess whether an independent public web archive can improve historical list-page coverage.

No Common Crawl WARC payload may be opened in this stage.

## Crawl universe

Retrieve:
`https://index.commoncrawl.org/collinfo.json`

Use every listed crawl whose declared `from`/`to` interval intersects:
2023-01-01T00:00:00Z through 2024-12-31T23:59:59Z.

If collinfo records do not expose from/to, select crawl IDs whose ID year is 2023 or 2024.

No 2025/2026 crawl index is authorized.

## Frozen URL queries per selected crawl

Query:
1. `api-manager.upbit.com/api/v1/announcements*`
2. `api-manager.upbit.com/api/v1/notices*`

Output index metadata only.

Accept status 200 captures only.

## Evidence

Record:
- selected crawl IDs
- per-crawl query HTTP status
- capture counts
- exact URL paths
- distinct original URLs
- page parameter values
- per_page values
- category/thread_name values
- capture timestamp range
- MIME/status counts
- digest counts
- WARC filename/offset/length existence booleans only

Do NOT download any WARC bytes.

Do NOT emit event titles, notice IDs from payloads, published timestamps from payloads, symbols or markets.

Numeric notice IDs embedded in detail URL paths must be redacted in human-readable output; aggregate detail-path counts are allowed.

## Candidate classification

`COMMON_CRAWL_LIST_COVERAGE_CANDIDATE` if at least one selected crawl contains successful captures of an exact list path:
- `/api/v1/announcements`
- or `/api/v1/notices`.

Otherwise:
`COMMON_CRAWL_NO_LIST_COVERAGE`.

Separately report whether list page values beyond page=1 exist.

No source equivalence is implied by index presence.

## Follow-up

Any WARC payload replay requires a separate prospective authority freezing:
- exact capture selection;
- WARC retrieval;
- HTTP payload extraction;
- compression decoding;
- schema equivalence;
- completeness rules.

## Firewalls

No WARC body.
No historical event values.
No Binance.
No title parser.
No source-gate classification.
No OHLCV/returns/PnL.
No strategy changes.
No main merge.
