# DEX-LIQUIDITY-PROVISION-001 — SHARDED TRANSPORT AMENDMENT V0.2

Date: 2026-09-20
Status: **TRANSPORT-ONLY / SOURCE-ONLY / OUTCOME-BLIND**

The exact V0.1 source gate hit GitHub runtime limits twice without producing a scientific source verdict. No economic field or outcome was opened.

This amendment changes only transport:
- same frozen block envelope: 13,900,000..21,525,890;
- same scientific timestamp window: 2022-01-01..2024-12-31;
- same pool, factory, pair, fee tier and event topics;
- same allowed fields;
- same 12 source adequacy gates;
- same fail-closed protected-period rule;
- no log.data or economic values.

Execution is split into 8 deterministic contiguous block shards. All shard ranges must be contiguous and exactly cover the frozen envelope. The aggregate step reconstructs the global source gate, unions UTC Swap days/months/years, sums event counts, verifies exact canonical (transactionHash,logIndex) uniqueness across shards, and repeats the frozen independent RPC pool-identity quorum.

No source threshold, event definition, scientific window, hypothesis, outcome, direction or promotion criterion is changed.

2025/2026, prices, returns, realized volatility and PnL remain forbidden.
