# UPBIT-KRW-LISTING-SHOCK-001 — WAYBACK SCHEMA EQUIVALENCE AUTHORITY V0.2.3

Date: 2026-09-27
Status: FROZEN BEFORE ARCHIVED PAYLOAD REPLAY / SOURCE-ONLY / OUTCOME-BLIND

## Parent evidence

Wayback index run 36321378859:
- 108 qualifying HTTP-200 JSON captures in 2023-2024
- 60 modern `/api/v1/announcements*` captures
- 48 legacy `/api/v1/notices*` captures
- list URLs with preserved query parameters are present
- no archived payload body was opened in V0.2.2

## Purpose

Determine:
1. exact archived LIST URL/page coverage;
2. whether archived first-party Upbit list payload schemas can be mapped to the frozen event contract without changing event semantics.

No historical event enumeration or Binance access is authorized in this stage.

## Frozen CDX scope

Query the same two patterns and 2023-2024 window as V0.2.2.

Retain only list endpoints whose path is exactly:
- `/api/v1/announcements`
- `/api/v1/notices`

Exclude:
- detail URLs with numeric path suffix;
- `latest`;
- `news`;
- any other path.

Record exact original list URLs, capture timestamps and CDX digests because these are transport/archive metadata, not event values.

## Deterministic schema-sample selection

For each family independently:
- sort qualifying list captures by `(timestamp, original, digest)`;
- choose the earliest qualifying capture;
- choose the latest qualifying capture if distinct.

Maximum archived payload replays: 4.

Replay URL:
`https://web.archive.org/web/{CAPTURE_TIMESTAMP}id_/{ORIGINAL_URL}`

No other payload may be opened in this stage.

## Allowed extraction from archived list payload

Schema/metadata only:
- HTTP status, bytes, SHA-256
- JSON top-level type/keys
- row-array path
- row count
- row field names from up to first 3 rows
- presence of semantic fields:
  - event id
  - title
  - listed timestamp
  - category/thread
- pagination metadata field names and scalar values:
  - page
  - per_page
  - total_count
  - total_pages
- capture timestamp and original list URL

Forbidden to emit:
- title strings
- notice IDs / UUID values
- listed_at / created_at values
- notice bodies
- symbols / market names
- event classification.

## Frozen equivalence contract

A modern archived list is schema-equivalent if it exposes:
- `data.notices[]`
- row fields including `id`, `title`, `listed_at`

A legacy archived list is only a candidate if it exposes:
- a deterministic row array (historically `data.list[]`)
- event id
- title
- an authoritative publication timestamp field.

No mapping from a non-`listed_at` legacy timestamp to the frozen signal time is accepted merely by name similarity; it requires a later explicit equivalence proof.

## Classification

- `MODERN_ARCHIVED_SCHEMA_EQUIVALENT` if at least one modern deterministic sample passes the exact modern schema contract.
- `LEGACY_ARCHIVED_SCHEMA_CANDIDATE` if modern fails but legacy exposes all required semantic field classes.
- `ARCHIVE_SCHEMA_NOT_EQUIVALENT` otherwise.

Separately report list-page capture coverage metadata. No SOURCE_DATA_PASS can be emitted here.

## Follow-up firewall

Historical event enumeration remains CLOSED until a separate authority freezes:
- accepted family;
- exact payload mapping;
- snapshot/capture de-duplication;
- list-page completeness rule;
- anti-selection-bias rule;
- event-window filtering;
- frozen title parser reuse.

No Binance.
No OHLCV.
No returns/PnL.
No strategy changes.
No main merge.
