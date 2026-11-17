# TRADE/L2 JOIN GATE V0.1 RESULT

Date: 2026-09-25
Workflow run: 36194278892

## Status
EXACT_SEQUENCE_JOIN = BLOCKED
COARSE_TIME_JOIN_100MS = FEASIBLE_SAMPLE

## Evidence
Historical 2023-01-18 L2 sample:
- 250,000 reconstructed L2 states
- historical cts present: 0%
- fallback event clock: orderbook ts

Historical public trades overlapping L2 sample:
- 189,851 trades
- timestamp regressions: 0
- buys: 98,576
- sells: 91,275

Clock alignment:
- nearest L2 timestamp distance: median 26 ms; p95 48 ms; p99 50 ms; max 99 ms
- prior L2 lag: median 50 ms; p95 95 ms; p99 99 ms
- next L2 lag: median 50 ms; p95 94 ms; p99 99 ms

Price/side sanity:
- 175,737 / 189,851 = 92.5657% of trades are consistent with the immediately preceding reconstructed BBO under the simple taker-side check.

## Decision
Do NOT claim exact queue reconstruction for this historical file.

For exploratory maker research only, a conservative coarse-time model may use:
- orderbook ts
- a minimum 100 ms clock-uncertainty buffer
- exact-price executed trades only
- no same-timestamp fills
- no credit from cancellations or price touches

Any maker candidate that survives must still pass a forward venue-specific execution study with native sequence data.
