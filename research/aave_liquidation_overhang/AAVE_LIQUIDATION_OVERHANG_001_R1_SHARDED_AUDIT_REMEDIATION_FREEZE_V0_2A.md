# AAVE-LIQUIDATION-OVERHANG-001 — R1 SHARDED AUDIT REMEDIATION FREEZE V0.2A

Date: 2026-09-18
Branch: aave-liquidation-overhang-v0.1
Status: FROZEN BEFORE SHARDED EXECUTION / OPERATIONAL-ONLY / OUTCOME-BLIND

## Why remediation is required

The frozen monolithic R1 scaled-ledger audit was attempted twice without producing a scientific receipt:

- run 35226616121: cancelled at the original 45-minute workflow wall-clock limit;
- run 35355395431: cancelled at the remediated 120-minute workflow wall-clock limit.

Both cancellations occurred inside the same deterministic scaled-ledger replay step. Neither run emitted the canonical R1 audit receipt. Therefore neither run is a scientific or reconstruction verdict.

Classification of both: OPERATIONAL_WALL_CLOCK_CANCELLATION / NO_SCIENTIFIC_VERDICT.

The failed continuation run 35355593345 is also operational-only: it correctly failed closed because the exact pinned upstream audit did not complete successfully.

## Frozen scientific contract preserved

This remediation does NOT change:

- lab: AAVE-LIQUIDATION-OVERHANG-001;
- protocol: AAVE_LIQUIDATION_OVERHANG_001_R1_EXECUTION_PROTOCOL_V0_2;
- canonical R0 bootstrap;
- full historical block envelope: 16,490,000 through 21,525,890 inclusive;
- Borrow canonical count requirement: 204,952;
- borrower identity: Borrow.onBehalfOf;
- borrower ranking: (keccak256(raw 20-byte address), address);
- sample size: first 16 ranked unique borrowers;
- exact 37-reserve token universe;
- Mint/Burn/BalanceTransfer semantics;
- token-native ray arithmetic;
- variable-debt non-transferability check;
- audit blocks: 17,748,972; 19,007,945; 20,266,917; 21,525,890;
- replay definition: cumulative scaled-token delta at or before each audit block;
- archive RPC set, batch semantics, quorum and exact-equality requirements;
- all R1 classifications and fail-closed rules;
- all protected-period firewalls.

## Only operational change: deterministic block sharding

The full inclusive block envelope is partitioned into exactly 8 disjoint contiguous shards:

0. 16,490,000 .. 17,119,486
1. 17,119,487 .. 17,748,973
2. 17,748,974 .. 18,378,460
3. 18,378,461 .. 19,007,946
4. 19,007,947 .. 19,637,432
5. 19,637,433 .. 20,266,918
6. 20,266,919 .. 20,896,404
7. 20,896,405 .. 21,525,890

Union = exact original envelope. Intersection between any two shards = empty.

### Stage A — Borrow census shards

Each shard retrieves only the original Pool Borrow logs inside its own block interval and preserves canonical transactionHash+logIndex uniqueness, Borrow log count, and unique onBehalfOf borrower addresses.

The aggregate must:
- receive all 8 exact shard ranges;
- sum to exactly 204,952 canonical Borrow logs;
- reject cross-shard canonical-log duplicates;
- union all borrowers;
- apply the original deterministic ranking once;
- select exactly 16 borrowers.

No shard may choose borrowers independently.

### Stage B — scaled-token delta shards

Every shard receives the exact aggregated 16-borrower sample plus the canonical R0 bootstrap.

Within only its frozen block range it executes the same original token address universe, Mint filter/decoder, Burn filter/decoder, aToken BalanceTransfer filter/decoder, variable-debt BalanceTransfer provenance check, ray arithmetic, and filter-overlap deduplication.

Each shard emits only raw deterministic delta ledger material and source/provenance counters. It does NOT replay final audit balances and does NOT validate RPC targets independently.

### Stage C — canonical aggregate and validation

The aggregate:
1. requires all 8 exact shard ranges;
2. merges delta entries keyed by user, token and block;
3. sums event counters and variable-debt BalanceTransfer count;
4. reconstructs the exact full-envelope cumulative ledger;
5. calls the original replay logic against all four frozen audit blocks;
6. performs the original archive-RPC validation on the complete target set;
7. emits the only canonical R1 audit classification.

No failed shard, borrower, reserve, target or audit block may be dropped or replaced.

## Equivalence guard

Before network execution, a synthetic split/merge QA must prove that partitioning an artificial delta ledger across these 8 ranges, merging it, and replaying the merged ledger produces byte-equivalent canonical target tuples to replaying the same artificial ledger monolithically.

Static compile + equivalence QA must pass before source execution.

## Safety

Still forbidden:
- health factor;
- liquidation-overhang predictor;
- adverse-shock definition;
- future liquidation outcomes;
- market-return prices;
- returns/PnL/PF/win-rate/drawdown;
- 2025/2026 access;
- trading, exchange mutation, wallets, orders, alerts/webhooks;
- merge to main;
- tuning or removal of inconvenient source rows.

Only a final canonical R1_AUDIT_PASS permits the already-frozen R1 reconstruction continuation.
