# UPBIT-KRW-LISTING-SHOCK-001 — ARCHIVE LIST CONTINUITY AUTHORITY V0.2.7

Date: 2026-09-27
Branch: `upbit-krw-listing-shock-archive-coverage-v0.2.7`
Status: FROZEN BEFORE PAYLOAD REPLAY / SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Test whether archived first-party Upbit page-1 announcement-list snapshots are sufficiently continuous to reconstruct the frozen 2023-2024 notice universe without archive-induced event-selection bias.

This is a completeness/provenance audit only.

No listing-title parser, Binance source gate, OHLCV, return or PnL may be opened.

## Frozen archive families

Legacy stream:
- exact path `/api/v1/notices`;
- calendar captures 2023-2024;
- accept only list URLs with `thread_name=general`;
- page must equal 1;
- per_page may be any positive archived value.

Modern stream:
- exact path `/api/v1/announcements`;
- calendar captures 2024;
- accept only list URLs with `category=all`;
- page must equal 1;
- per_page may be any positive archived value.

No detail endpoint.
No press stream.
No latest/news endpoint.
No path guessing.

## Replay transport

Use exact CDX HTTP-200 captures.

Replay exact capture with:
`https://web.archive.org/web/{TIMESTAMP}id_/{ORIGINAL_URL}`

Decode only by:
- gzip magic -> gzip;
- explicit original Content-Encoding br -> Brotli;
- explicit original Content-Encoding gzip -> gzip;
- otherwise identity UTF-8 JSON.

If exact id_ replay returns HTTP 200 but decoding/JSON parsing fails due opaque archive transport, one retry using `if_` for the same exact capture is permitted.

No capture substitution.

## Frozen row extraction

Legacy list:
- row path `data.list[]`;
- require `id`, `created_at`, `updated_at`.

Modern list:
- row path `data.notices[]`;
- require `id`, `first_listed_at`, `listed_at`.

Titles may not be read or stored by this audit.

For continuity timing only:
- legacy row time = normalized `created_at`;
- modern row time = normalized `first_listed_at`.

This timing use is a coverage diagnostic only and does not establish signal-time equivalence.

## Snapshot validity

A snapshot is usable only if:
- >= 1 valid row;
- IDs are unique within the snapshot;
- row publication times are non-increasing in API row order;
- all parsed timestamps are timezone-aware.

## Within-family continuity

Sort usable snapshots by archive capture timestamp.

For each consecutive snapshot pair within the same family, require at least one shared notice ID.

A missing ID overlap is a continuity break because page-1 snapshots alone cannot then prove that no notices fell between the two archived windows.

Duplicate archive snapshots with identical row-ID sequences may be collapsed before continuity testing.

## Boundary requirements

Frozen scientific source window:
- start inclusive: 2023-01-01T00:00:00Z
- end exclusive: 2025-01-01T00:00:00Z

Legacy start boundary passes only if the earliest usable legacy snapshot's row-time interval straddles or precedes the source start:
- oldest row time <= source start;
- newest row time >= source start.

Modern end boundary passes only if the latest usable modern snapshot is capable of covering the end boundary:
- archive capture timestamp >= source end;
- newest row publication time >= source end.

Because no capture may describe notices published after its own archive timestamp, a latest capture before the source end necessarily fails the end boundary.

## Cross-family overlap diagnostic

Report:
- legacy usable coverage interval;
- modern usable coverage interval;
- temporal overlap duration between the two intervals.

A merged archive can only be considered if:
- legacy internal continuity passes;
- modern internal continuity passes;
- the family coverage intervals overlap by at least 7 calendar days;
- the separate schema-equivalence lineage proves legacy/modern timestamp semantics.

This V0.2.7 audit does not itself consume the equivalence result.

## PASS gate

`ARCHIVE_LIST_CONTINUITY_PASS` requires all:
- usable legacy general-list snapshots exist;
- usable modern all-category snapshots exist;
- legacy start boundary passes;
- modern end boundary passes;
- zero legacy continuity breaks;
- zero modern continuity breaks;
- family coverage intervals overlap >= 7 days.

Otherwise:
`ARCHIVE_LIST_CONTINUITY_NOT_PROVEN`.

## Evidence output

May emit only aggregate metadata:
- capture/usable counts;
- collapsed duplicate counts;
- continuity-pair count;
- continuity-break count;
- minimum/median/maximum shared-ID count across pairs;
- boundary pass booleans;
- coverage interval endpoints;
- cross-family overlap seconds/days;
- aggregate SHA-256 of canonicalized ID/timestamp-free continuity receipts.

Must not emit:
- notice IDs;
- titles;
- event timestamps per row;
- symbols;
- market names.

## Firewalls

No title parser.
No event classification.
No qualified-event counts.
No Binance.
No OHLCV.
No returns/PnL.
No 2025/2026 market data.
No strategy changes.
No source-minimum changes.
No main merge.
No post-outcome tuning.
