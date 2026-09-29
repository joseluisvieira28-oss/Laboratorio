# DLS — DRIFT WITH-FILL PUBLIC WINDOW TRANSPORT SHARDING ADDENDUM V0.3

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01
Status: FROZEN OPERATIONAL CORRECTION / SOURCE-ONLY

Parent:
DRIFT_WITH_FILL_TRANSPORT_SHARDING_ADDENDUM_V0.2.md

Canonical run 36547101169 recovered valid source receipts for wf2-01..wf2-11 and wf2-13.
wf2-12, wf2-14 and wf2-15 were repeatedly cancelled by workflow runtime before emitting receipts.
The global scientific window, decoder and source semantics remain unchanged.

No price, return, PnL or direction outcome is opened by this correction.

## Replacement transport shards

Replace only the three unfinished V0.2 intervals:

wf3-12a: [2024-11-21T00:00:00Z, 2024-11-26T00:00:00Z)
wf3-12b: [2024-11-26T00:00:00Z, 2024-12-01T00:00:00Z)

wf3-14a: [2024-12-11T00:00:00Z, 2024-12-16T00:00:00Z)
wf3-14b: [2024-12-16T00:00:00Z, 2024-12-21T00:00:00Z)

wf3-15a: [2024-12-21T00:00:00Z, 2024-12-26T00:00:00Z)
wf3-15b: [2024-12-26T00:00:00Z, 2025-01-01T00:00:00Z)

All other V0.2 shard artifacts remain immutable and are reused.

## Final reassembly requirements

A terminal public-window PASS requires:
- original successful/zero receipts for wf2-01..wf2-11 and wf2-13;
- all six replacement receipts above;
- every receipt classification in {DRIFT_WITH_FILL_CENSUS_PASS, DRIFT_WITH_FILL_CENSUS_ZERO};
- error_count=0 for every receipt;
- exact interval union equals [2024-07-30T17:21:13Z, 2025-01-01T00:00:00Z);
- no gap or overlap;
- union transaction+instruction duplicate identity count=0;
- global realized_count > 0.

The cancelled wf2-12/wf2-14/wf2-15 jobs are never treated as scientific failures and are not reused.

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
