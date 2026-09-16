# PMD-001 — SOURCE GATE VERDICT V0.1

Date: 2026-09-16
Status: **CLOSED PRE-OUTCOME — SOURCE_ALIGNMENT_FAILURE / INSUFFICIENT_SAMPLE**
Branch: `pumpfun-migration-direction-v0.1`

## Verdict

PMD-001 V0.1 may **not** open Discovery outcomes.

This is **not** a `NO_EDGE` verdict and **not** a negative-expectancy result. No post-migration return, PnL, direction label, feature/outcome correlation, Validation result or Protected Holdout result was opened.

The economic hypothesis remains untested. V0.1 is closed because the selected public corpus cannot supply the frozen pre-migration microstructure population at the required sample size.

## What passed

The public corpus source integrity gate verified the published hashes and schema for the required core files. `postgard_outcomes.parquet` was explicitly forbidden and remained absent.

After excluding synthetic/null pool identities, Mayhem and the 2026-07-03 outage, the post-migration source could support a frozen execution convention with:

- canonical PumpSwap pool only;
- entry no earlier than T0+15s and no later than T0+90s;
- primary horizon = 5 minutes from actual entry;
- first valid exit observation no more than 120s after the +5m target;
- frozen 3.00 percentage-point round-trip execution stress.

This produced a pre-feature source ceiling of **1,012 migrations across 20 dates**.

## What failed

All 18 raw trade shards were audited:

- raw trades: 33,581,765;
- distinct raw-trade mints: 622,870;
- post-source-executable migration universe: 1,012 across 20 dates.

Among those 1,012 migrations, the raw trade table provided:

- any human pre-migration trade at all: 472–474, depending on G0/T0 null handling;
- at least one human trade in the final 300s: 51–52;
- at least one human trade in the final 60s: 12;
- at least one human trade in the final 30s: 6.

That is far below the frozen minimum population of 1,000 and is incompatible with using the raw corpus to build the intended final-curve flow/breadth/velocity features.

## Timestamp hypothesis tested and rejected

A separate outcome-blind audit tested whether the problem came from anchoring features to `migrations.migrated_at` (T0) rather than `tokens.graduated_at` (G0).

Results within the 1,012 executable universe:

- G0 non-null: 1,010;
- G0 <= T0: 1,010;
- G0 > T0: 0;
- `T0 - G0` quantiles were all 0 seconds;
- human raw-trade coverage in the last 60s at G0 remained 12;
- human raw-trade coverage in the last 300s at G0 remained 51.

Therefore the deficiency is not repaired by swapping graduation and migration timestamps. In this public release, the raw-trade/migration linkage is insufficient for PMD-001's frozen mechanism.

## Why the gate is binding

Pump.fun documents graduation as an automatic transition from a completed bonding curve to the canonical PumpSwap pool. The intended hypothesis requires the actual final-curve microstructure immediately before that transition. Replacing missing raw observations with zeros, stale aggregate buckets, post-migration information, or a much smaller cherry-picked sample would change the question and create avoidable source bias.

The lab therefore fails closed.

## Explicitly forbidden rescues

V0.1 may not be rescued by:

- lowering the >=1,000 sample gate;
- opening the 12/51 observable cases and calling them representative;
- changing the primary hypothesis to launch-time prediction;
- using post-T0 data as predictive features;
- lowering the frozen 3.00% cost stress;
- using `postgard_outcomes.parquet` labels;
- manually selecting famous or successful tokens;
- treating missing final-window trades as zero demand;
- using stale `wallet_stats` as a substitute for raw point-in-time wallet activity.

## Authorized continuation

A new **source-rebuild version** may test the same economic mechanism using authoritative historical Solana transaction data. That is a source replication/expansion, not a rescue of V0.1 outcomes.

Until a new source independently passes the already-defined scale and leakage gates, no economic outcome may be opened.

Governance remains: research-only, fail-closed, no live trading, no exchange mutation, no main merge, no post-outcome tuning.