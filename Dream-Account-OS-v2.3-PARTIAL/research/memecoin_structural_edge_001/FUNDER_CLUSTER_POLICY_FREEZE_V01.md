# MSEL-001 — Funder / Economic-Entity Cluster Policy Freeze V0.1

Status: FROZEN PRE-OUTCOME
Branch: `memecoin-structural-edge-v0.1`
Scope: MSEL-001 forensic pilot and later preregistered replication unless superseded BEFORE outcomes by an explicitly versioned protocol change.

## Purpose

Convert V0.5 direct native-SOL funding evidence into a conservative point-in-time economic-entity clustering rule without turning shared exchange/service funding into fake common-control evidence.

This freeze is created before any future token outcome is opened.

## Hard principles

1. Shared funder alone is NOT sufficient to merge wallets.
2. Missing funding evidence is NOT evidence of independence.
3. High-degree funders are treated as hub/service ambiguity, not as common-control clusters.
4. Clustering must be recomputed point-in-time for every token snapshot. No information whose wallet anchor occurs after that snapshot may affect that snapshot.
5. Cross-launch co-participation observed after a snapshot is forbidden as a clustering input for that snapshot.
6. Origin creator is not automatically merged with any wallet. It is merged only under the same frozen evidence rule. If a hard cluster contains the origin creator, the whole cluster is creator-linked for external-organicity calculations.
7. No transitive chaining across different primary funders.
8. Outcomes, future prices, graduation, later DEX state and later wallet behavior are forbidden inputs.

## Point-in-time funder degree

For a snapshot deadline D, `funder_degree_asof(D)` is the number of target-cohort wallets whose frozen V0.5 anchor is <= D and whose V0.5 primary direct native-SOL funder equals that funder.

Degrees computed from wallets anchored after D are future information and MUST NOT be used.

## Degree policy

- degree = 1: singleton; no merge.
- degree 2–5: eligible for conservative hard merge only if the synchronization rule below also passes.
- degree 6–9: ambiguous shared-service/shared-actor zone; NO hard merge.
- degree >=10: high-degree hub/service candidate; NO hard merge.

The 2–5 threshold is intentionally conservative and is frozen before outcomes.

## Funding evidence eligibility

A wallet can participate in a hard merge only if all are true:

- V0.5 status is `DIRECT_FUNDING_EVIDENCE_FOUND`;
- primary funding timestamp exists;
- anchor timestamp exists;
- funding occurs no later than anchor;
- funding lead = anchor_time - funding_time is between 0 and 3600 seconds inclusive;
- primary funder is identical across merged members;
- snapshot-local funder degree is 2–5 inclusive.

## Synchronization rule

Hard merge is allowed by either Tier A or Tier B.

### Tier A — same funding transaction

Two or more eligible wallets funded by the same primary funder in the exact same primary funding transaction signature are hard-merged.

### Tier B — tightly synchronized funding

For eligible wallets of the same small-degree funder that were not already merged under Tier A, the entire remaining same-funder group is hard-merged only when:

- group size >=2;
- max funding timestamp - min funding timestamp <=60 seconds; and
- max funding amount / min funding amount <=1.05.

If any condition fails, those wallets remain separate. No subset rescue or post-outcome tuning is allowed.

## Snapshot-local application

A hard cluster for a token snapshot may contain only wallets that have economic activity in that token by the snapshot deadline. Funding evidence may come from before each wallet's anchor, but a wallet that has not yet appeared by the snapshot cannot influence that snapshot.

## Creator-linked handling

If the origin creator is a member of a hard cluster, the complete cluster is tagged `creator_linked = true`.

Creator-linked clusters are excluded from the numerator and denominator of the external Organicity candidate metric.

## Cluster-adjusted Organicity candidate

For each external non-creator-linked economic cluster e:

- `buy_e` = delivered, non-atomic economic BUY SOL notional through snapshot;
- `sell_e` = delivered, non-atomic economic SELL SOL notional through snapshot;
- `gross_e = buy_e + sell_e`;
- `net_e = buy_e - sell_e`.

Define:

`external_positive_net_inflow = sum(max(net_e, 0))`

`external_gross_turnover = sum(gross_e)`

`cluster_adjusted_organicity_candidate = external_positive_net_inflow / external_gross_turnover`

Also retain signed diagnostic:

`cluster_adjusted_signed_net_to_gross = sum(net_e) / external_gross_turnover`

These are structural features, NOT trading returns and NOT proof of edge.

## Mandatory uncertainty features

Every snapshot must retain at least:

- unresolved-funding gross share;
- high-degree hub-candidate gross share;
- degree-6–9 ambiguous-funder gross share;
- small-degree but non-merged gross share;
- hard-merged wallet count;
- hard-cluster count;
- largest hard-cluster size.

The Organicity candidate must not be described as fully identified if material unresolved/ambiguous share remains.

## No-outcome gate

Applying this policy does not authorize opening outcomes. After V0.7, holder-state Hidden Concentration must be reconciled with the same snapshot-local cluster map, then the complete feature matrix must be hashed/frozen before future outcomes are opened.
