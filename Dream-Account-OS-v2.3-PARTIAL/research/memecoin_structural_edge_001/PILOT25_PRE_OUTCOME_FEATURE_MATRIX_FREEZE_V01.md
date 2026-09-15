# MSEL-001 — PILOT25 PRE-OUTCOME FEATURE MATRIX FREEZE V0.1

Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED
Branch: `memecoin-structural-edge-v0.1`
Date: 2026-09-15

## 1. Purpose

Freeze the exact T+5m feature matrix and a single primary pilot risk score BEFORE any future token outcomes are opened for the blind 25-launch cohort.

This is a forensic pilot, not the full Killer Filter MVE. A 25-token cohort spanning ~87 seconds cannot satisfy the already-frozen temporal-OOS survival gate, the >=3 chronological-block stability requirement, or certify a trading edge. The pilot may only answer whether the structural mechanism is directionally worth scaling after source/semantic integrity is established.

## 2. Source authorities

The builder must bind fail-closed to:

- cohort SHA-256: `7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9`
- V07 cluster manifest SHA-256: `7516861dd86a2b302e4a1360acbaa68f3360b4ddd802352db93f2eccc3012090`
- V10A holder-cluster manifest SHA-256: `149d55f5abb8b781236070fd4d3ba01dd5a3a5b7a2bf054f6b22dd178a36cb95`

All bound manifests must state `outcomes_opened == false`. Their referenced JSONL hashes must reconcile exactly.

## 3. Decision timestamp

Only the `snapshot_horizon_seconds == 300` row is eligible for the pilot feature matrix.

No T+5m feature may use a funding edge, holder state, trade, creator state, metadata observation, price or other information first known after its frozen snapshot deadline.

## 4. Frozen core mechanism features

### 4.1 Hidden concentration family

Use the conservative holder-state output from V10A:

- `entity_top1_share_5m`
- `entity_top3_share_5m`
- `entity_top5_share_5m`
- `entity_top10_share_5m`
- `entity_hhi_5m`
- `entity_gini_5m`
- `creator_entity_share_5m`

Raw wallet-level concentration is retained separately:

- `raw_top1_holder_share_5m`
- `raw_top3_holder_share_5m`
- `raw_top5_holder_share_5m`
- `raw_top10_holder_share_5m`
- `raw_holder_hhi_5m`
- `raw_holder_gini_5m`

Because V10A produced zero approved hard merges at T+5m, raw and entity concentration may be numerically identical in this pilot. This is NOT evidence that hidden linkage is absent. It is only the result under the frozen conservative hard-merge policy.

### 4.2 Organicity / independent-flow family

Use the V07 cluster-adjusted candidate fields:

- `organicity_candidate_5m = external_positive_net_inflow_raw / external_gross_sol_raw`
- `signed_net_to_gross_5m`
- `external_buy_cluster_top1_share_5m`
- `external_buy_cluster_top3_share_5m`
- `external_buy_cluster_hhi_5m`
- `external_gross_sol_raw_5m`
- `economic_wallet_count_5m`
- `external_cluster_count_5m`

The term `organicity_candidate` is retained intentionally. Funding uncertainty and service-hub ambiguity remain non-zero, so this pilot must not rename the quantity to a fully proven independent-flow ratio.

## 5. Frozen uncertainty features

Uncertainty is a feature, never silently converted into independence.

Holder-state uncertainty from V10A:

- `holder_unresolved_funding_share_5m`
- `holder_hub10plus_share_5m`
- `holder_ambiguous_degree6to9_share_5m`
- `holder_small_degree_unmerged_share_5m`

Trade-flow uncertainty from V07:

- `flow_unresolved_funding_share_5m`
- `flow_hub10plus_share_5m`
- `flow_ambiguous_degree6to9_share_5m`
- `flow_small_degree_unmerged_share_5m`

No additional funding lookback, new hub classifier, relaxed cluster threshold, or post-outcome rescue is authorized for this cohort.

## 6. Primary pilot score — frozen before outcomes

The single primary directional pilot score is intentionally simple and tied only to the two highest-priority mechanisms frozen before outcomes:

1. high holder/entity concentration is riskier;
2. low Organicity candidate is riskier.

For the 25 blind tokens:

- `concentration_rank_risk` = deterministic fractional rank of `entity_top1_share_5m`, ascending from safest to riskiest, scaled to [0,1];
- `organicity_rank_risk` = deterministic fractional rank of `organicity_candidate_5m`, DESCENDING in safety, so lower Organicity receives higher risk, scaled to [0,1];
- `primary_pilot_risk_score = 0.50 * concentration_rank_risk + 0.50 * organicity_rank_risk`.

Tie-breaking for rank order is fixed as `(feature value, cohort_rank, mint)` in the relevant direction. Missing primary inputs are fail-closed: the matrix build must stop rather than impute.

No weights, features or sign directions may change after outcome opening.

## 7. Frozen pilot slices

For N=25:

- safest 20% = 5 lowest primary scores;
- safest 50% = 13 lowest primary scores (ceiling convention);
- riskiest 20% = 5 highest primary scores.

Ties at a slice boundary are resolved by `(primary_pilot_risk_score, cohort_rank, mint)` in ascending order. The riskiest slice is the final 5 rows of that same deterministic order.

These slices are pilot diagnostics only and cannot by themselves satisfy `SURVIVES_MVE`.

## 8. Secondary diagnostics — no feature rescue

All other frozen matrix columns may be reported descriptively or as pre-specified secondary diagnostics, but no secondary feature can replace the primary score after outcomes are visible.

Creator-history, metadata/copycat, price-return control and full chronological-OOS model families from `FEATURE_DICTIONARY_V01.md` remain outside this pilot matrix unless separately reconstructed and frozen BEFORE outcome opening. Their absence prevents the 25-token pilot from being treated as the final MVE.

## 9. Interpretation of current V10A structural result

Pre-outcome facts now known:

- 0/25 T+5 snapshots contain an approved hard holder merge;
- median unresolved holder balance share is ~35.4%; maximum ~58.2%;
- median degree-10+ hub-candidate balance share is ~35.1%; maximum ~98.5%;
- median raw top-1 holder share is ~30.1%;
- median conservative entity top-1 share is also ~30.1%.

Therefore holder/entity concentration is a conservative estimate with material ambiguity, not a fully resolved economic-ownership truth.

## 10. Outcome lock

Building and hashing the matrix does NOT authorize opening future prices or labels.

The exact outcome/execution schema — including price authority, migration handling, catastrophic label mechanics, future windows and missing-data policy — must be frozen separately before any outcome collector runs.

No live trading. No exchange mutation. No main merge. No post-outcome tuning.
