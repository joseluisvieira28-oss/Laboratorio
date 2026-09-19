# AAVE-LIQUIDATION-OVERHANG-001 — DISCOVERY ACTIVE RESERVE SCOPE REMEDIATION V0.1.1

Status: **FROZEN AFTER TECHNICAL FAILURE / BEFORE DISCOVERY OUTCOMES**
Date: **2026-09-19**

## Trigger

Canonical Discovery run `35393804723` completed:
- preflight PASS;
- calendar PASS;
- global-source PASS;
- reserve shards 2 and 7 PASS;
- reserve shards 0,1,3,4,5,6 failed before predictor materialization;
- predictor, outcomes and canonical adjudication remained skipped.

No future liquidation outcome was opened.

## Exact failure class

All six failed reserve shards stopped on:

`RuntimeError: missing reserve decimals`

The union of missing reserve addresses is exactly 10 reserves.

R0 canonical bootstrap proves every one of those 10 reserves has
`init_block > 18,908,894`, the final canonical 2023 Discovery event block.

Missing addresses / init blocks:
- `0x6c3ea9036406852006290770bedfcaba0e23a0e8` — 19,211,968
- `0xcd5fe23c85820f7b72d0926fc9b05b43e359b7ee` — 19,653,435
- `0xf1c9acdc66974dfb6decb12aa385b9cd01190e38` — 19,859,211
- `0x4c9edd5852cd905f086c759e8383e09bff1e68b3` — 20,033,499
- `0xa35b1b31ce002fbf2058d22f30f95d405200a15b` — 20,139,378
- `0x9d39a5de30e57443bff2a8307a4256c8797a3497` — 20,184,634
- `0x18084fba666a33d37592fa2633fd49a74dd93a88` — 20,812,949
- `0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf` — 20,813,115
- `0xdc035d45d973e3ec169d2276ddab16f1e407384f` — 20,879,386
- `0xa1290d69c65a6fe4df752f95823fae25cb99e5a7` — 21,235,953

Therefore the failure is a deterministic scope bug:
the V0.1 Discovery reserve shard required aToken decimals for the full 37-reserve
2023-2024 R1 universe even when a reserve had not yet been initialized during
the frozen 2023 Discovery partition.

## Authorized correction

For Discovery 2023 only:

1. preserve the exact canonical 37-reserve R1 universe and modulo-8 shard
   assignment;
2. inside each shard, define `active_reserves_2023` as the assigned reserves
   with `init_block <= discovery_event_to_block`;
3. query/replay/materialize only those active reserves;
4. require decimals only for those active reserves;
5. aggregate the exact union of active reserves at the frozen 2023 boundary.

The exact active-reserve count at 2023-12-31 is **27**.

The 10 post-2023 reserves are not deleted from R1 provenance and are not treated
as unsupported. They are simply not members of the point-in-time 2023
Discovery universe because their canonical ReserveInitialized event had not
occurred yet.

## Recovery topology

Reuse the already-PASS V0.1 artifacts for:
- shard 2;
- shard 7.

Rerun only:
- shard 0;
- shard 1;
- shard 3;
- shard 4;
- shard 5;
- shard 6.

The row-generation, ray math, oracle/index quorum, eMode rules, 10% stress,
predictor, outcome, horizon and statistical gates are unchanged.

## Firewalls

Still forbidden:
- 2024 predictor/outcome opening;
- 2025/2026 scientific data;
- market returns;
- PnL;
- trading;
- threshold/shock/horizon/regime tuning.

This remediation is technical and outcome-blind.
