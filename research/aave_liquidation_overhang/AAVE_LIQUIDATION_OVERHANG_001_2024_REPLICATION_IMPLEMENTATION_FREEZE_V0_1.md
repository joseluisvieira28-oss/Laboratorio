# AAVE-LIQUIDATION-OVERHANG-001 — 2024 REPLICATION IMPLEMENTATION FREEZE V0.1

Status: **FROZEN BEFORE ANY 2024 PREDICTOR OR OUTCOME OPENING**
Date: **2026-09-19**

Canonical Discovery authority:
- run 35436923688
- canonical artifact 10582547257
- classification DISCOVERY_MECHANISM_PASS
- next authorized phase 2024_REPLICATION_PROTOCOL_EXECUTION

Replication authority:
- AAVE_LIQUIDATION_OVERHANG_001_2024_REPLICATION_EXECUTION_AUTHORITY_V0_1.md
- AAVE_LIQUIDATION_OVERHANG_001_2024_REPLICATION_TERMINAL_DAY_FIREWALL_CLARIFICATION_V0_1.md

Frozen implementation blob SHAs:
- replication_calendar_2024_v01.py = d7aa8542790005e00197e2144286ca7323120957
- replication_global_replay_2024_v01.py = 1f1d645ca6aa64875af59ae6b4ceff02b44dd47e
- replication_reserve_shard_2024_v01.py = 6822c8048979cb035042c44c99b9bc17679205e1
- replication_predictor_aggregate_2024_v01.py = 058e289a534004de5e162991d9a3397ee9e8cdef
- replication_outcomes_2024_v01.py = 071b9dd3810475bf2d4619f40f0d5761f9e0202f
- replication_adjudicate_2024_v01.py = b185e8a807c19cbd8c33686a0292dc23d63dcc77

Frozen execution semantics:
- 366 predictor snapshots: 2024-01-01..2024-12-31 inclusive;
- 365 complete next-24h outcome pairs: 2024-01-01..2024-12-30;
- 2024-12-31 predictor right-censored only because opening its full outcome would cross the hard 2025 firewall;
- exact 37-reserve canonical master and point-in-time state;
- identical HF/eMode/oracle logic;
- 10% primary shock;
- identical Spearman + stationary bootstrap (block 7, 10,000, seed 20260918);
- no market returns, PnL or trading.

Any change to these six blobs after this freeze requires a new prospective remediation document before re-execution.
