# RAW L2 REPLAY RECEIPT V0.1

Date: 2026-09-25
Scope: source integrity only; no future-price outcomes inspected.

GitHub Actions run: 36187976006
Result: PASS_SAMPLE

Pre-holdout raw source:
Bybit BTCUSDT linear, 2023-01-18, ob500.

Observed:
- archive bytes: 87,855,500
- ZIP CRC: PASS
- sampled messages: 250,000
- snapshots: 1
- deltas: 249,999
- JSON errors: 0
- schema errors: 0
- pre-snapshot deltas: 0
- crossed/locked reconstructed books: 0
- nonmonotonic ts: 0
- nonmonotonic cts: 0
- nonmonotonic update id: 0
- nonmonotonic seq: 0
- final reconstructed levels: 500 bids / 500 asks
- inter-message delta median: 100 ms
- p95: 101 ms
- max: 500 ms

Interpretation:
This sample supports deterministic replay feasibility for the observed file.
It does NOT yet prove complete multi-day/multi-symbol integrity, economic edge, fills, or MEXC transferability.
