# LL-0017 — DUPLICATE PROVENANCE DIAGNOSTIC AUTHORITY V0.1

Date: 2026-09-18
Status: **FROZEN BEFORE DIAGNOSTIC / SOURCE-ONLY / OUTCOME-BLIND**

Parent authority:
`LL0017_POSITIONING_RATIO_PRE_SOURCE_AUTHORITY_V0_1.md`

Observed parent terminal result:
- run `35365438710`
- classification `PROVENANCE_FAILURE`
- first probe date `2021-01-15`
- provider header was present and contained all three required positioning fields;
- failure detail: `duplicate timestamps=288`.

The parent V0.1 verdict remains immutable.

## Purpose

Determine whether the duplicate timestamps are caused by:
1. exact byte-identical duplicate provider rows; or
2. multiple non-identical records sharing the same timestamp.

This is a provenance diagnostic only. It does not alter the parent gate.

## Frozen diagnostic scope

Date: `2021-01-15` only.
Source: exact same Binance Data Vision BTCUSDT metrics ZIP and CHECKSUM route.

May inspect/persist only:
- checksum;
- CSV header;
- row count;
- timestamp field;
- symbol field;
- multiplicity per timestamp;
- SHA-256 of each complete raw CSV row;
- whether rows sharing a timestamp have identical raw-row hashes;
- aggregate counts of identical vs non-identical duplicate groups.

Forbidden:
- parsing or persisting any ratio numeric value;
- parsing open-interest or taker numeric values;
- prices, returns, PnL or future outcomes;
- 2025/2026.

## Diagnostic classifications

- `EXACT_PROVIDER_ROW_DUPLICATION_CONFIRMED`: every duplicated timestamp group consists only of byte-identical full rows.
- `MULTIPLE_DISTINCT_ROWS_PER_TIMESTAMP`: at least one duplicate group contains different raw-row hashes.
- `DIAGNOSTIC_TECHNICAL_FAILURE`
- `DIAGNOSTIC_PROVENANCE_FAILURE`

If exact provider duplication is confirmed, a new prospective source-normalization amendment MAY be written before any rerun. It must preserve the original V0.1 failure and may only collapse exact byte-identical duplicate rows.

If distinct rows share timestamps, do not choose among them without a new independently justified source identity rule.

No economic outcome is authorized by this diagnostic.
