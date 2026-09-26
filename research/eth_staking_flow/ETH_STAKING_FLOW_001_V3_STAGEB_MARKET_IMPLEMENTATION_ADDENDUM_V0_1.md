# ETH-STAKING-FLOW-001 — V3 STAGE-B MARKET ACQUISITION IMPLEMENTATION ADDENDUM V0.1

Date frozen: 2026-09-27
Parent: ETH_STAKING_FLOW_001_V3_INDEPENDENT_REPLICATION_AUTHORITY_V0_1
Status: FROZEN BEFORE ANY V3 STAGE-B 2025/2026 MARKET ACCESS

## Trigger firewall

Stage B may execute only after a durable Stage-A receipt on the same research branch states:

SOURCE_REPLICATION_PASS

with exactly 608 source dates through 2026-08-31.

Any other source classification keeps Stage B closed.

## Market source unchanged

Official Binance Data Vision Spot ETHUSDT 1d klines only.

Every ZIP must be verified against the provider .CHECKSUM sidecar before parsing.

## Frozen file partitioning

For completed calendar months:
- use monthly Spot ETHUSDT 1d ZIP + CHECKSUM.

Required completed-month range:
- 2025-01 through 2025-12;
- 2026-01 through 2026-08.

For the still-incomplete September 2026 month, only exits through the already-frozen ceiling 2026-09-08 are authorized.

Therefore acquire exactly these daily files:
- 2026-09-01 through 2026-09-08 inclusive;
- Spot ETHUSDT 1d daily ZIP + CHECKSUM.

No market date after 2026-09-08 may be requested.

No fallback to exchange API, third-party candles, current prices, or unverified files is allowed.

## Timestamp normalization

Binance archive timestamps may be encoded in milliseconds or microseconds depending on archive era.

Parse by magnitude only:
- 10^12 <= timestamp < 10^14 => milliseconds;
- 10^15 <= timestamp < 10^17 => microseconds;
- anything else => fail closed.

After normalization, the UTC date must match the archive row/date geometry.

Timestamp-unit handling is a transport/schema compatibility rule only. It does not alter any price.

## Frozen replication blocks

R1:
- signal dates 2025-01-01 through 2025-12-23;
- entry t+1;
- exit t+8;
- market ceiling 2025-12-31.

R2:
- signal dates 2026-01-01 through 2026-08-31;
- entry t+1;
- exit t+8;
- market ceiling 2026-09-08.

R1 and R2 are scanned independently. Non-overlap state resets at the start of each independent block.

Prior-90 context:
- R1 may use the already-canonical 2024 queue source;
- R2 uses the frozen Stage-A 2025/2026 source.

## Signal/statistics

No change from the V3 authority:
- net_queue = pending_queued - active_exiting;
- current >= linear q80 of exactly 90 prior observations;
- current excluded from threshold;
- LONG ETHUSDT spot;
- next UTC daily open entry;
- exit t+8 signal geometry;
- 10 bps NET10;
- 20 bps NET20;
- unchanged non-overlap;
- stationary bootstrap reps=10,000, seed=730031, restart probability=0.25.

## V3 adjudication

Evaluate D, R1, R2 separately and pooled exactly as frozen in the V3 authority.

This implementation addendum creates no new promotion gate and no rescue rule.

## Safety

No live trading.
No orders.
No authenticated exchange API.
No wallet.
No exchange mutation.
No market date after 2026-09-08.
No source date after 2026-08-31.
No main merge.
No post-outcome tuning.
