# L2R-CROSSVENUE-001 — PARENT EVENT-STATE EXPORT SPEC V0.1

Date: 2026-10-01
Status: **FROZEN PRE-OUTCOME**

## Purpose

Define the exact event-level parent interface required to carry the already-frozen `L2-RESILIENCY-001` 2024 mechanism into the Crossvenue child without changing the parent science.

This specification is an export/interface contract only. It does not authorize Binance price-response computation.

## Canonical parent identity

- Parent LAB: `L2-RESILIENCY-001`
- Calendar: 2024 only
- Canonical parent manifest SHA256:
  `59e16ce8ea41658c2ea0fc6f2489d4deafbdc676e008d0b93f95ee6e3864913d`
- Canonical sweep anchor CSV SHA256:
  `be2c2d795a55ac3522fc6f3cdeb2d2c2ccf38bef8640a505934cbc76d9337eb3`
- Canonical sweep count: `9,181,478`
- Parent timing maximum lateness: `1,100 ms`
- Parent WEAK: `RR_R < 1.0`
- Parent STRONG: `RR_R >= 1.0`

## Event-state rows

The deterministic replay/export must produce one row per canonical sweep event, with a stable `event_id` assigned in accepted envelope order inside the canonical segment sequence.

Required common fields:

- `event_id`
- `segment_id`
- `anchor_date_utc`
- `anchor_envelope_ns`
- `side` = `ASK` or `BID`
- `direction` = +1 for ASK-consumed, -1 for BID-consumed
- `pre_depth5`
- `zero_pre_depth`

For each frozen replenishment horizon `R in {1000,5000,15000}`, required fields:

- `r_<R>_status` = `AVAILABLE`, `MISSING_SOURCE_TIMING`, or `ZERO_PRE_DEPTH_UNDEFINED`
- `r_<R>_envelope_ns` when available
- `r_<R>_lateness_ms` when available
- `r_<R>_same_side_depth5` when available
- `r_<R>_rr` = `r_same_side_depth5 / pre_depth5` when defined
- `r_<R>_class` = `WEAK` iff RR < 1.0, otherwise `STRONG`

No midpoint, Hyperliquid Y-response, parent outcome, PnL, cost or Binance value belongs in this export.

## Deterministic reconstruction rules

The replay must inherit the parent rules byte-for-byte in meaning:

- stale-late payloads are quarantined and cannot form transitions;
- continuity resets at missing-hour segment boundaries;
- both-sides-adverse transitions are ambiguous and excluded from sweep events;
- ASK consumed requires adverse ask move plus prior best ask absent post-snapshot;
- BID consumed requires adverse bid move plus prior best bid absent post-snapshot;
- `PRE_DEPTH5` is same-side top-5 displayed depth in the immediately preceding accepted normalized snapshot;
- R lookup is first accepted normalized state at-or-after `anchor + R`;
- R lookup must be no later than `anchor + R + 1,100 ms`;
- no interpolation, backfill, nearest-before substitution or cross-segment lookup.

## Integrity gates

Before the export can be consumed by Crossvenue Discovery it must pass all of:

1. source manifest SHA256 equals the canonical 2024 parent manifest;
2. total sweep rows = 9,181,478;
3. ASK/BID event totals reproduce parent counts:
   - ASK = 4,721,124
   - BID = 4,460,354
4. segment event totals reproduce the parent sweep-event preflight receipt;
5. timing availability/missing counts for 1s/5s/15s reproduce the parent horizon-timing receipt;
6. aggregated WEAK/STRONG counts and mean RR by frozen cell reproduce the immutable 2024 Discovery receipt within deterministic floating-point serialization tolerance;
7. no 2025/2026 source access;
8. no Binance data access during this export.

Failure of any identity gate is fail-closed and does not authorize repair by changing scientific rules.

## Output identity

The eventual event-state CSV/Parquet must receive a SHA256 and row count that are frozen before Binance price responses are opened.

This specification does not guess the schema of the old anchor CSV. It defines a new, explicit, reproducible derivative interface from the canonical parent source.
