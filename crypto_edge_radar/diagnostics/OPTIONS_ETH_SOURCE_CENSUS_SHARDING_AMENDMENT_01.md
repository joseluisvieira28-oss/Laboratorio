# OPTIONS ETH — SOURCE CENSUS SHARDING AMENDMENT 01

Date: 2026-10-02
Status: FROZEN BEFORE SHARDED RERUN
Type: TECHNICAL ACQUISITION SCALING ONLY

## Reason

The already-frozen ETH source census covers the full 2024 calendar year and the public historical option stream is materially larger than SOL/XRP. Sequential acquisition is operationally slow.

No scientific outcome has been opened. This amendment changes acquisition parallelism only.

## Frozen sharding

The exact requested ETH period remains:
2024-01-01T00:00:00Z through 2025-01-01T00:00:00Z exclusive.

Split it into the 12 exact UTC calendar months of 2024.

Each month:
- requests Deribit history currency=ETH, kind=option;
- iterates disjoint UTC day windows;
- recursively splits any has_more window;
- rejects timestamps outside the month;
- records response SHA256 hashes;
- records all target trade IDs for global duplicate reconciliation;
- audits instrument parsing and required source fields;
- computes no scientific outcome.

After all 12 shards complete, one aggregation job MUST:
- prove all months completed;
- prove all 12 months contain target option trades;
- prove zero timestamp-boundary violations;
- prove zero structural missing-field rows;
- prove zero target instrument parse failures;
- prove zero duplicate trade IDs globally across all shards;
- sum invalid IV/index rows for later deterministic fail-closed filtering;
- emit the same SOURCE_GATE_PASS / SOURCE_GATE_BLOCKED_TRANSPORT / SOURCE_GATE_FAIL_DATA semantics.

## Invariants unchanged

No change to source provider, requested period, target asset, option kind, structural gates, invalid-row policy, or verdict definitions.

No skew.
No signal.
No forward return.
No PnL.
No 2025 rows.
No outcome price source.

Sharding cannot rescue a data-quality failure; it only accelerates acquisition of the same frozen source census.
