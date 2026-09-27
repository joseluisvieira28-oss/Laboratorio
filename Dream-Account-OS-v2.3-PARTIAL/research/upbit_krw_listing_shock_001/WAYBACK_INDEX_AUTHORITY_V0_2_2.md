# UPBIT-KRW-LISTING-SHOCK-001 — WAYBACK INDEX AUTHORITY V0.2.2

Date: 2026-09-27
Status: FROZEN BEFORE EXECUTION / INDEX-ONLY / OUTCOME-BLIND

## Trigger

Current first-party Upbit transport remains blocked from the GitHub-hosted research runtime:
- modern announcements API: HTTP 403
- current WWW notice frontend: HTTP 403
- external-announcements first-party root: HTTP 403
- legacy /api/v1/notices routes: HTTP 404

No proxy, authentication or anti-bot circumvention is authorized.

## Purpose

Determine whether the Internet Archive CDX index contains archived captures of the exact first-party Upbit announcement API surfaces during 2023-2024.

This stage reads archive INDEX METADATA ONLY. It does not fetch archived Upbit payload bodies.

## Frozen CDX queries

Query exactly these URL patterns for capture timestamps from 2023-01-01 through 2024-12-31:

1. `api-manager.upbit.com/api/v1/announcements*`
2. `api-manager.upbit.com/api/v1/notices*`

CDX endpoint:
`https://web.archive.org/cdx/search/cdx`

Request output fields only:
- timestamp
- original
- statuscode
- mimetype
- digest
- length

Filters:
- statuscode:200

No archived payload replay in this stage.

## Evidence

Record only:
- query HTTP status
- response bytes / SHA-256
- number of capture rows
- earliest/latest capture timestamp
- distinct original URL count
- distinct digest count
- status/mimetype counts
- whether query parameters are preserved in original URLs
- at most 20 original URL TEMPLATES with numeric/page values redacted.

Do not emit titles, notice IDs, timestamps from Upbit event JSON, or bodies.

## Classification

`WAYBACK_FIRSTPARTY_ARCHIVE_CANDIDATE` if at least one query returns 200-status archive captures within the frozen period for an Upbit announcement-list API URL.

Otherwise:
`WAYBACK_NO_QUALIFYING_ARCHIVE`.

A candidate does not establish source equivalence and does not open historical event values.

## Follow-up requirement

If candidate passes, a separate prospective authority must freeze:
- exact accepted original URL grammar;
- replay URL construction;
- archive timestamp rules;
- de-duplication;
- payload schema equivalence;
- completeness assessment;
- evidence hashing;
- protection against archive-induced event selection bias.

Only then may archived Upbit payloads be opened.

## Firewalls

No archived payload body.
No title/id/listed_at values.
No Binance.
No OHLCV/returns/PnL.
No 2025/2026 market data.
No strategy changes.
No source-minimum changes.
No main merge.
