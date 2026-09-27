# UPBIT-KRW-LISTING-SHOCK-001 — TITLE-LINKED LEGACY/MODERN EQUIVALENCE AUTHORITY V0.2.6

Date: 2026-09-27
Branch: `upbit-krw-listing-shock-title-equivalence-v0.2.6`
Status: FROZEN BEFORE PAYLOAD REPLAY / SOURCE-ONLY / OUTCOME-BLIND

## Parent evidence

The archive campaign already established:

- modern archived list schema:
  `data.notices[]`
  with `id,title,first_listed_at,listed_at,category`;
- legacy archived list schema:
  `data.list[]`
  with `id,title,created_at,updated_at`;
- current Upbit documentation defines:
  - `first_listed_at` as initial publication time;
  - `listed_at` as latest publication/update time;
- V0.2.4 ID-linked comparison found zero overlapping IDs between the two archived API families and therefore could not adjudicate timestamp-field equivalence.

Zero ID overlap is not treated as proof of semantic non-equivalence because legacy and modern detail paths exhibit non-overlapping identifier sets.

## Purpose

Test legacy/modern signal-time equivalence by linking archived records using the exact announcement title rather than notice ID.

This is a source-schema/provenance audit only.

No event qualification, title-parser execution, Binance access, OHLCV, return or PnL is authorized.

## Frozen archive population

Use all HTTP-200 CDX captures in calendar year 2024 from exactly:

Modern:
- `api-manager.upbit.com/api/v1/announcements*`

Legacy:
- `api-manager.upbit.com/api/v1/notices*`

Accept only exact API paths:
- modern list: `/api/v1/announcements`
- modern numeric detail: `/api/v1/announcements/{NUMERIC_ID}`
- legacy list: `/api/v1/notices`
- legacy numeric detail: `/api/v1/notices/{NUMERIC_ID}`

Exclude:
- latest;
- news;
- any non-numeric detail suffix;
- any other path.

No 2023 payload is opened in this audit.

## Replay transport

For each accepted capture:

1. replay exact capture using
   `https://web.archive.org/web/{TIMESTAMP}id_/{ORIGINAL_URL}`;
2. decode by:
   - gzip magic `1f8b` -> gzip;
   - explicit original `Content-Encoding: br` -> Brotli;
   - explicit original `Content-Encoding: gzip` -> gzip;
   - otherwise identity UTF-8 JSON;
3. if and only if the exact `id_` replay returns HTTP 200 bytes but cannot be decoded/parsing cannot reach JSON because archive transport encoding is opaque, make one transport-only retry of the same exact capture using `if_`;
4. accept the retry only if it returns JSON for the same archived original URL/capture.

No capture substitution, timestamp substitution or manual sample selection.

## Record extraction

Modern list/detail records may be used only when they expose:
- title
- first_listed_at
- listed_at

Legacy list/detail records may be used only when they expose:
- title
- created_at
- updated_at

Normalize timestamps only to UTC ISO-8601 seconds.

Titles:
- exact decoded Unicode string;
- no trimming;
- no case folding;
- no punctuation normalization;
- no translation;
- no fuzzy matching.

## Deterministic title linking

Within each family, group usable rows by exact title string.

A title is `UNAMBIGUOUS` within a family only if every usable instance of that exact title has one identical normalized timestamp tuple:
- modern: (first_listed_at, listed_at)
- legacy: (created_at, updated_at)

Any title with multiple distinct timestamp tuples inside either family is excluded as ambiguous.

Comparable title population:
- exact title present in both families;
- unambiguous in both families.

For each comparable title test:
- legacy created_at == modern first_listed_at
- legacy updated_at == modern listed_at

No notice-ID equality is required.

## PASS gate

`TITLE_LINKED_LEGACY_MODERN_SIGNAL_SCHEMA_EQUIVALENT` requires all:

- >= 5 unique comparable exact-title records;
- 100% legacy created_at == modern first_listed_at;
- 100% legacy updated_at == modern listed_at;
- zero ambiguous title among the compared set;
- zero timestamp parse ambiguity in compared rows.

Anything else:
`TITLE_LINKED_EQUIVALENCE_NOT_PROVEN`.

Insufficiency is not evidence of semantic non-equivalence.

## Evidence output

May emit only:
- CDX capture counts;
- replay/decoded counts;
- usable record counts;
- distinct exact-title counts;
- ambiguous-title counts;
- comparable-title count;
- timestamp exact-match counts/rates;
- aggregate SHA-256 of canonicalized comparison tuples;
- transport/decode failure counts.

Must not emit:
- title strings;
- notice IDs;
- publication timestamps;
- symbols;
- market names;
- event classifications.

## Scientific firewall

No 2023 event enumeration.
No title parser.
No source-gate qualified-event count.
No Binance.
No OHLCV.
No returns.
No PnL.
No 2025/2026 market data.
No strategy changes.
No source-minimum changes.
No main merge.
No post-outcome tuning.

A PASS still requires a separate prospective historical-enumeration authority before source events may be opened.
