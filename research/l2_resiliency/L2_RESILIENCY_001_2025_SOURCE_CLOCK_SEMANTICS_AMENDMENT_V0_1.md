# L2-RESILIENCY-001 — 2025 SOURCE CLOCK SEMANTICS AMENDMENT V0.1

Date: 2026-09-21
Status: FROZEN BEFORE ANY 2025 VALIDATION OUTCOME ACCESS
Branch: l2-resiliency-v0.1

## Trigger
The exact V0.1.1 2025 validation pipeline completed source inventory and raw-body acquisition, then stopped fail-closed in source/schema normalization at:
market_data/20250101/4/l2Book/BTC.lz4
with the message "future payload".

No sweep, replenishment, midpoint response, return, PnL or validation statistic had been computed.

## Timestamp-only diagnostic
Evidence bundle:
L2_RESILIENCY_001_2025_SOURCE_CLOCK_DIAGNOSTIC_V0_1.zip
Bundle SHA256:
77d477d565962a7107b1fe13bd8f99eff9229c5d09a1d5d33bd284433f8db3c4

Exact offending raw object:
market_data/20250101/4/l2Book/BTC.lz4
SHA256:
248d0f9f4e3eff470520af97908ca299f34314c97a29a0fac650285d4d705093
Hash match: true.

Diagnostic scope was timestamps only. It did not read/store price levels, sizes, midpoint, sweeps, replenishment, returns, PnL or validation outcomes.

Observed:
- records: 6,295
- envelope backwards: 0
- payload rewinds: 0
- payload <= envelope: 6,292
- payload > envelope: 3
- positive deltas: +0.357706 ms, +2.297287 ms, +2.315735 ms
- positive max: +2.315735 ms
- median payload-minus-envelope: -48.094167 ms
- minimum: -1,589.441852 ms
- p95: -26.6126492 ms
- p99: -23.95004842 ms

## Source-semantics finding
The two timestamps represent distinct clocks and must not be constrained by a cross-clock causality inequality.

Frozen V0.1.2 semantics:
1. outer time = node/archive ordering clock;
2. nested raw.data.time = exchange payload clock;
3. envelope time remains the sole ordering/availability clock for archive-state sequencing and horizon scheduling;
4. envelope time must remain non-decreasing within a contiguous PRESENT segment;
5. envelope time must remain inside the UTC hour encoded by the official archive key;
6. payload time remains the payload freshness clock;
7. payload rewind below last accepted payload time remains STALE_LATE_PAYLOAD and is quarantined exactly as before;
8. equal payload timestamps remain accepted exactly as before;
9. payload > envelope is diagnostic only and is counted, not rejected;
10. no numerical cross-clock skew threshold is introduced.

The amendment removes only the invalid cross-clock requirement:
payload_ms * 1,000,000 <= envelope_ns.

## Independent semantic support
Independent Hyperliquid archive tooling describes L2 snapshots as event-driven and distinguishes outer time as node wall-clock at nanosecond precision and nested data.time as exchange time in milliseconds.
The official Hyperliquid SDK/API schema independently confirms that L2Book payloads carry their own millisecond time field inside the exchange payload.
These references support treating the clocks independently rather than assuming synchronized ordering across clocks.

## 2024 equivalence proof
The frozen 2024 source/schema closeout recorded future_payload = 0.
V0.1.2 changes only the handling of records for which payload > envelope.
Because that predicate was false for every accepted 2024 source record, the change has zero-hit impact on the 2024 corpus:
- same raw objects;
- same accepted/rejected states;
- same stale payload quarantine;
- same state ordering;
- same sweep events;
- same replenishment states;
- same response cells;
- same 2024 Discovery result.

No 2024 parameter or result is recomputed or retuned.

## Scientific invariants unchanged
Unchanged:
- source: official Hyperliquid requester-pays BTC l2Book;
- 2025 full-year holdout;
- 95% hourly source-coverage gate;
- immutable missing-hour segmentation;
- ASK/BID sweep definitions;
- PRE_DEPTH5;
- RR_R;
- WEAK < 1.0 / STRONG >= 1.0;
- R horizons +1s/+5s/+15s;
- response horizons +5s/+15s/+60s;
- 1,100 ms maximum lateness;
- six frozen causal cells;
- UTC-day contrasts;
- 10,000 bootstrap resamples;
- seed 20260919;
- >=300-day sample gates;
- validation PASS/FAIL criteria;
- 2026 forbidden;
- no PnL/economic layer;
- no post-outcome retuning.

## Receipt hygiene correction
V0.1.2 also overwrites the current pipeline-failure receipt on each fail-closed stop instead of preserving stale text from an older failure.
This changes evidence hygiene only and has no effect on source state or scientific outcomes.

## Authorization basis
Existing user authorization to attack L2-RESILIENCY-001 through the already-frozen independent 2025 validation remains in force.
This amendment is limited to a demonstrated source-clock semantic defect discovered before any 2025 validation outcome access.

## Next action
Execute exact V0.1.2 against the already acquired, hash-verified 2025 raw corpus.
No rule may be changed after the first 2025 validation outcome is computed.
