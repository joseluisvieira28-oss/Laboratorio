# PMD-001 — CHAIN-EXACT MIGRATION BOUNDARY AUTHORITY V0.6

Date: 2026-09-16
Status: **RESEARCH-ONLY / FAIL-CLOSED / PRE-OUTCOME**
Branch: `pumpfun-migration-direction-v0.1`

## Relationship to earlier versions

This is a new source-method version. It does not modify, rescue or erase the V0.4 cross-date failure or the V0.5/V0.5.1 feasibility verdicts.

No economic outcome has been opened.

V0.4 showed that second-resolution quarantine can discard valid same-second evidence. V0.5.1 then established two additional source facts without opening outcomes:

1. the Pump `migrate` discriminator is also present in later idempotent calls whose logs state `Bonding curve already migrated`; therefore discriminator matching alone is not the exact migration boundary;
2. for two fixed positive-control rows, the transaction that actually creates the canonical PumpSwap pool occurs in the integer second immediately before the corpus `T0` second, proving that corpus `migrated_at` is not always the exact causal boundary.

The original timestamp-precision amendment explicitly reserved a future source method using the on-chain migrate instruction and transaction index. V0.6 implements that reserved path.

## Economic hypothesis unchanged

PMD-001 still asks whether information observable strictly before Pump.fun migration predicts economically tradable post-migration direction.

V0.6 changes only the authoritative source-time boundary. It does not change:
- causal thesis;
- canonical PumpSwap regime;
- feature families;
- 300-second backward window length;
- post-migration execution/cost assumptions;
- chronological split;
- minimum sample gates;
- promotion gates;
- outcome lock.

## Authoritative chain migration boundary T*

Pump program:
`6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`

PumpSwap AMM program:
`pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`

Pump `migrate` Anchor discriminator:
`[155,234,231,146,236,158,162,30]`
(hex `9beae792ec9ea21e`).

For a frozen candidate `(mint, canonical_pool, corpus_T0)`, V0.6 defines `T*` only as the unique successful finalized transaction satisfying all of:

1. an outer instruction invokes the Pump program;
2. that instruction begins with the exact Pump `migrate` discriminator;
3. its instruction accounts contain the frozen mint;
4. its instruction accounts contain the deterministically derived Pump bonding-curve PDA for that mint;
5. its instruction accounts contain the frozen canonical PumpSwap pool;
6. transaction execution succeeds (`meta.err == null`);
7. transaction logs contain `Instruction: CreatePool` during the PumpSwap migration flow;
8. the finalized full block and exact transaction body are available and hashable;
9. the boundary is not later than the integer second containing corpus `T0`;
10. the boundary is found within the already-frozen source horizon beginning at `corpus_T0 - 300s`.

Calls that match the `migrate` discriminator but log `Bonding curve already migrated` without creating the canonical pool are explicitly **not** migration boundaries.

Zero or more than one qualifying `CreatePool` migration transaction => `CHAIN_MIGRATION_BOUNDARY_UNRESOLVED` for that candidate. No nearest-timestamp or first/last-success heuristic is allowed.

## Exact ledger ordering

The authoritative boundary key is:

`T* = (migration_block_time, migration_slot, migration_transaction_index)`.

Within the boundary integer second, causal order is resolved by:

`(slot, transaction_index)`.

A source transaction is strictly pre-migration only if:
- its block time is earlier than the migration boundary second; or
- its block time equals the migration boundary second and its `(slot, transaction_index)` is lexicographically earlier than the migration boundary `(slot, transaction_index)`.

Any transaction at or after the migration boundary is forbidden from predictive features, even if its `blockTime` is earlier than corpus `T0`.

## Correct 300-second feature-source window

Once `T*` is established, the feature-source interval is re-anchored causally to:

`[T* - 300 seconds, T*)`

using the exact ordering rule above for the boundary second.

The window length remains 300 seconds; only the source boundary becomes exact. This prevents both forms of leakage observed pre-outcome:
- discarding valid transactions that occurred earlier in the same second as migration;
- incorrectly treating post-migration transactions as pre-migration when corpus `T0` lags the real migration by one or more seconds.

## Corpus T0 role after V0.6

Corpus `T0` remains a frozen candidate-alignment/source-discovery field and an upper bound for locating the chain migration. It is no longer permitted to override the exact on-chain causal boundary when the unique `CreatePool` migration is found.

No post-migration price or return is used to locate `T*`.

## First V0.6 feasibility probe

Before any 20-date or 1,012-row V0.6 execution, the same four candidates frozen in V0.5 are retained unchanged:
- index 0: `9af7PmWRca2QYmknQehoLH19jG5ss9ajYFpgL8dMpump`;
- index 1: `QHhbroZxDShtSXm9X2RqjpQP9FvpxbSTUWktPMopump`;
- index 5: `7N3RPJC7ZxXyEnVyx8i83dcKb9QjMjV34cH2VKjypump`;
- index 10: `71HtXHfexjKgem92Y5sPLPb6qkmtqWmPUzdKAcU9pump`.

V0.6 feasibility PASS requires all four to have exactly one qualifying chain migration boundary with complete block evidence and complete ordering of candidate bonding-curve transactions around that boundary.

The feasibility probe may report source-only quantities such as:
- corpus-T0 minus chain-boundary seconds;
- boundary slot/transaction index/signature;
- same-boundary-second signatures before/after boundary;
- successful target Pump buy/sell transactions strictly before boundary;
- hashes and retrieval timestamps.

No economic outcome may be read.

## Downstream authority

A four-row feasibility PASS does **not** authorize outcomes and does not directly authorize the 1,012 population.

The next permitted stage after feasibility PASS is a separately executed 20-date V0.6 cross-date source gate using the same frozen one-per-date candidates. Only after that cross-date gate passes may a full-population V0.6 source ceiling/rebuild be considered under unchanged minimum scale requirements.

## Unchanged scale gate

Any later full V0.6 source reconstruction must still meet:
- at least 1,000 feature-source-eligible migrations;
- at least 20 distinct migration dates;
- complete/fail-closed source evidence;
- no outcome opening before source and formula freezes are complete.

## Explicit prohibitions

- no retroactive V0.4 PASS;
- no replacement probe/cross-date mint;
- no post-chain-boundary predictive transaction;
- no nearest-timestamp migration heuristic;
- no reduction of >=1,000 or >=20-date gates;
- no `postgard_outcomes.parquet`;
- no return/PnL/direction inspection;
- no live trading or exchange mutation;
- no merge to main;
- no post-outcome tuning or rescue.
