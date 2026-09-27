# UPBIT-KRW-LISTING-SHOCK-001 — LEGACY/MODERN ARCHIVE EQUIVALENCE AUTHORITY V0.2.4

Date: 2026-09-27
Status: FROZEN BEFORE CROSS-FAMILY EVENT-FIELD COMPARISON / SOURCE-ONLY / OUTCOME-BLIND

## Parent evidence

V0.2.3A established:
- archived modern list schema is exact:
  `data.notices[]`
  with `id,title,first_listed_at,listed_at,category`;
- archived legacy list schema exposes:
  `data.list[]`
  with `id,title,created_at,updated_at`;
- modern list captures begin in 2024;
- legacy list captures cover 2023 and overlap 2024.

## Question

Does the historical legacy Upbit schema map exactly to the modern frozen signal-time semantics as:

- legacy `id` -> modern `id`
- legacy `title` -> modern `title`
- legacy `created_at` -> modern `first_listed_at`
- legacy `updated_at` -> modern `listed_at`

for notices observed by both archived API families during 2024?

## Frozen archive population

Use ALL successfully decodable exact-list captures in 2024 from:
- modern path exactly `/api/v1/announcements`;
- legacy path exactly `/api/v1/notices`.

Only HTTP-200 CDX captures.
Only page-1 list URLs already observed by V0.2.3A.

No detail endpoint.
No 2023 legacy event may be used until this audit passes.

## Archived payload decoding

Permitted only:
1. if raw bytes have gzip magic `1f8b`, gzip-decompress;
2. otherwise, if Wayback response explicitly reports original content encoding `br`, Brotli-decompress;
3. otherwise parse raw bytes as UTF-8 JSON.

No heuristic decompression beyond these rules.

## Deterministic comparison

For each notice ID present in both successfully decoded families:

1. collect every archived version from each family;
2. choose the modern/legacy record pair with the smallest absolute archive-capture timestamp gap;
3. ties resolve lexicographically by `(modern_capture, legacy_capture, modern_payload_sha, legacy_payload_sha)`;
4. classify the ID as COMPARABLE only if the chosen capture-time gap is <= 7 calendar days;
5. compare exact Unicode title strings and exact timestamp strings after ISO-8601 normalization to UTC.

No manual pair selection.

## PASS gate

`LEGACY_MODERN_SIGNAL_SCHEMA_EQUIVALENT` requires:
- >= 5 COMPARABLE overlapping notice IDs;
- 100% title equality;
- 100% legacy created_at == modern first_listed_at;
- 100% legacy updated_at == modern listed_at;
- zero parse/provenance ambiguity among compared rows.

Anything else:
`LEGACY_MODERN_SIGNAL_SCHEMA_NOT_PROVEN`.

This is deliberately conservative.

## Evidence output

May emit only:
- capture counts / decodable counts;
- overlap-ID count;
- comparable-ID count;
- exact-match counts/rates;
- mismatch counts;
- capture-gap min/median/max in seconds;
- aggregate SHA-256 of canonicalized compared tuples.

Do NOT emit:
- notice IDs;
- titles;
- timestamp values;
- symbols;
- market names.

## Firewall

No 2023 event enumeration.
No Binance.
No title parser execution.
No source-gate count.
No OHLCV/returns/PnL.
No strategy changes.
No main merge.

If PASS, a separate source-enumeration authority is still required before historical listing events are opened.
