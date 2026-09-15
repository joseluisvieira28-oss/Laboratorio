# MSEL-001 — Holder Cluster Application Addendum V0.1

Status: FROZEN PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED
Date: 2026-09-15
Branch: `memecoin-structural-edge-v0.1`

## Purpose

Apply the already-frozen `FUNDER_CLUSTER_POLICY_FREEZE_V01.md` to holder balances after the one-time V0.9 funding-completeness pass, while preventing future-holder selection from leaking backward into earlier snapshots.

This addendum does not change the degree thresholds, synchronization thresholds, creator handling, or any market-outcome rule.

## Evidence authority

1. V0.9 holder funding evidence is authoritative for a holder wallet only from the first frozen holder snapshot at which that wallet is observed onward.
2. Before a wallet's first observed holder snapshot, V0.9 completion evidence must not be used merely because the wallet is known to become a holder later.
3. For the global point-in-time funder-degree calculation, start from the full V0.5 economic/creator funding universe, but accept a V0.5 primary edge only when it is uniquely reconciled to a standard Solana System Program `Transfer` (`SYSTEM_TRANSFER`). `TransferWithSeed` or unverifiable primary edges are treated as unresolved for this application.
4. Once a V0.9 holder wallet has become observable by snapshot deadline D, its V0.9 final standard-transfer status supersedes its V0.5 status for D and later snapshots.
5. A holder-only wallet absent from V0.5 enters the degree universe only once its first observed holder snapshot is at or before D.
6. Remaining V0.9 unresolved wallets remain unresolved. The 50-signature escalation is closed and cannot be increased.

## Point-in-time degree

At snapshot deadline D, `funder_degree_asof(D)` is computed over the combined evidence universe above, using only wallets whose applicable anchor is at or before D and whose applicable primary funder is resolved under trusted standard-transfer evidence.

The original frozen bands remain unchanged:
- degree 1: no merge;
- degree 2–5: eligible only under Tier A/Tier B synchronization rules;
- degree 6–9: ambiguous, no hard merge;
- degree >=10: hub/service candidate, no hard merge.

## Current-holder assignment

A wallet that is an external holder in the current frozen T+1/T+3/T+5 snapshot uses its V0.9 final funding status. The original hard-merge rules remain unchanged:
- funding lead 0..3600 seconds;
- same primary funder;
- snapshot-local degree 2..5;
- Tier A: exact same primary funding transaction; or
- Tier B: entire remaining same-funder group has funding-time span <=60 seconds and max/min funding amount <=1.05.

No subset rescue, no hub transitivity, and no missing-evidence independence assumption are allowed.

## Hidden Concentration outputs

For every frozen holder snapshot, retain both wallet-level and conservative hard-cluster-adjusted concentration:
- Top1 / Top3 / Top5 / Top10 external-holder share;
- HHI;
- Gini;
- creator-entity share;
- hard-cluster count, merged-wallet count and largest hard-cluster size;
- unresolved-funding balance share;
- degree-6–9 ambiguous balance share;
- degree-10+ hub-candidate balance share;
- small-degree-but-unmerged balance share.

Remaining unresolved/ambiguous balances are uncertainty, not proof of independence. Cluster-adjusted concentration may be used as a structural feature only together with these uncertainty fields.

## Organicity separation

This holder-completion pass does not retroactively use later holder selection to rewrite earlier V0.7 economic-flow clustering. V0.7 Organicity remains on its original pre-outcome lineage. V0.9 exists to complete holder-state Hidden Concentration.

## Governance

No price outcomes, graduation status, +15m/+1h/+6h/+24h outcomes, live trading, exchange mutation, merge to main, threshold rescue or post-outcome tuning are authorized.
