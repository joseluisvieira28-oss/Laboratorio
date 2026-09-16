# PMD-001 — SIGNATURE CEILING SHARDING AMENDMENT V0.1

Status: RESEARCH-ONLY / FAIL-CLOSED / PRE-OUTCOME
Branch: `pumpfun-migration-direction-v0.1`
Date: 2026-09-16

## Purpose

`FULL_SOURCE_REBUILD_EXECUTION_FREEZE_V02.md` freezes the signature ceiling on the complete 1,012-candidate population. This amendment changes execution transport only so the same complete ceiling can be collected in deterministic slices without changing any scientific rule.

No economic outcome has been opened to justify this amendment.

## Frozen deterministic slices

The full frozen manifest remains authoritative and must first validate to exactly 1,012 rows with SHA-256:

`56a8836921b7d348597fa3e63f210adbfe8f34bd67321af797855d23c364243b`

Only these four contiguous slices are authorized:
- shard A: start 0, limit 253;
- shard B: start 253, limit 253;
- shard C: start 506, limit 253;
- shard D: start 759, limit 253.

Every shard validates the full manifest hash and 1,012-row population before slicing.

## No shard verdict

A shard can only report collection completeness for its deterministic rows. A shard MUST NOT emit `SIGNATURE_CEILING_VIABLE` or `SIGNATURE_CEILING_INSUFFICIENT` as a scientific verdict.

The only scientific signature-ceiling verdict is produced after all four shards are reconciled into exactly:
- 1,012 rows;
- 1,012 unique frozen manifest indices 0..1011;
- 1,012 unique mints;
- zero duplicate indices;
- zero duplicate mints.

Missing or unreconciled shard evidence fails closed as `SIGNATURE_CEILING_UNRESOLVED`.

## Aggregate definitions unchanged

A mint contributes to the ceiling only under the existing frozen rules:
- signature pagination is complete/fail-closed;
- no signature metadata conflicts;
- no null block-time contamination;
- at least one successful signature in `[T0-300s, floor(T0))`.

The integer second containing T0 remains quarantined.

Aggregate verdicts remain exactly:
- `SIGNATURE_CEILING_VIABLE`: all 1,012 histories resolved and >=1,000 contain successful safe-window evidence;
- `SIGNATURE_CEILING_INSUFFICIENT`: all 1,012 histories resolved but <1,000 qualify;
- `SIGNATURE_CEILING_UNRESOLVED`: any technical incompleteness or reconciliation failure.

Minimum viable ceiling remains 1,000. No threshold reduction is authorized.

## Parallel transport authority

The four signature-only shards may execute on independent runners in parallel because:
- shard membership is frozen before execution;
- every row is mandatory in final reconciliation;
- no shard can be dropped or replaced because of latency or errors;
- provider failures remain visible and force `UNRESOLVED`;
- no transaction body, price, return, direction label or PnL is read at this stage.

Parallelism changes wall-clock transport only and cannot change population membership or verdict logic.

This authority does NOT alter the full block-first reconstruction rule in `FULL_SOURCE_REBUILD_EXECUTION_FREEZE_V02.md`; the four 253-row full block shards remain sequential with `max-parallel: 1`.

## Outcome wall

No post-migration price values, returns, labels, PnL, Discovery statistics, Validation statistics or Holdout data may be opened by this ceiling execution.

## Governance unchanged

- research-only;
- fail-closed;
- no exchange mutation;
- no live orders;
- no main merge;
- no post-outcome tuning;
- no cherry-picking;
- no rescue thresholds.
