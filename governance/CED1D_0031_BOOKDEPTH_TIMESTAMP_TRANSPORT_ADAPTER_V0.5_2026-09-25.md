# CED1D-0031 — BOOKDEPTH TIMESTAMP TRANSPORT ADAPTER V0.5 — 2026-09-25

**Status:** FROZEN TECHNICAL TRANSPORT REMEDIATION / NO SCIENCE CHANGE  
**Authority ID:** `CED1D-0031-BOOKDEPTH-TIMESTAMP-TRANSPORT-V0.5`  
**Parent authority:** `CED1D_0031_RENDER_SHADOW_ACTIVATION_V0.3`  
**Frozen collector:** `crypto_edge_radar/radar/ced1d_render_shadow_collector_v03.py`

## Observed source fact

A source-format probe was run against the exact frozen Binance Vision public archives after the 2026-09-24 file became available.

GitHub Actions source probe:
- workflow: `CED1D Binance Vision BookDepth Format Probe`
- run id: `36149821006`
- result: PASS

Observed archives:

### 2026-09-23
- URL: `https://data.binance.vision/data/futures/um/daily/bookDepth/AVAXUSDT/AVAXUSDT-bookDepth-2026-09-23.zip`
- SHA256: `47f0834067cf0cb8c19d9484036d24c6a2b9940fb6a78d34b681fddb002435c2`
- member: `AVAXUSDT-bookDepth-2026-09-23.csv`
- header: `timestamp,percentage,depth,notional`
- observed timestamp form: `2026-09-23 00:00:04`

### 2026-09-24
- URL: `https://data.binance.vision/data/futures/um/daily/bookDepth/AVAXUSDT/AVAXUSDT-bookDepth-2026-09-24.zip`
- SHA256: `60c4a474743212e695bc6ce617717166d0b12ca768bc7c13bd1bc95524fb3b8f`
- member: `AVAXUSDT-bookDepth-2026-09-24.csv`
- header: `timestamp,percentage,depth,notional`
- observed timestamp form: `2026-09-24 00:00:01`

The frozen V0.3 collector currently calls `norm_ms()`, which accepts numeric epoch-like values only. Therefore the source-format mismatch fails closed with:
`ValueError: could not convert string to float: '2026-09-23 00:00:04'`.

## Frozen remediation

The collector file remains byte-for-byte unchanged.

A transport adapter may wrap **only** the frozen `parse_bookdepth_zip(raw, expected_day)` call at runtime.

Allowed normalization:

1. Preserve the original Binance Vision ZIP bytes for existing `verified_zip()` verification and SHA256 evidence.
2. Preserve CSV row order, header, percentage, depth and notional values exactly.
3. If and only if the first CSV field is:
   - already numeric: pass through unchanged; or
   - strict `YYYY-MM-DD HH:MM:SS`: interpret as UTC and convert to integer Unix epoch milliseconds.
4. Reject any other timestamp representation fail-closed.
5. Require the parsed textual date to equal the collector's `expected_day`.
6. Delegate the normalized in-memory ZIP bytes to the original frozen `parse_bookdepth_zip`.
7. Do not modify `book_capacity`, target timestamps, +/-1% bands, max-age threshold, capacity threshold, signal, direction, costs, notional, horizon, routing or any outcome metric.
8. Record a transport receipt with normalization counts and timestamp mode.
9. No historical outcome selection or rule rescue is permitted.

Because `verified_zip()` runs before `parse_bookdepth_zip()`, the source evidence SHA256 remains the SHA256 of the original public Binance Vision archive, not of normalized transport bytes.

## Scientific invariants unchanged

- candidate: CED1D-0031 / AVAXUSDT;
- family: A_MOMENTUM;
- lookback: 20 valid prior daily observations;
- direction: CONTINUATION;
- horizon: 1 day;
- first eligible signal day: 2026-09-22;
- first reference entry: 2026-09-23 00:01 UTC;
- source-readiness guard: 3 days;
- research notional: 100 USDT;
- BASE14 / STRESS20 reference costs;
- BASE8 / STRESS10 execution fees;
- aggTrades window: 5000 ms;
- bookDepth bands: +/-1%;
- bookDepth max age: 60000 ms;
- Tier-1 gate: >=60 resolved events, >=8 complete UTC signal weeks, >=50 complete execution pairs;
- no retrospective 2026 backfill;
- no parameter changes.

## Safety

- public/read-only data only;
- no authenticated exchange API;
- no orders;
- no exchange mutation;
- no wallet;
- no live capital;
- no automatic promotion;
- no main merge.

This authority is strictly a source-format transport correction.
