# LCOD-001 PROVENANCE ADJUDICATION ADDENDUM V0.1

Frozen: 2026-09-26
Lab: LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001
Scope: provenance resolution only.

## Problem

FORWARD_OBSERVATION_001 was produced by run 36150913137 while the research branch advanced during the run.

The persisted snapshot itself records:
- caller_git_sha = 9c01873c3f0044c0f628871a13a803bccfdc8cd5
- scientific_code_sha = null

Job logs show:
- prepare used 9c01873c3f0044c0f628871a13a803bccfdc8cd5;
- 8 classify_population shards used 9c01873c3f0044c0f628871a13a803bccfdc8cd5;
- 8 classify_population shards used c45b46b6e3eca3bb9a56d89caccc8cb70a43d276;
- aggregate_population used 502e6fe94422c2ae40cd314b5a8c854552df2037;
- reconstruct_and_curve used 502e6fe94422c2ae40cd314b5a8c854552df2037.

## Scientific-core identity test

The following scientific-core files have identical Git blob SHAs at all three observed checkout SHAs:

- lcod_active_population_prepare_v08.mjs
- lcod_active_population_chunk_v08.mjs
- lcod_active_population_aggregate_v08.mjs
- lcod_full_same_block_component_reconstruction_v01.mjs
- canonical_stress_curve.py
- lcod_open_canonical_curve_v01.py

Combined scientific-core fingerprint:
2c2f14706348e61727a68ebb5eea4fc9db5900e74fff339594cf7098005dd650

The branch changes between the observed SHAs were limited to:
- forward-series indexing;
- workflow orchestration/provenance plumbing;
- finalizer provenance metadata;
- technical failure runbook.

No scientific-core calculation file changed.

## Resolution

FORWARD_OBSERVATION_001 remains immutable and remains canonical.

Its missing in-snapshot scientific_code_sha is resolved by:
LCOD_FORWARD_PROVENANCE_ADJUDICATION_001.json

A future predictor-only viability review may treat this single missing field as resolved ONLY when all of the following hold:
1. snapshot SHA exactly matches the adjudication target;
2. Ethereum block number exactly matches;
3. adjudication classification is PROVENANCE_EQUIVALENCE_PASS;
4. scientific_core_changed_between_observed_shas is false;
5. outcome_data_opened, market_returns_opened, liquidation_outcomes_opened and pnl_opened are all false;
6. snapshot_mutated is false;
7. scientific_core_fingerprint_sha256 is present.

Any missing or mismatched condition remains fail-closed.

## Boundary

This addendum does not:
- alter the original snapshot;
- alter any curve point;
- alter population membership;
- open outcomes;
- grant promotion credit;
- authorize trading;
- relax the 30-observation / 21-day gate.

This is provenance repair only.
