# LICP-001 — SOURCE GATE RECEIPT V0.1

Date: 2026-09-26
Workflow run: 36230382690
Status: SOURCE_FEASIBLE / PASS_SAMPLE

## Scope
Public market data only.
No authentication.
No orders.
No exchange mutation.
No strategy outcomes.

## Binance BTCUSDT BBO
- connected: yes
- updates: 23,093
- crossed BBO: 0
- local monotonic clock regressions: 0

## Binance all-market force-liquidation stream
- subscription acknowledged: yes
- messages: 15
- forced-liquidation events: 14
- malformed liquidation payloads: 0
- local clock regressions: 0

Important source limitation:
Binance publishes only the latest liquidation order per symbol inside each 1,000 ms interval. These 14 events are therefore snapshots, not complete liquidation volume.

## Bybit allLiquidation BTC/ETH/SOL
- subscription acknowledged: yes
- messages: 1
- liquidation events during this 90-second sample: 0
- malformed liquidation payloads: 0
- local clock regressions: 0

Zero observed Bybit liquidations in this specific sample is not a source failure because the subscription was acknowledged and the feed is event-driven.

## MEXC BTC_USDT incremental depth
- subscription acknowledged: yes
- depth updates: 408
- total messages: 417
- heartbeats sent: 8
- crossed reconstructed BBO: 0
- version regressions: 0
- local clock regressions: 0

## Decision
LICP-001 Phase A = SOURCE_FEASIBLE.

The first failed run was an infrastructure failure only:
- Binance BBO had been subscribed through an incompatible market-stream route;
- MEXC heartbeat was conditional on idle periods and therefore starved during continuous depth traffic.

Both defects were corrected without changing the hypothesis or any scientific threshold.

## Next authorized research stage
Forward calibration only:
- measure liquidation-event size and burst distributions;
- keep Bybit and Binance source semantics separate;
- do not interpret Binance snapshot counts as complete volume;
- do not inspect post-trigger price outcomes until calibration features and thresholds are frozen.

No live-trading authority is created by this receipt.
