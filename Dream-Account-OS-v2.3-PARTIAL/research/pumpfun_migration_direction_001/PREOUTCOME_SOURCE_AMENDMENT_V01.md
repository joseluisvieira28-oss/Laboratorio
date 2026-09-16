# PMD-001 — PRE-OUTCOME SOURCE AMENDMENT V0.1

Status: RESEARCH-ONLY / FAIL-CLOSED / OUTCOME-BLIND
Date: 2026-09-16
Applies to: `PROTOCOL_FREEZE_V01.md`

## Why this amendment exists

The initial source profile was performed without reading any post-migration price value and without computing any return or outcome label.

It showed that the originally specified `T0+15s .. T0+60s` entry window and `+30s` exit-target tolerance were not aligned with the cadence of the published `postgard_snapshots.parquet` source. The initial strict join left only 84 observations after additionally requiring aggregate pre-migration snapshot coverage. That was classified as a source-resolution failure, not an economic result.

A dedicated outcome-blind timestamp diagnostic then inspected only:
- migration timestamp;
- canonical pool identity;
- post snapshot timestamp;
- DEX identity;
- `incomplete_data`;
- whether `price_native` is non-null.

No price values, returns, PnL, direction labels, feature/outcome correlations or outcome file were opened.

## Observed source cadence

For the clean primary base population (real canonical pool, non-Mayhem, excluding 2026-07-03):
- base rows: 2,048;
- exact canonical PumpSwap pool observations existed for 1,973 mints;
- with the economic guard `entry >= T0+15s`, entry availability was 649 by +60s, 1,152 by +90s, and 1,173 by +120s;
- requiring a valid +5 minute exit with a maximum +120s source delay left 510 cases at a +60s entry cap, 1,012 cases at +90s, and 1,033 cases at +120s;
- all these retained 20 distinct migration dates;
- availability plateaus at +120s and then jumps to much later observations, so extending beyond +120s adds no useful near-event coverage.

## Frozen source-resolution correction

The following replaces only the bounded snapshot availability windows in Protocol Freeze V0.1. The economic horizon and cost stress do not change.

### Entry

Entry price = first valid price observation from the exact canonical PumpSwap pool timestamped:

`T0 + 15 seconds <= entry_timestamp <= T0 + 90 seconds`

The +15s lower bound is preserved to avoid assuming instantaneous migration fills.

The +90s upper bound is frozen because it is the **smallest tested source cap** that satisfies the already-frozen total sample gate once the +5m exit availability rule below is also applied. It was selected without price values or outcomes.

### Primary exit

Target = `entry_timestamp + 300 seconds`.

Exit price = first valid price observation from the exact canonical PumpSwap pool at or after the target, provided:

`0 <= exit_timestamp - target <= 120 seconds`.

The +120s source tolerance is the smallest tested exit tolerance that, together with the +90s entry cap, satisfies the already-frozen >=1,000 total sample requirement. No post-migration price value or return was used in selecting it.

### Resulting pre-feature source ceiling

Before requiring raw pre-migration trade coverage, this rule yields 1,012 candidate migrations across 20 dates.

Under the pre-existing 60/20/20 chronological count split this is sufficient in principle for:
- Discovery: 607 observations;
- Validation: 202 observations;
- Protected Holdout: 203 observations.

The final eligible count may only decrease after raw pre-migration trade integrity requirements are applied. If it drops below any frozen minimum sample gate, PMD-001 V0.1 fails closed. Sample thresholds may not be lowered.

## Pre-migration source correction

Aggregate `snapshots.parquet` is not authoritative for the final seconds before migration because its buckets are 60/300/1800/3600 seconds and `bucket_start` does not guarantee a truly contemporaneous final-window observation for every token.

Therefore, all primary final-curve flow/breadth/velocity features must be reconstructed from timestamped raw `trades/*.parquet` rows strictly before `T0`.

Aggregate snapshots may be used only for source diagnostics or a feature whose timestamp semantics prove point-in-time safe in a separate pre-outcome freeze. They cannot be used as a substitute for missing raw final-window trades.

## Unchanged rules

Everything else remains frozen:
- causal thesis: fresh-demand absorption versus latent sell supply;
- feature cutoff strictly `< T0`;
- primary horizon = 5 minutes from actual entry;
- 3.00 percentage-point round-trip execution stress;
- pre-BOOST population only;
- Mayhem excluded;
- 2026-07-03 excluded;
- chronological 60/20/20 partitions;
- no outcomes before source gate + feature formula freeze + partition manifest;
- no threshold rescue;
- no post-outcome tuning;
- no live trading or exchange mutation;
- no merge to main.
