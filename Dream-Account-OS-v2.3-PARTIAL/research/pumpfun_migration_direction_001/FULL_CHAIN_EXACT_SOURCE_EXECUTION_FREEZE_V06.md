# PMD-001 — FULL CHAIN-EXACT SOURCE EXECUTION FREEZE V0.6

Date: 2026-09-16
Status: **PRE-OUTCOME / INERT UNTIL CHAIN_EXACT_CROSSDATE_V06_PASS**
Branch: `pumpfun-migration-direction-v0.1`

## Prerequisite

No full-population V0.6 execution is authorized unless the frozen 20-date gate returns exactly:

`CHAIN_EXACT_CROSSDATE_V06_PASS`

If the 20-date gate fails or remains technically incomplete, this plan remains inert.

## Frozen population

The full candidate population remains exactly:
- 1,012 rows;
- 20 migration dates;
- manifest SHA-256 `56a8836921b7d348597fa3e63f210adbfe8f34bd67321af797855d23c364243b`.

No candidate may be added, removed or replaced because of source accessibility or later results.

## Stage A — chain-exact signature/boundary ceiling

The purpose of the ceiling is to determine whether the frozen 1,012-row population can support the unchanged minimum source scale before expensive full feature-block reconstruction.

For every frozen candidate:

1. derive the Pump bonding-curve PDA;
2. retrieve complete finalized signature metadata far enough backward to cover the maximum required chain-exact window (`corpus_T0 - 600s` retrieval envelope);
3. within the frozen boundary-search horizon `[corpus_T0 - 300s, floor(corpus_T0)]`, retrieve transaction bodies for every bonding-curve-PDA signature;
4. locate the unique successful Pump `migrate` call that matches frozen mint + PDA + canonical pool and whose logs show PumpSwap `CreatePool`;
5. reject later idempotent `Bonding curve already migrated` calls as boundaries;
6. retrieve the finalized full boundary block and locate the exact migration transaction index;
7. define chain boundary `T* = (block_time, slot, transaction_index)`;
8. count successful bonding-curve signatures strictly inside `[T* - 300s, T*)`, resolving same-boundary-second order using slot and boundary-block transaction index;
9. open no transaction-derived economic feature and no post-migration outcome.

### Ceiling completeness

A candidate's ceiling history is resolved only if:
- signature pagination is complete/fail-closed through the required retrieval envelope;
- no signature metadata conflict/null-time contamination exists;
- every boundary-search transaction body is retrieved successfully;
- exactly one qualifying `CreatePool` migration boundary exists;
- the boundary full block is complete and contains the migration signature exactly once;
- `T*` is no later than corpus `T0` and no earlier than the frozen 300-second boundary-search lower bound.

### Ceiling verdicts

The sole full-population ceiling verdict is produced after exact reconciliation of all 1,012 candidates:

- `CHAIN_EXACT_CEILING_VIABLE`: all 1,012 ceiling histories resolved AND at least 1,000 candidates have at least one successful signature strictly inside `[T* - 300s, T*)`;
- `CHAIN_EXACT_CEILING_INSUFFICIENT`: all 1,012 ceiling histories resolved BUT fewer than 1,000 candidates have such evidence;
- `CHAIN_EXACT_CEILING_UNRESOLVED`: any candidate/history/reconciliation remains technically unresolved.

No partial-population inference is permitted.

The minimum viable count remains exactly 1,000.

## Deterministic ceiling sharding

The 1,012 candidates may be collected in four fixed contiguous shards:
- start 0, limit 253;
- start 253, limit 253;
- start 506, limit 253;
- start 759, limit 253.

The four ceiling shards may execute on independent runners in parallel because every row is mandatory in final reconciliation and no shard has scientific verdict authority.

Only the aggregate 1,012-row receipt may emit a ceiling verdict.

## Stage B — full chain-exact block reconstruction

Authorized only if Stage A returns `CHAIN_EXACT_CEILING_VIABLE`.

Use `source_rebuild_chain_exact_v06.py` on the exact same 1,012 rows and the exact same chain-boundary method.

For each candidate reconstruct the unchanged 300-second source window `[T* - 300s, T*)` from finalized full blocks, preserving exact pre-boundary transaction bodies and auditable block hashes/retrieval timestamps.

### Full reconstruction sharding

Use exactly four fixed shards:
- 0..252;
- 253..505;
- 506..758;
- 759..1011.

To reduce public-RPC pressure and preserve the prior conservative execution posture, the full block shards remain `max-parallel: 1`.

No failed shard/candidate may be dropped or replaced.

## Final V0.6 Source Gate

After exact reconciliation of all 1,012 full reconstruction rows:

`CHAIN_EXACT_SOURCE_GATE_PASS` requires all of:
- exactly 1,012 reconciled rows;
- exactly 1,012 unique frozen mints;
- zero duplicate/missing rows;
- at least 1,000 `feature_source_eligible == true`;
- at least 20 distinct migration dates represented among eligible rows;
- outcome wall intact.

If the 1,012 rows reconcile but fewer than 1,000 are eligible or fewer than 20 dates are eligible:

`CHAIN_EXACT_SOURCE_GATE_INSUFFICIENT_SAMPLE`

If population/evidence reconciliation is incomplete:

`CHAIN_EXACT_SOURCE_GATE_TECHNICAL_INCOMPLETE`

## Source eligibility semantics

To preserve the earlier source gate rather than silently strengthening it, `feature_source_eligible` at this stage means:
- source-complete chain-exact 300-second reconstruction;
- at least one successful pre-boundary transaction that matches Pump program + frozen mint + bonding-curve PDA.

Exact feature formulas remain a later freeze and are not selected here.

## Outcome wall

Throughout Stage A and Stage B forbidden data/analysis remain:
- `postgard_outcomes.parquet`;
- post-migration price/return/direction/PnL;
- feature/outcome correlations;
- Discovery/Validation/Holdout outcomes.

A final Source Gate PASS still does not authorize economic outcomes until feature formulas and split manifests are separately frozen under the existing protocol.

## Governance unchanged

- research-only;
- fail-closed;
- no threshold rescue;
- no cherry-picking;
- no post-outcome tuning;
- no live trading or exchange mutation;
- no merge to main.
