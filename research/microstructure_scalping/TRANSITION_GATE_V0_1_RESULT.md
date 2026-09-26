# MICROSTRUCTURE SCALPING LAB — TRANSITION GATE V0.1 RESULT

Date: 2026-09-25
Status: PASS_STRATIFIED_SAMPLE
Workflow run: 36188296492
Scope: source integrity only — NO outcomes

## Archive transition identified
- Last ob500 day: 2025-08-20
- First ob200 day: 2025-08-21
- Latest pre-2026 holdout day checked by metadata: 2025-12-31

## Stratified raw replay samples
Each file: first 100,000 messages replayed from snapshot + deltas.

### 2025-08-20 — ob500
Compressed bytes: 297,395,226
CRC: PASS
Snapshot: 1
Deltas: 99,999
Final book: 500 bids / 500 asks
Median message delta: 100 ms
p95: 101 ms
max: 130 ms
All tracked integrity violations: 0
Gate: PASS_SAMPLE

### 2025-08-21 — ob200
Compressed bytes: 155,822,135
CRC: PASS
Snapshot: 1
Deltas: 99,999
Final book: 200 bids / 200 asks
Median message delta: 100 ms
p95: 101 ms
max: 204 ms
All tracked integrity violations: 0
Gate: PASS_SAMPLE

### 2025-12-31 — ob200
Compressed bytes: 154,553,382
CRC: PASS
Snapshot: 1
Deltas: 99,999
Final book: 200 bids / 200 asks
Median message delta: 100 ms
p95: 102 ms
max: 398 ms
All tracked integrity violations: 0
Gate: PASS_SAMPLE

## Combined decision
PASS_STRATIFIED_SAMPLE.

Together with the earlier 2023-01-18 250k-message replay, the source now has clean sample evidence at archive start, immediately before and after the depth-format transition, and at the end of the pre-holdout period.

This is sufficient to promote the historical Bybit L2 source from PROVISIONAL to SOURCE_FEASIBLE for building a pre-holdout research dataset.

It is NOT evidence of trading edge.

## Next gate
Build the frozen pre-holdout feature/label dataset and validate feature causality:
- no feature may use information later than t
- labels are future mid-price only
- 100ms/500ms/1s/5s/15s/30s horizons
- economic outputs gross and net of frozen venue costs
- Discovery remains separated from OOS and protected holdout
