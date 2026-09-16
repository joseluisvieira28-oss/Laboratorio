# PMD-001 — FULL CHAIN-EXACT SOURCE EXECUTION AMENDMENT V0.7

Date: 2026-09-16
Status: **PRE-OUTCOME / INERT UNTIL CHAIN_EXACT_CROSSDATE_V07_PASS**
Branch: `pumpfun-migration-direction-v0.1`

This amendment inherits `FULL_CHAIN_EXACT_SOURCE_EXECUTION_FREEZE_V06.md` in full except for the migration parser version and prerequisite named below.

## Mandatory prerequisite

No 1,012-row ceiling or full reconstruction may execute unless the frozen 20-date V0.7 gate returns exactly:

`CHAIN_EXACT_CROSSDATE_V07_PASS`

The V0.6 result `CHAIN_EXACT_CROSSDATE_V06_FAIL` remains part of the audit trail and is not overwritten. V0.7 exists because finalized V0.6 block evidence proved that mandatory failure rows used Pump `migrate_v2`, which V0.6 did not parse.

## Boundary parser V0.7

For all Stage A and Stage B operations, the authoritative migration parser is `MIGRATE_V2_PARSER_AMENDMENT_V07.md` / `chain_boundary_semantics_v07.py`.

Exactly these two Pump outer-instruction discriminators are supported:

- `migrate`: `[155,234,231,146,236,158,162,30]`;
- `migrate_v2`: `[187,203,18,31,206,237,254,41]`.

All other V0.6 chain-boundary requirements remain mandatory: successful transaction, frozen Pump program, exact mint + bonding-curve PDA + frozen canonical pool, PumpSwap `CreatePool`, frozen PumpSwap AMM invocation, no `Bonding curve already migrated`, and exactly one qualifying boundary inside the frozen search horizon.

## Stage A — unchanged ceiling governance

Population remains exactly 1,012 frozen rows / 20 dates / manifest SHA-256:

`56a8836921b7d348597fa3e63f210adbfe8f34bd67321af797855d23c364243b`

Four deterministic shards remain:
- start 0, limit 253;
- start 253, limit 253;
- start 506, limit 253;
- start 759, limit 253.

Ceiling shards may run in parallel because none has verdict authority.

Only the reconciled 1,012-row aggregate can emit:

- `CHAIN_EXACT_CEILING_V07_VIABLE`: all 1,012 histories resolved and >=1,000 rows have at least one successful signature strictly inside `[T* - 300s, T*)`;
- `CHAIN_EXACT_CEILING_V07_INSUFFICIENT`: all 1,012 histories resolved but fewer than 1,000 meet that evidence condition;
- `CHAIN_EXACT_CEILING_V07_UNRESOLVED`: any row/history/reconciliation is unresolved.

Minimum viable count remains exactly 1,000.

## Stage B — unchanged full reconstruction governance

Authorized only after `CHAIN_EXACT_CEILING_V07_VIABLE`.

Use the V0.7 parser with the same 1,012 rows and same 300-second chain-exact feature window.

Four deterministic shards remain 253 rows each and execute with `max-parallel: 1`:
- 0..252;
- 253..505;
- 506..758;
- 759..1011.

No failed row or shard may be dropped or replaced.

Full-block payload persistence may be omitted for the 1,012-row run under `BLOCK_EVIDENCE_STORAGE_AMENDMENT_V02.md`, provided compact block ledgers, canonical block hashes, retrieval timestamps and exact matched pre-boundary transaction bodies remain preserved.

## Final Source Gate

The V0.7 final Source Gate retains the V0.6 criteria exactly:

`CHAIN_EXACT_SOURCE_GATE_V07_PASS` requires:
- exactly 1,012 reconciled rows;
- exactly 1,012 unique frozen mints;
- zero duplicate/missing rows;
- >=1,000 `feature_source_eligible == true`;
- >=20 distinct migration dates among eligible rows;
- outcome wall intact.

If rows reconcile but scale/date gates fail: `CHAIN_EXACT_SOURCE_GATE_V07_INSUFFICIENT_SAMPLE`.

If population/evidence reconciliation is technically incomplete: `CHAIN_EXACT_SOURCE_GATE_V07_TECHNICAL_INCOMPLETE`.

No new source-completeness threshold is introduced beyond the frozen V0.6 criteria.

## Outcome wall and governance

Still forbidden throughout this source campaign:
- post-migration prices/returns/direction/PnL;
- `postgard_outcomes.parquet`;
- feature/outcome correlations;
- Discovery, Validation or Holdout economic results;
- threshold rescue or candidate substitution;
- live trading or exchange mutation;
- merge to main.

A Source Gate PASS still does **not** authorize outcomes until exact feature formulas, transaction-event parser semantics and chronological partition membership are separately frozen.
