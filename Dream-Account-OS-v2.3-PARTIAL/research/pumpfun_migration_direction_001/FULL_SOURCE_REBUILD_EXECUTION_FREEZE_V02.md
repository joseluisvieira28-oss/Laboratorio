# PMD-001 — FULL SOURCE REBUILD EXECUTION FREEZE V0.2

Status: RESEARCH-ONLY / FAIL-CLOSED / PRE-OUTCOME
Branch: `pumpfun-migration-direction-v0.1`
Date: 2026-09-16

## Authority

This document freezes the remaining Source Gate execution before any economic outcome is opened.
It does not authorize returns, PnL, post-migration direction labels, Discovery, Validation, Holdout, shadow, alerts or live trading.

`PROTOCOL_FREEZE_V01.md`, `SOURCE_REBUILD_AUTHORITY_V01.md` and `TIMESTAMP_PRECISION_CUTOFF_AMENDMENT_V01.md` remain controlling documents.

## 1. Population authority

Frozen candidate population: 1,012 outcome-blind migration candidates across 20 distinct migration dates.

Frozen manifest SHA-256:
`56a8836921b7d348597fa3e63f210adbfe8f34bd67321af797855d23c364243b`

No mint may be replaced because it is difficult to reconstruct. No manual token selection is allowed.

## 2. Timestamp precision authority

For all source-ceiling and full block reconstruction work, the integer second containing T0 is quarantined.

Feature/source eligibility window:
`[T0 - 300 seconds, floor(T0))`

Any signature with Solana `blockTime == floor(T0)` is excluded from predictive evidence. This intentionally sacrifices at most the final sub-second/second of potentially valid pre-migration activity in order to prevent same-second post-migration leakage.

## 3. Cross-date V0.2 gate

The deterministic cross-date audit uses exactly one mint per each of the 20 dates: the first candidate in frozen chronological `(T0, mint)` order for that date.

No substitutions are permitted.

Cross-date V0.2 PASS requires:
- 20/20 rows source complete;
- 20/20 rows feature-source eligible;
- 20 distinct dates;
- timestamp precision amendment applied to every row;
- no economic outcomes opened.

PARTIAL and FAIL remain source classifications only and cannot be presented as edge outcomes.

## 4. Signature ceiling gate

The signature-ceiling audit runs on all 1,012 frozen candidates and reads only Solana signature metadata for the mint-specific Pump bonding-curve PDA.

It does not read transaction outcome labels, post-migration prices or PnL.

A mint contributes to the ceiling only when:
- signature pagination is complete/fail-closed;
- no signature metadata conflicts are observed;
- no null block time contaminates the required history;
- at least one successful signature exists inside the safe pre-T0 window.

Frozen minimum viable ceiling: 1,000 mints.

Verdicts:
- `SIGNATURE_CEILING_VIABLE` when all 1,012 source histories are resolved and at least 1,000 contain successful safe-window evidence;
- `SIGNATURE_CEILING_INSUFFICIENT` when all 1,012 are resolved but fewer than 1,000 qualify;
- `SIGNATURE_CEILING_UNRESOLVED` when source access is technically incomplete.

No threshold reduction is authorized.

## 5. Full block-first reconstruction

Full reconstruction is authorized only if the signature ceiling is `SIGNATURE_CEILING_VIABLE`.

The frozen population is divided mechanically into four consecutive shards of exactly 253 rows:
- shard A: start 0, limit 253;
- shard B: start 253, limit 253;
- shard C: start 506, limit 253;
- shard D: start 759, limit 253.

The shards execute sequentially (`max-parallel: 1`) so source-provider throttling is not converted into hidden sample selection.

Every eligible signature slot is fetched through canonical `getBlock`. Transaction bodies used by the lab come only from those block responses.

## 6. Storage authority

For the full 1,012-population gate, scientific evidence consists of:
- per-mint transaction JSONL containing signature metadata and full matched transaction body;
- SHA-256 of each matched transaction response;
- compact block ledger containing mint, slot, canonical block SHA-256, source and error state;
- per-mint reconstruction summary;
- final aggregate gate receipt.

Full block payload persistence is not required for all 1,012 candidates because it materially increases storage without changing the reconstruction rule. Full blocks remain reproducible from slot + source, while their canonical response hashes are frozen in the ledger.

The smaller cross-date V0.2 audit may preserve full blocks as additional forensic evidence.

## 7. Source-complete definition

A mint is `source_complete` only when all of the following hold:
- no signature conflicts;
- no null block-time contamination;
- pagination demonstrably crosses the lower time boundary or exhausts history;
- every required slot block is returned without source error;
- every eligible signature is found exactly once in its canonical block;
- at least one eligible slot and one safe-window signature exist.

Missing data is never converted to zero activity.

## 8. Feature-source-eligible definition

A mint is `feature_source_eligible` only when:
- `source_complete == true`; and
- at least one successful target Pump transaction for the mint + bonding-curve PDA is present inside the frozen safe window.

A transaction that merely touches the PDA but is failed does not satisfy this requirement.

## 9. Full Source Gate verdict

After all four fixed shards are aggregated, PASS requires simultaneously:
- exactly 1,012 reconstructed rows;
- exactly 1,012 unique mints;
- zero duplicate mints;
- at least 1,000 `feature_source_eligible` mints;
- at least 20 distinct migration dates represented;
- timestamp precision amendment applied across all rows;
- economic outcomes still unopened.

Verdicts are frozen as:
- `SOURCE_REBUILD_GATE_PASS` when all PASS conditions are met;
- `SOURCE_REBUILD_INSUFFICIENT_SAMPLE` when the population is technically complete but fewer than 1,000 mints or fewer than 20 dates are feature-source eligible/represented;
- `SOURCE_REBUILD_TECHNICAL_INCOMPLETE` when 1,012 unique rows cannot be reconciled.

No threshold relaxation, replacement mint, alternate date sampling or provider-specific cherry-picking is authorized after execution.

## 10. What PASS would and would not mean

A Source Gate PASS proves only that the pre-migration causal feature substrate is reconstructible at the frozen scale.

It does **not** prove predictive edge.
It does **not** authorize opening returns.
It does **not** authorize model fitting.
It does **not** authorize shadow or live execution.

After PASS, the next legal steps are:
1. freeze exact feature formulas from source-complete pre-T0 data;
2. freeze hashes of the resulting feature matrix;
3. freeze chronological 60/20/20 partition membership without returns;
4. only then open Discovery outcomes under `PROTOCOL_FREEZE_V01.md`.

## Governance unchanged

- research-only;
- fail-closed;
- no exchange mutation;
- no live orders;
- no main merge;
- no post-outcome tuning;
- no cherry-picking;
- no rescue thresholds;
- no protected holdout opening before prior gates pass.
