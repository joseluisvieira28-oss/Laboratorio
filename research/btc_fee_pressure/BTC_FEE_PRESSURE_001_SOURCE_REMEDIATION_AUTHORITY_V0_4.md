# BTC-FEE-PRESSURE-001 — SOURCE-REMEDIATION AUTHORITY V0.4

Status: FROZEN PRE-EXECUTION / OUTCOME-BLIND  
Date: 2026-09-14 UTC  
Lineage: V0.3 terminal `PROVENANCE_FAILURE` caused solely by one predecessor context block at height `663912` dated `2020-12-31` UTC. No market outcomes were opened.

## Immutable MVE
`BFP-TOTALFEES-7D-001`. Daily total BTC transaction fees paid to miners in canonical blocks assigned to UTC day. Future trigger remains strictly above trailing 90-observation 80th percentile excluding day t; LONG BTC; next UTC daily open; hold 7 days; no overlap; 10 bps base / 20 bps stress. No scientific parameter changes are authorized here.

## Window
`2021-01-01T00:00:00Z` through `2024-12-31T23:59:59Z` only.

## V0.4 remediation scope
This version changes only boundary interpretation. Timestamp-route heights are source anchors/context, not automatically canonical inclusion bounds. Reuse the immutable V0.3 shard artifacts from run `34880810011`; do not reacquire external source data.

## Boundary normalization rule
1. Reconstruct the complete canonical block index from the four V0.3 `CHUNK_PASS` artifacts.
2. Preserve and verify V0.3 source lineage, shard identities, source run ID, no hash conflicts, and complete height coverage.
3. Define the canonical in-window set strictly by block timestamp: `START_TS <= timestamp <= END_TS`.
4. `normalized_start_height` = minimum height among in-window canonical blocks.
5. `normalized_end_height` = maximum height among in-window canonical blocks.
6. Outside-window context is permitted only when its height lies strictly below `normalized_start_height` or strictly above `normalized_end_height`. Any outside-window block inside the normalized height interval is `PROVENANCE_FAILURE`.
7. Require complete source height coverage across `normalized_start_height..normalized_end_height`, no malformed/negative fee values, no hash conflicts, at least 1,400 UTC daily observations, and no missing UTC days. No fill/interpolation.
8. The output daily fee series contains only in-window block timestamps.

## Frozen input authority
- V0.3 source run: `34880810011`
- V0.3 tested source HEAD: `41fbbd23bbf0de3bc39965c9532c57febacb4a53`
- Chunk artifact IDs: `10363317187`, `10362954334`, `10363577920`, `10363658168`
- V0.3 final artifact ID: `10364463317`
- V0.3 final ZIP SHA256: `03df1bf7d146243be3d398ea9fecd1b6d83f5e08a5ee01ee7c1fc9ab36080a41`
- V0.3 manifest SHA256: `08454a435c4fef2727919b54b481f1b75ef302fa4decf783096a66466e8a38ca`
- Drive authority receipt: `1cgaqmcxXT6t9R1MMrzTcqQeQEFbIDp-yb3rkOK88egA`

## Valid terminal states
`SOURCE_DATA_PASS`, `SOURCE_ACQUISITION_TECHNICAL_FAILURE`, `DATA_FAILURE`, `PROVENANCE_FAILURE`, `INSUFFICIENT_SAMPLE`.

## Hard firewalls
Discovery prohibited. BTC/ETH prices prohibited. Returns/PnL/performance statistics prohibited. 2025 and 2026 prohibited. Live trading and exchange mutation prohibited. No merge to main, no deployment, no post-outcome tuning.
