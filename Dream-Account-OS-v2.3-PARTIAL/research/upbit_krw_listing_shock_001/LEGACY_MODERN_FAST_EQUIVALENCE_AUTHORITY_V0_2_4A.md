# UPBIT-KRW-LISTING-SHOCK-001 — LEGACY/MODERN FAST EQUIVALENCE AUTHORITY V0.2.4A

Date: 2026-09-27
Status: FROZEN BEFORE PAYLOAD REPLAY / SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Provide an independent, bounded equivalence proof while the exhaustive V0.2.4 archive replay is transport-slow.

This is not a replacement for a valid contradictory V0.2.4 result.

## Prospective precedence

- If V0.2.4 reaches a valid non-technical adjudication with >=5 comparable overlapping IDs, V0.2.4 remains authoritative.
- V0.2.4A may establish equivalence only if it independently passes its strict gate.
- A V0.2.4A insufficient result is not evidence of non-equivalence.

## Frozen capture selection

Use 2024 CDX index metadata only for exact list paths:
- modern /api/v1/announcements
- legacy /api/v1/notices

Construct all modern × legacy capture pairs.

Sort by:
1. absolute capture timestamp gap ascending;
2. modern timestamp;
3. legacy timestamp;
4. modern original URL;
5. legacy original URL;
6. modern digest;
7. legacy digest.

Select greedily the first 6 pairs subject to:
- a modern capture may appear in at most one selected pair;
- a legacy capture may appear in at most one selected pair.

Maximum payload replays: 12.

Selection uses archive metadata only, never payload contents.

## Decoding

Same transport rules as V0.2.4:
- gzip magic -> gzip;
- explicit original Content-Encoding br -> Brotli;
- explicit original Content-Encoding gzip -> gzip;
- otherwise identity UTF-8 JSON.

## Comparison

For each selected capture pair:
- compare rows sharing the same notice ID;
- emit no IDs/titles/timestamps;
- compare exact Unicode title;
- legacy created_at to modern first_listed_at after UTC ISO normalization;
- legacy updated_at to modern listed_at after UTC ISO normalization.

Union shared IDs across selected pairs; for duplicates retain the comparison from the selected pair with smallest capture gap, ties lexicographically by capture metadata.

## PASS

`FAST_LEGACY_MODERN_SIGNAL_SCHEMA_EQUIVALENT` iff:
- >=5 unique comparable IDs;
- 100% title exact;
- 100% created_at == first_listed_at;
- 100% updated_at == listed_at;
- zero ambiguous duplicate status for compared IDs.

Otherwise:
`FAST_EQUIVALENCE_INSUFFICIENT`.

No negative semantic conclusion is permitted from insufficiency.

## Firewall

No 2023 event enumeration.
No source-gate event classification.
No Binance.
No OHLCV/returns/PnL.
No strategy changes.
No main merge.
