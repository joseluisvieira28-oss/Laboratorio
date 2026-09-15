# MSEL-001 — DATA SOURCE BENCHMARK V0.1

Date: 2026-09-15
Status: SOURCE GATE IN PROGRESS

## Purpose

Select the smallest data stack capable of reconstructing a leakage-safe all-launch universe, T+5m structural features and independent +24h outcomes.

## Candidate source verdicts

### Helius archival RPC / getTransactionsForAddress

Current documentation supports:
- mainnet historical retention: unlimited;
- time / slot filters;
- chronological or reverse pagination;
- full transaction details;
- token-account balance-change expansion;
- up to 100 full transactions per call or 1,000 signatures;
- archival history from arbitrary historical windows.

Important operational notes:
- Helius recommends `getTransactionsForAddress` for new historical indexing workflows;
- LaserStream historical replay is only ~24h and is therefore unsuitable as the historical research backfill source by itself;
- archival RPC can be paired with streaming later, but live streaming is outside this research stage;
- paid-plan / credit and rate-limit cost must be estimated before a full-universe pull.

Preliminary verdict: **BEST CURRENT CANDIDATE FOR HISTORICAL RECONSTRUCTION**, pending authentication/cost/coverage test against the Pump.fun program address and a small frozen date slice.

### RED-PUMP-2026-v1.4

Strengths:
- 860k+ launch metadata observations;
- known launch/seen timestamps and social-presence metadata;
- public and reproducible.

Fatal limitation for outcome labels:
- v1.4 corrigendum confirms the original collector only retained visibility for roughly minutes due to a top-50 newest-token buffer;
- published 0.198% graduation rate is therefore a fast-window lower bound, not a 24h graduation rate;
- TIMEOUT cannot be treated as a 24h negative label.

Verdict: **USE FOR UNIVERSE / TIMESTAMP CROSS-CHECK ONLY; QUARANTINE OUTCOMES.**

### MemeTrans / MELT

Strengths:
- rich parsed pre-migration transactions;
- bundle traces;
- feature generation code;
- risk labels / post-migration outcomes;
- 122-feature taxonomy useful for replication.

Limitations:
- research universe is based on launches that successfully migrated to DEX;
- raw transaction corpus is extremely large (>1TB in the associated public repository description);
- license is non-commercial for the MELT release unless separate permission is obtained.

Verdict: **REFERENCE / REPLICATION SOURCE, NOT PRIMARY ALL-LAUNCH UNIVERSE.**

### RED-COHORT-2026-v1.1.1

Strengths:
- 1,012 persistent early-buyer cohorts;
- 1.58M buyer events across 166k launches;
- public detection code and robustness artefacts.

Critical result:
- cohort-touched launches were associated with higher first-hour buyer flow, but activity-matched placebo wallets showed an even larger lift;
- repeated early-wallet activity is therefore likely heavily selected on launch quality / attention and is not a standalone causal edge.

Verdict: **USE FOR HEURISTIC DESIGN / NEGATIVE CONTROL; DO NOT ASSUME ‘smart-wallet’ edge.**

## Frozen source architecture for MVE

### Stage A — pilot slice only

1. Choose a historical date slice fully outside any future protected holdout.
2. Enumerate Pump.fun launch/create events directly from the Pump.fun program history.
3. For each mint, reconstruct every Pump.fun interaction through T+5m.
4. Independently reconstruct outcome state to +24h.
5. Sample 100 launches and manually reconcile against at least one independent explorer/data source.
6. Record missingness, pagination completeness, duplicate signatures and transaction errors.

No model training until this audit passes.

### Stage B — feature pilot

For the source-audited slice only, compute:
- unique buyers;
- buyer acceleration;
- repeat-buyer share;
- transaction concentration;
- early-buyer supply concentration;
- creator prior-launch count as-of launch time;
- repeated-wallet co-occurrence using prior launches only;
- buy/sell imbalance;
- curve state / progress;
- price-volume baseline controls.

### Stage C — independent outcomes

Reconstruct:
- migration/graduation;
- executable +15m/+1h/+6h/+24h return;
- -50% / -80%;
- +50% / +100%;
- MAE / MFE.

Outcome reconstruction must not reuse any future-derived input in the feature pipeline.

## Data leakage red list

Immediate FAIL if any of the following appears:
- wallet cluster built using transactions after the current decision time;
- creator ‘success rate’ using launches that had not yet resolved;
- top-holder snapshot queried from current state rather than historical T+5m state;
- token universe created from survivors/listed tokens only;
- labels sourced from a collector with hidden truncation and treated as clean negatives;
- social metrics using current followers/posts rather than archived point-in-time values;
- migration state used as an input to a pre-migration decision;
- transaction parser silently dropping failed / versioned / inner instructions that alter balance reconstruction.

## Pilot PASS criteria

Source gate passes only if:
- >=99% of sampled launch/create events reconcile by mint and timestamp;
- T+5m transaction reconstruction has documented completeness and deterministic reruns;
- +24h outcome can be reconstructed independently;
- no future-derived wallet/creator fields enter features;
- historical fee schedule and venue transition are timestamp-aware;
- the pilot produces a frozen evidence manifest with hashes/counts.

If these fail, classify as DATA_FAILURE / SOURCE_BLOCKED rather than NO_EDGE.

## Next action

Run a small authenticated Helius archival pilot against a frozen historical window. Until API access is available, keep the lab at SOURCE_GATE_IN_PROGRESS and do not fabricate outcomes from incomplete public snapshots.
