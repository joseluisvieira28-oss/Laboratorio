# AAVE-LIQUIDATION-OVERHANG-001 — R1 SHARDED AUDIT V0.3.2 SUPERSESSION CLOSEOUT

Date: 2026-09-18
Status: **SUPERSEDED / DUPLICATE OPERATIONAL RECOVERY / NOT CANONICAL**

The V0.3.2 sharded R1 audit remediation was prepared from an earlier observed branch state in which the monolithic R1 audit had twice hit wall-clock limits.

Before V0.3.2 could establish any canonical authority, branch reconciliation recovered a newer, already-completed authoritative lineage:

- canonical R1 semantic-reconciliation run: `35384529037`;
- canonical artifact: `AAVE_R1_SEMANTIC_RECONCILIATION_V0_5`;
- canonical classification: `RECONSTRUCTION_DATA_PASS`;
- audit component: `R1_AUDIT_PASS`;
- global component: `R1_GLOBAL_STATE_PASS`;
- reserve components: 8/8 `R1_RESERVE_SHARD_PASS`;
- 77/77 frozen audit targets validated;
- 119 Aave-oracle price targets; 0 failures;
- final pre-Discovery protocol frozen at commit `28d585c643d9...`;
- 2023 Discovery execution authority frozen at commit `c8c5f8677ec7...`;
- canonical Discovery run `35393804723` launched from commit `c5a317e56e6a090313add1c6eca192d3d934b963`.

Therefore V0.3.2 is **not** a source of canonical reconstruction authority and must not override, replace, re-adjudicate or reopen the already-passed R1 lineage.

GitHub Actions run `35396926952`, if it executes/completes, is diagnostic duplicate work only. Its receipts must not be used to change the canonical R1 classification or the Discovery protocol.

No economic result, market outcome, threshold, shock, horizon or trading rule is changed by this supersession closeout.

Canonical path now:
`RECONSTRUCTION_DATA_PASS -> FINAL_PRE_DISCOVERY_PROTOCOL_V0.1 -> 2023 Discovery run 35393804723`.

2024 remains locked until the canonical 2023 Discovery receipt permits replication.
2025/2026 remain locked.
No live trading, orders, wallets, exchange mutation, capital deployment or main merge are authorized.
