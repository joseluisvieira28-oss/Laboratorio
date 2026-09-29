# OPENMARKET NEGATIVE CONTROL — UNIFIED LAG REPRODUCTION FREEZE V0.1

Frozen: 2026-09-24
Source commit: 6e6cc240f32ab9fd2f8fa602bd0aba823b24bfee
Dataset revision: 74502466d1a7cef56395bfd8d0b465fbebc849cf

Published targets from the exact pinned OpenMarket paper artifacts:
- lag pair count: 2,936,031
- median lead_lag_ms: 16 ms
- p5: -186 ms
- p95: 316 ms

## Reproduction rule

Read every parquet under:
full/lag_pairs_ms/**/*.parquet
at the exact immutable dataset revision.

No sampling.

For every row with finite values, verify:
lead_lag_ms == polymarket_source_ts_ms - binance_source_ts_ms

Compute:
- n
- median
- p5
- p95

## PASS

- identity violations = 0;
- n exactly 2,936,031;
- rounded median exactly 16 ms;
- rounded p5 exactly -186 ms;
- rounded p95 exactly 316 ms.

No tolerance widening after execution.

This is a negative-control/method reproduction only. It cannot promote IPG-001.
No IPG outcome, PnL or live execution is opened by this test.
