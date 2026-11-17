# MICROSTRUCTURE SCALPING LAB — RAW REPLAY GATE V0.1 RESULT

Date: 2026-09-25
Status: PASS_SAMPLE
Workflow run: 36187976006
Scope: source/replay integrity only — NO strategy outcomes inspected

## Sample
Source:
https://quote-saver.bycsi.com/orderbook/linear/BTCUSDT/2023-01-18_BTCUSDT_ob500.data.zip

Downloaded bytes: 87,855,500
Archive member: 2023-01-18_BTCUSDT_ob500.data
ZIP CRC: PASS

## Replay
Messages inspected: 250,000
Snapshots: 1
Deltas: 249,999

Integrity observations:
- JSON errors: 0
- schema errors: 0
- deltas before first snapshot: 0
- crossed reconstructed books: 0
- non-monotonic ts: 0
- non-monotonic cts: 0
- non-monotonic update id u: 0
- non-monotonic seq: 0
- final reconstructed bids: 500 levels
- final reconstructed asks: 500 levels

Observed message spacing in sample:
- median: 100 ms
- p95: 101 ms
- max: 500 ms

## Decision
PASS_SAMPLE.

This proves that one real historical BTCUSDT L2 file can be parsed and replayed snapshot + delta without integrity violations in the first 250,000 messages.

It DOES NOT prove:
- full-day integrity
- all-date integrity
- integrity across the ob500 -> ob200 archive transition
- ETH or other symbols
- venue portability to MEXC
- any predictive edge
- any net profitability

## Next mandatory gate
Run a deterministic, predeclared multi-date source-integrity matrix across pre-holdout years and the archive-depth transition. Do not choose dates based on price outcomes.

Outcome testing remains BLOCKED until that gate passes.
