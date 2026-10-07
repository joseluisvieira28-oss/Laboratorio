# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.4 INDEX-FREE CENSUS FREEZE

Date: 2026-10-07
Parent V0.3 closeout: 6cca7f9c26d10592950b51beec9f78bde12082cf
Outcomes opened before V0.4: NO
Main baseline: f263c6c6f3a57f26666a7aee28e782f2cbd08418

## Purpose

V0.4 tests whether the V0.3 source blocker can be removed without any historical transaction index. Canonical raw blocks plus block results are the census authority. Indexes may only accelerate discovery and never establish completeness.

## Frozen interval and firewall

Completion interval: 2023-01-01 through 2024-12-31 UTC.
Earlier blocks may be read only to reconcile a completion inside that interval.

No market prices, returns, PnL or outcome-informed search. No change to main. No sample, materiality, chain or source rule may be altered after counts are observed.

## Lifecycle authority

Qualifying cohorts must be native Cosmos SDK x/staking voluntary undelegations or a version-pinned equivalent.

Ledger must resolve:
- successful MsgUndelegate initiation;
- committed completion_time from the successful execution event;
- MsgCancelUnbondingDelegation including partial cancellation;
- slash and hold effects;
- actual canonical complete_unbonding release;
- final native amount and canonical completion time.

Expected maturity is not T_completion.

## Index-free raw census

For each selected chain:
1. binary-search first/last canonical heights for the frozen interval;
2. partition the full inclusive range into deterministic non-overlapping shards before event counts are inspected;
3. fetch every /block?height=H in every shard;
4. decode TxRaw -> TxBody -> Any;
5. retain MsgUndelegate and MsgCancelUnbondingDelegation;
6. for target txs, fetch /block_results?height=H and retain only successful tx execution plus staking unbond event fields;
7. record coverage, failures and output hashes per shard;
8. census completeness requires every frozen height covered with no unresolved gaps.

Smoke windows never establish census completeness.

## Completion lookup

Use the committed completion_time only to bound the later search. Map it to canonical height by timestamp binary search, inspect block_results around maturity, and reconcile the same cohort through cancellation/slash/hold to actual complete_unbonding. Never join initiation and completion by tx index.

## Version-pinned state route

Cosmos SDK versions using the classic staking store define UnbondingQueueKey = 0x41. Historical queue/state evidence is secondary unless the chain's production version, store layout, historical state availability and iteration completeness are all proven. Current state cannot substitute for historical state.

## Materiality inherited unchanged

For UTC chain-day d:
R_d = qualifying native principal actually released by completion.
B_d = historical bonded native stake immediately before d.
M_d = R_d / B_d.

MATERIAL iff M_d >= 0.001 (10 bps / 0.10%).

Hard bar: >=40 MATERIAL chain-days TOTAL across >=5 qualifying chains.

## Prospectively frozen chain order

Already two-source qualified at fixed historical heights:
1. ATOM
2. OSMO
3. TIA
4. DYDX

Fifth-chain qualification order, fixed before V0.4 counts:
5a. KAVA
5b. INJ
5c. SEI

Use the first candidate in that order that proves comparable native staking plus two independent public/free historical paths. Do not skip an earlier qualifying chain because of event counts.

## Hard gates

G1 >=5 comparable version-pinned chains.
G2 two independent historical paths per selected chain.
G3 complete raw-block census of 2023-2024 per selected chain, or an independently verifiable complete equivalent.
G4 cancellation/slash/hold lifecycle reconciled.
G5 >=40 MATERIAL chain-days TOTAL across >=5 chains.
G6 >=12 consecutive months pre-2026 market-source capability metadata only, before outcomes.
G7 reproducible receipts and no prohibited access.

Allowed verdicts: SOURCE_GATE_PASS, SOURCE_HISTORICAL_COVERAGE_BLOCKED, SOURCE_CENSUS_INCOMPLETE, INSUFFICIENT_INDEPENDENT_SAMPLE, MECHANISM_NOT_COMPARABLE, SOURCE_PROVENANCE_INCOMPLETE, TECHNICAL_FAILURE.

No NO_EDGE verdict is possible in V0.4.
