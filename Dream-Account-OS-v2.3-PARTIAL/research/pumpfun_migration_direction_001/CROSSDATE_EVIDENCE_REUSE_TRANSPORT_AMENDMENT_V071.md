# PMD-001 — CROSS-DATE EVIDENCE REUSE TRANSPORT AMENDMENT V0.7.1

Date: 2026-09-16
Status: **PRE-OUTCOME / SOURCE-ONLY / FAIL-CLOSED**
Branch: `pumpfun-migration-direction-v0.1`

## Purpose

Accelerate the already-frozen V0.7 20-date source gate without changing any scientific population, boundary rule, feature window, threshold or economic rule.

The prior V0.6 run `35132853202` already persisted finalized full-block evidence for all 20 mandatory rows. Offline V0.7 re-adjudication of those immutable artifacts resolved exactly 20/20 unique canonical migration boundaries: 10 legacy `migrate` and 10 `migrate_v2`. The 10 V0.6 failures were parser-coverage failures.

Across the frozen 20 rows, the exact chain boundary `T*` is only 0.579078 to 2.576055 seconds earlier than corpus T0. Therefore the V0.6 persisted block set already overlaps almost the entire exact `[T* - 300s, T*)` source window.

## Frozen V0.7.1 transport method

For each of the same 20 mandatory rows:

1. use only the V0.6 full-block artifact from run `35132853202` as the persisted block-evidence base;
2. recompute and verify persisted canonical block hashes before reuse;
3. apply the frozen V0.7 `migrate + migrate_v2` parser to locate exactly one successful canonical Pump migration that invokes PumpSwap `CreatePool` for frozen mint + bonding-curve PDA + canonical pool;
4. define the same chain-exact `T* = (block_time, slot, transaction_index)`;
5. query finalized `getSignaturesForAddress` only to enumerate the complete bonding-curve-PDA signature set covering `[T* - 300s, T*]` and prove pagination completeness;
6. reuse any required full block already present in the V0.6 artifact;
7. fetch from the same public Solana RPC only those required feature-window slots that are absent from the persisted V0.6 artifact (expected only near the re-anchored lower edge);
8. persist hashes/retrieval timestamps for every newly fetched gap block;
9. locate every causally pre-boundary signature body in its finalized block and resolve same-second ordering by `(blockTime, slot, transaction_index)`;
10. preserve the unchanged source-eligibility semantics: source-complete exact 300-second reconstruction plus at least one successful pre-boundary transaction matching frozen Pump program + mint + bonding-curve PDA.

No V0.6 classification is trusted as a V0.7 result; only raw finalized block evidence is reused.

## Completeness requirements per row

A row is `source_complete` only if all are true:
- persisted block evidence has zero hash mismatch and zero stored block error for every reused required slot;
- signature pagination crosses/exhausts the exact 300-second lower boundary with zero conflicts and zero null blockTime contamination;
- exactly one V0.7 canonical pool-creation boundary is found;
- every signature causally inside `[T* - 300s, T*)` resolves to exactly one transaction body in a verified reused or newly fetched finalized block;
- every newly required gap block is fetched successfully and hash-recorded;
- same-boundary-second ordering is fully resolved;
- outcome wall remains intact.

## Gate

This is the same 20-row scientific gate, not a reduced diagnostic.

`CHAIN_EXACT_CROSSDATE_V071_REUSE_PASS` requires exactly:
- 20/20 frozen rows reconciled;
- 20 unique indices, mints and dates;
- 20/20 unique V0.7 boundaries;
- 20/20 `source_complete`;
- 20/20 `feature_source_eligible`;
- zero outcome access.

Anything less is `CHAIN_EXACT_CROSSDATE_V071_REUSE_FAIL` or technical incomplete and does not authorize the 1,012-row ceiling.

A V0.7.1 PASS is scientifically equivalent to `CHAIN_EXACT_CROSSDATE_V07_PASS` for the sole purpose of satisfying the pre-outcome cross-date prerequisite, because it reconstructs the same rows, same finalized ledger, same V0.7 parser, same boundary and same exact source window. It changes only transport/evidence reuse.

## Unchanged governance

- frozen 1,012-row population and 20 mandatory cross-date rows;
- no candidate substitution;
- no post-migration price/return/direction/PnL;
- no `postgard_outcomes.parquet`;
- no feature/outcome correlation;
- no threshold rescue;
- no live trading or exchange mutation;
- no main merge.
