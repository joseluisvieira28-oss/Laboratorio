# DLS — DRIFT WITH-FILL PUBLIC WINDOW TRANSPORT SHARDING ADDENDUM V0.2

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01
Status: FROZEN OPERATIONAL CORRECTION
Parent: DRIFT_WITH_FILL_PUBLIC_SOURCE_WINDOW_ADDENDUM_V0.1.md

## Reason

Run 36531242612 proved the short 2024-07-30 tail shard but the monthly shards were cancelled at the
70-minute workflow timeout. No price, return, PnL or direction outcome was opened.

This addendum changes only transport granularity.

## Global source window unchanged

[2024-07-30T17:21:13Z, 2025-01-01T00:00:00Z)

Program, discriminator and source semantics remain unchanged.

## Frozen shards

- wf2-01: [2024-07-30T17:21:13Z, 2024-08-10T00:00:00Z)
- wf2-02: [2024-08-10T00:00:00Z, 2024-08-20T00:00:00Z)
- wf2-03: [2024-08-20T00:00:00Z, 2024-09-01T00:00:00Z)
- wf2-04: [2024-09-01T00:00:00Z, 2024-09-11T00:00:00Z)
- wf2-05: [2024-09-11T00:00:00Z, 2024-09-21T00:00:00Z)
- wf2-06: [2024-09-21T00:00:00Z, 2024-10-01T00:00:00Z)
- wf2-07: [2024-10-01T00:00:00Z, 2024-10-11T00:00:00Z)
- wf2-08: [2024-10-11T00:00:00Z, 2024-10-21T00:00:00Z)
- wf2-09: [2024-10-21T00:00:00Z, 2024-11-01T00:00:00Z)
- wf2-10: [2024-11-01T00:00:00Z, 2024-11-11T00:00:00Z)
- wf2-11: [2024-11-11T00:00:00Z, 2024-11-21T00:00:00Z)
- wf2-12: [2024-11-21T00:00:00Z, 2024-12-01T00:00:00Z)
- wf2-13: [2024-12-01T00:00:00Z, 2024-12-11T00:00:00Z)
- wf2-14: [2024-12-11T00:00:00Z, 2024-12-21T00:00:00Z)
- wf2-15: [2024-12-21T00:00:00Z, 2025-01-01T00:00:00Z)

## Global PASS

DRIFT_WITH_FILL_PUBLIC_WINDOW_PASS only if:
- all 15 shard receipts exist;
- every shard classification is DRIFT_WITH_FILL_CENSUS_PASS or DRIFT_WITH_FILL_CENSUS_ZERO;
- every shard error_count = 0;
- intervals match exactly and cover the frozen source window with no gap/overlap;
- union transaction+instruction identity duplicate count = 0;
- global realized_count > 0.

No direction is decoded in this stage.

## Firewall

prices=false
returns=false
pnl=false
direction=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
