# DEFI-LIQUIDATION-SHOCK-001 — SOURCE SAMPLE GATE FREEZE V0.1

Date: 2026-09-27
Status: FROZEN / SOURCE-COUNT ONLY / OUTCOME-BLIND

## Purpose

Freeze numerical adequacy requirements after the raw source population became known but before market outcomes.

Raw realized-event count alone is not the inferential sample size.
The primary independent unit is the 60-second completed cascade from CASCADE_CLUSTERING_FREEZE_V0.1.

## Primary aggregate gate

To authorize inferential Discovery:
- Discovery primary clusters >= 1,000

To authorize inferential OOS:
- OOS primary clusters >= 500

If either fails:
`SAMPLE_GATE_BLOCKED_FOR_PRIMARY_INFERENCE`

No threshold may be lowered after market outcomes.

## Protocol/class subgroup gate

A protocol/class subgroup may receive its own inferential Discovery result only if:
- Discovery clusters >= 200

It may receive its own inferential OOS result only if:
- OOS clusters >= 100

Below threshold:
`DESCRIPTIVE_ONLY_INSUFFICIENT_INDEPENDENT_N`

It remains in aggregate analysis and is not removed from the source population.

## Late-launch external-confirmatory families

A family with no Discovery period under PRE_DISCOVERY_TEMPORAL_HOLDOUT_FREEZE_V0.1 may be labeled:
`EXTERNAL_CONFIRMATORY_ONLY`

Required OOS cluster count for an inferential family-level result:
- >= 200

Below 200:
descriptive only.

## Asset-level strata

No asset-level stratum is promoted inferentially unless:
- Discovery clusters >= 200
- OOS clusters >= 100

Asset strata below these gates remain descriptive and cannot be cherry-picked after outcomes.

## Sensitivity clustering

15-second and 300-second cluster definitions do not replace the primary 60-second sample gate.

They are sensitivity analyses and must satisfy the same numerical thresholds if inferential claims are made.

## Source-only calculation

Cluster counts are computed only from frozen on-chain source events and source market identities.

No price, return, volatility, PnL or market outcome may enter the sample-gate calculation.

## Current raw-event reference

Already terminal source authorities establish millions of realized instructions across the frozen families, but this document deliberately does not infer cluster counts from raw-event counts.

Cluster counts must be materially computed after GLOBAL_FIELD_COVERAGE_FINAL_PASS.

## No post-outcome rescue

If cluster counts fail a threshold:
- do not widen dates into protected 2025/2026;
- do not merge protocols/assets solely to pass N;
- do not reduce the threshold after outcomes.

## Firewall

prices=false
returns=false
pnl=false
economic_outcomes=false
protected_2025_2026_market_outcomes=false
post_outcome_tuning=false
live_trading=false
merge_main=false
