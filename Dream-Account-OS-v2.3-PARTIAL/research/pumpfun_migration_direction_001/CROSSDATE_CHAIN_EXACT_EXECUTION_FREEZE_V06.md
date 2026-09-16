# PMD-001 — CROSS-DATE CHAIN-EXACT EXECUTION FREEZE V0.6

Date: 2026-09-16
Status: **PRE-OUTCOME / INERT UNTIL V0.6 FEASIBILITY PASS**
Branch: `pumpfun-migration-direction-v0.1`

## Authority dependency

This execution is authorized to run only if `CHAIN_EXACT_BOUNDARY_FEASIBILITY_V06` returns `CHAIN_EXACT_BOUNDARY_METHOD_FEASIBLE` on all four pre-frozen feasibility probes.

If feasibility does not pass, this execution remains inert.

## Frozen population

Use exactly the deterministic 20-row cross-date manifest already frozen by `build_crossdate_probe20_manifest_v01.py`:
- source full manifest: exactly 1,012 rows;
- source full manifest SHA-256: `56a8836921b7d348597fa3e63f210adbfe8f34bd67321af797855d23c364243b`;
- one deterministic earliest `(t0, mint)` candidate per each of the 20 UTC migration dates;
- no replacement mint/date.

## Source method

For every one of the 20 candidates apply `CHAIN_EXACT_MIGRATION_BOUNDARY_AUTHORITY_V06.md` and `source_rebuild_chain_exact_v06.py`:
- locate the unique successful Pump `migrate` that actually executes PumpSwap `CreatePool` for the frozen canonical pool;
- reject idempotent `Bonding curve already migrated` calls as boundaries;
- require the boundary no later than corpus `T0` and within the existing 300-second boundary-search horizon;
- define exact ledger boundary by `(block_time, slot, transaction_index)`;
- re-anchor the unchanged 300-second predictive source window to `[T* - 300s, T*)`;
- exclude every transaction at or after `T*` even if corpus `T0` is later;
- allow same-second transactions only when their exact ledger order is strictly before `T*`.

## Retrieval envelope

A 600-second metadata retrieval envelope before corpus `T0` is authorized solely to guarantee complete coverage of the 300-second feature window when `T*` occurs up to 300 seconds before corpus `T0`.

This is transport/source coverage only. The feature window remains exactly 300 seconds.

## Cross-date PASS rule

The cross-date V0.6 source gate is deliberately unchanged in severity.

`CHAIN_EXACT_CROSSDATE_V06_PASS` requires all of:
- exactly 20 reconciled mandatory rows;
- exactly 20 unique mints;
- exactly 20 distinct frozen migration dates;
- all 20 `source_complete == true`;
- all 20 `feature_source_eligible == true`;
- exact index set 0..19;
- no duplicate indices or mints;
- outcome wall intact.

Any resolved row that is not source-complete or not feature-source-eligible prevents PASS.

Missing/unreconciled evidence => `CHAIN_EXACT_CROSSDATE_V06_TECHNICAL_INCOMPLETE`.

Complete 20-row reconciliation with fewer than 20 complete/eligible rows => `CHAIN_EXACT_CROSSDATE_V06_FAIL`.

No threshold relaxation is authorized.

## Parallelism

The exact 20 mandatory candidates may run as independent one-row jobs, with up to 10 runners in parallel. Parallelism changes only wall-clock transport.

Every row is mandatory in final reconciliation; latency or provider errors cannot remove or replace a row.

## Downstream rule

Only `CHAIN_EXACT_CROSSDATE_V06_PASS` may authorize preparation/execution of a full 1,012-row V0.6 source ceiling/rebuild.

Even a cross-date PASS does not authorize economic outcomes.

## Outcome wall and governance

Forbidden:
- `postgard_outcomes.parquet`;
- post-migration prices;
- direction labels;
- returns/PnL;
- Discovery/Validation/Holdout outcomes;
- threshold rescue;
- live trading/exchange mutation;
- merge to main.
