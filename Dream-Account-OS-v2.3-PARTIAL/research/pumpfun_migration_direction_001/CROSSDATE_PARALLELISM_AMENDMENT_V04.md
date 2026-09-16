# PMD-001 — CROSS-DATE PARALLELISM AMENDMENT V0.4

Status: RESEARCH-ONLY / FAIL-CLOSED / PRE-OUTCOME
Branch: `pumpfun-migration-direction-v0.1`
Date: 2026-09-16

## Purpose

The deterministic 20-date cross-date audit is already frozen to exactly one preselected mint per date. V0.3 preserves the scientific method but a single runner remains a throughput bottleneck because one mint can require many finalized block fetches.

Before any economic outcome is opened, this amendment authorizes execution-only sharding of the exact same 20 deterministic cases.

## Population unchanged

The authoritative 1,012-candidate manifest remains frozen at SHA-256:

`56a8836921b7d348597fa3e63f210adbfe8f34bd67321af797855d23c364243b`

The cross-date sample remains exactly the deterministic 20-row manifest produced by `build_crossdate_probe20_manifest_v01.py`: one mint per each of the 20 migration dates, first candidate in frozen chronological `(T0, mint)` order for that date.

No mint or date may be substituted because of latency, errors, missing blocks or provider behavior.

## Execution-only sharding

The 20-row cross-date manifest may be partitioned mechanically into 20 single-row jobs by frozen manifest index 0..19.

All jobs:
- use the same public Solana RPC provider class;
- use the V0.3 batch-json collector;
- use the same Pump bonding-curve PDA derivation;
- use `[T0-300s, floor(T0))`;
- quarantine the integer second containing T0;
- fetch every unique eligible signature slot with finalized full `getBlock` transaction detail;
- preserve full blocks for cross-date forensic evidence;
- preserve canonical block SHA-256 and UTC retrieval timestamp;
- remain outcome-blind.

Parallel runner execution is authorized because every frozen row is mandatory in final reconciliation. Provider or runner failures cannot remove or replace a row and therefore cannot become hidden sample selection.

## Aggregate-only verdict

Individual row jobs have no scientific PASS/FAIL authority.

The only cross-date verdict is emitted after aggregate reconciliation of exactly:
- 20 rows;
- 20 unique mints;
- 20 distinct migration dates;
- the full index set 0..19;
- zero duplicate indices;
- zero duplicate mints;
- no economic outcomes opened.

`BLOCK_FIRST_CROSSDATE_V04_PASS` requires all 20 rows `source_complete == true` and all 20 rows `feature_source_eligible == true`.

If all 20 rows reconcile but fewer than 20 are complete/eligible, verdict is `BLOCK_FIRST_CROSSDATE_V04_PARTIAL_OR_FAIL`.

If the 20-row population cannot be reconciled exactly, verdict is `BLOCK_FIRST_CROSSDATE_V04_TECHNICAL_INCOMPLETE`.

No threshold relaxation is authorized.

## Authority relationship

V0.4 changes transport scheduling only. It does not change the scientific sample, source semantics, block representation or feature eligibility rules frozen in V0.2/V0.3.

If V0.3 monolithic evidence later completes, any material contradiction with V0.4 must be investigated fail-closed before later scientific gates are opened.

## Outcome wall

No post-migration price, return, direction label, PnL, Discovery statistic, Validation statistic or Holdout data may be opened during this amendment or its execution.

## Governance unchanged

- research-only;
- fail-closed;
- no exchange mutation;
- no live orders;
- no main merge;
- no post-outcome tuning;
- no cherry-picking;
- no rescue thresholds.
