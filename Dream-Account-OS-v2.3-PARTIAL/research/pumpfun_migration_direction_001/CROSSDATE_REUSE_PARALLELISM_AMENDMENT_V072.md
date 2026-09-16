# PMD-001 — CROSS-DATE REUSE PARALLELISM AMENDMENT V0.7.2

Date: 2026-09-16
Status: **PRE-OUTCOME / SOURCE-ONLY / FAIL-CLOSED**
Branch: `pumpfun-migration-direction-v0.1`

## Purpose

Reduce wall-clock time of the already-frozen V0.7.1 evidence-reuse cross-date gate. This amendment changes only execution partitioning. It does not change source semantics, population, boundary logic, feature window, eligibility, thresholds, provider class or any economic rule.

## Scientific method inherited unchanged

V0.7.2 inherits `CROSSDATE_EVIDENCE_REUSE_TRANSPORT_AMENDMENT_V071.md` exactly:
- same 20 mandatory rows and dates;
- same V0.6 immutable finalized block artifacts from run `35132853202`;
- same canonical-block hash verification before reuse;
- same V0.7 `migrate + migrate_v2` parser;
- same unique canonical Pump migration -> PumpSwap `CreatePool` boundary `T*`;
- same finalized signature pagination;
- same exact `[T* - 300s, T*)` source window;
- same gap-only block fetch from the public Solana RPC;
- same `(blockTime, slot, transaction_index)` ordering;
- same `source_complete` and `feature_source_eligible` definitions;
- same outcome wall.

## Only execution change

The 20 mandatory rows are executed as 20 deterministic shards indexed 0..19.

- each shard downloads only its matching frozen V0.6 row artifact;
- each shard runs the identical V0.7.1 row reconstruction;
- up to 10 independent runners may execute concurrently;
- no row may be replaced, skipped or retried with different semantics;
- no row shard has scientific verdict authority.

Only a final aggregate over all 20 row receipts may classify the gate.

## Aggregate PASS

`CHAIN_EXACT_CROSSDATE_V072_REUSE_PASS` requires exactly:
- 20 row receipts;
- indices exactly 0..19 once each;
- 20 unique frozen mints;
- 20 distinct migration dates;
- 20/20 unique V0.7 chain boundaries;
- 20/20 `source_complete`;
- 20/20 `feature_source_eligible`;
- zero malformed receipts;
- outcome wall intact.

Anything less is FAIL or TECHNICAL_INCOMPLETE and does not authorize the 1,012-row ceiling.

## Prerequisite equivalence

A V0.7.2 PASS is scientifically equivalent to `CHAIN_EXACT_CROSSDATE_V071_REUSE_PASS` and `CHAIN_EXACT_CROSSDATE_V07_PASS` solely for satisfying the frozen pre-outcome cross-date prerequisite. This equivalence follows because the ledger evidence and all scientific semantics are identical; only deterministic execution partitioning differs.

## Governance unchanged

- research-only;
- outcome-blind;
- fail-closed;
- no threshold rescue;
- no candidate substitution;
- no post-migration prices, returns, direction labels or PnL;
- no live trading or exchange mutation;
- no merge to main.
