# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.4.1 QUEUE-SUBSPACE AMENDMENT

Date: 2026-10-07
Parent freeze: 71ac365e709b0e0d7074caed7e842f513207aa85
Outcomes opened: NO

## New source capability

Before opening any unbonding queue contents, V0.4.1 freezes a second index-free census route based on historical Cosmos SDK store-prefix queries.

For a chain/height whose production staking store layout is version-pinned and confirms the classic unbonding queue key:

- store: staking
- queue prefix: 0x41
- ABCI path: /store/staking/subspace
- data: raw byte prefix 0x41
- explicit historical height H
- prove: false for census extraction; canonical block hash/time retained separately

The Cosmos SDK store subspace query iterates all key/value pairs whose key begins with the requested prefix.

## Scientific use

A queue snapshot is eligible only when:
1. the chain production version/fork at H is pinned;
2. that version confirms UnbondingQueueKey = 0x41 or an explicitly equivalent key;
3. archive application state at H is available;
4. the response is bounded to H and persisted with digest;
5. queue value encoding is decoded using the version-pinned SDK type;
6. an independent source returns the same canonical state content or equivalent reconstructible evidence.

## Census rule

If the queue route is viable, the full raw-block scan is no longer required as primary discovery.

Instead:
- determine deterministic historical checkpoint heights before inspecting queue counts;
- checkpoint cadence must be strictly shorter than the minimum native unbonding period applicable to that chain/era;
- enumerate the full 0x41 queue at every checkpoint;
- de-duplicate queue entries/cohorts deterministically;
- resolve each candidate to its initiation and actual completion using canonical raw blocks/block_results;
- preserve cancellation, slash and hold handling from V0.4.

A checkpoint route can claim complete discovery only if it is proven that any cohort that ultimately completes must remain represented in the queue for longer than the frozen checkpoint interval. Otherwise the chain fails census completeness.

## Checkpoint cadence

Primary cadence is frozen at 24 hours UTC.

If a version-pinned native unbonding period is <=24 hours at any point in the frozen interval, that chain is ineligible for this route unless a shorter cadence is frozen in a separate amendment before queue counts are inspected.

## Materiality and hard gates

Unchanged:
- 10 bps of historical bonded stake;
- >=40 MATERIAL chain-days TOTAL;
- >=5 qualifying chains;
- no market outcomes in source remediation.

Queue counts observed after this amendment may not be used to change cadence, materiality or chain-selection order.
