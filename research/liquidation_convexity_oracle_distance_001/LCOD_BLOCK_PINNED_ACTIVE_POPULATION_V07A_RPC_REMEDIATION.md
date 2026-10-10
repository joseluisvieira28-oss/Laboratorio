# LCOD BLOCK-PINNED ACTIVE POPULATION V0.7A — RPC REMEDIATION

Date: 2026-09-25
Science change: NONE

V0.7 produced:
- 14 / 16 shards PASS;
- shards 14 and 15 completed SQD Borrow streaming with zero decode errors;
- shard 14 lost 78 UAD calls;
- shard 15 lost 72 UAD calls;
- the loss pattern is consistent with a large public-RPC JSON batch being
  rejected/partially dropped under concurrent load.

No canonical population receipt passed and no curve/outcome was opened.

V0.8 preserves:
- same 13 official lending Spokes;
- one common finalized block N per run;
- same full Borrow-history candidate universe;
- ACTIVE_DEBT_N iff totalDebtValueRay > 0;
- no raw wallet persistence.

Technical changes only:
- UAD JSON-RPC batch size 80 -> 20;
- failed/missing calls retried individually up to 5 times;
- 120 ms inter-batch pause;
- workflow max-parallel 16 -> 8.

PASS criteria are unchanged.
