# PMD-001 — TIMESTAMP PRECISION CUTOFF AMENDMENT V0.1

Date: 2026-09-16
Status: **RESEARCH-ONLY / FAIL-CLOSED / PRE-OUTCOME / LEAKAGE FIX FROZEN**
Branch: `pumpfun-migration-direction-v0.1`

## Problem discovered pre-outcome

The frozen corpus migration timestamp `T0` is represented at microsecond precision, while standard Solana `blockTime` in signature/block RPC evidence is second-resolution Unix time.

Therefore a naïve comparison `blockTime < T0` can classify every transaction in the integer second containing T0 as pre-migration, even though some transactions in that second may occur after the actual migration boundary.

No economic outcome has been opened. This is a leakage-resolution issue discovered during source reconstruction.

## Frozen conservative rule

For PMD-001 V0.1, transaction evidence is predictive-feature eligible only when:

`blockTime < floor(T0_unix_seconds)`

In words: **the entire integer second containing T0 is quarantined from predictive features**.

This deliberately sacrifices at most approximately one second of genuinely pre-migration activity in exchange for a proof that no same-second post-migration transaction can leak into the feature set solely because of timestamp precision mismatch.

The lower source-reconstruction boundary remains the already-frozen `T0-300s`. A transaction must satisfy both:

- `blockTime >= T0-300s`; and
- `blockTime < floor(T0)`.

## Same-second evidence

Transactions whose `blockTime == floor(T0)` may be retained in raw forensic evidence for migration-boundary diagnostics, but must carry `feature_eligible=false` and may not enter any predictive feature, score, source-ceiling success count or partition eligibility count.

## Why not infer within-second order now

The public `migrations.parquet` source does not expose an authoritative migration transaction signature or transaction index. PMD-001 will not infer a within-second migration boundary from token popularity, post-migration pool activity, or other outcome-adjacent evidence.

A future independently frozen source method may identify the exact on-chain `migrate` instruction and transaction index, but V0.1 does not need that precision to remain causal. The conservative whole-second quarantine is binding for this experiment.

## Required reruns

Any source-access audit or source-ceiling audit executed before this amendment may be retained as an operational diagnostic, but it is **not authoritative for final feature eligibility** until rerun under this cutoff.

The final `n>=1000` Source Gate must use this amended safe cutoff.

## Unchanged rules

No change to:
- economic thesis;
- 300-second source window family;
- T0 population condition;
- post-migration entry/exit rules;
- 3.00 percentage-point round-trip stress;
- 60/20/20 chronological split;
- minimum sample thresholds;
- promotion gates;
- outcome lock;
- research-only / no-live-trading governance.

Outcomes remain locked.
