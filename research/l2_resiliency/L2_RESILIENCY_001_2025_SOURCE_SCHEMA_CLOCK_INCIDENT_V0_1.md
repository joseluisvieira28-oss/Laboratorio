# L2-RESILIENCY-001 — 2025 SOURCE-SCHEMA CLOCK SEMANTICS INCIDENT V0.1

Date: 2026-09-20
Status: SOURCE_SCHEMA_SEMANTICS_BLOCKED / NO_OUTCOMES
Branch: l2-resiliency-v0.1

## Evidence bundle received
File: L2_RESILIENCY_001_2025_VALIDATION_EVIDENCE_V0_1.zip
Observed uploaded ZIP SHA256: 4167d0f1c64b7b6fe76894a3c4c8e41720180276e9bef4e04ccb010a47c41c00

## Source inventory
- expected hours: 8,760
- PRESENT: 8,400
- MISSING: 360
- ERROR: 0
- coverage: 95.89041095890411%
- frozen minimum: 95.0%
- classification: SOURCE_INVENTORY_PASS

The 360 missing hours are exactly two immutable runs:
- 2025-10-16T11:00Z through 2025-10-22T23:00Z = 157h
- 2025-11-17T13:00Z through 2025-11-25T23:00Z = 203h

## Body acquisition
- expected PRESENT objects: 8,400
- verified objects: 8,400
- failed objects: 0
- compressed bytes verified: 8,975,275,014
- classification: SOURCE_BODY_ACQUISITION_PASS
- raw manifest SHA256: 767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3

## Schema fail-closed
The source/schema stage stopped before outcome computation:
SOURCE_SCHEMA_FAIL_CLOSED
failure:
PipelineFailure: market_data/20250101/4/l2Book/BTC.lz4: future payload

No validation statistics were computed.
No 2025 directional outcome was opened.
2026 remained untouched.

## Receipt caveat
The evidence ZIP also contains L2_RESILIENCY_001_2025_PIPELINE_FAILURE_V0_1.json with an older
"PipelineFailure: SOURCE_INVENTORY_ERROR" string.
This is operationally stale: the canonical current inventory receipt in the same bundle is SOURCE_INVENTORY_PASS.
The V0.1.1 main exception handler preserves a pre-existing pipeline-failure file rather than overwriting it.
This is a receipt-hygiene defect, not a scientific result.

## Why this is not NO_EDGE
The failure happened in source-time normalization before any sweep, replenishment, response or validation outcome.
It is neither VALIDATION_FAIL_NO_PROMOTION nor evidence against the L2 mechanism.

## Source-clock issue under investigation
The frozen V0.1.1 normalizer rejects any record where raw.data.time (payload exchange timestamp, ms)
is later than the outer archive time (envelope timestamp, ns).

Independent ingestion references describe these as distinct clocks: outer node/archive wall-clock versus nested exchange time.
Therefore a small positive payload-envelope delta may be clock skew rather than corrupt source ordering.

No scientific rule may be changed yet.
First action is a source-only clock diagnostic on the exact offending raw object:
market_data/20250101/4/l2Book/BTC.lz4

The diagnostic may inspect ONLY:
- outer time;
- raw.data.time;
- record order;
- timestamp deltas;
- raw-byte SHA256 binding.

It must not inspect/store:
- price levels;
- sizes;
- midpoint;
- sweeps;
- replenishment;
- returns;
- validation outcomes.

## Next decision
After the source-clock diagnostic:
1. if the record is structurally corrupt => preserve SOURCE_SCHEMA_FAIL_CLOSED;
2. if it demonstrates legitimate cross-clock skew => freeze a source-semantics amendment before any validation outcome access, prove 2024 equivalence, then rerun 2025 schema/validation unchanged economically.

No post-outcome tuning is possible because no outcome has been computed.
