# DEFI-LIQUIDATION-SHOCK-001 — DRIFT V2 SQD FIRST-SUCCESS BOUNDARY FREEZE V0.1

Date: 2026-09-25
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose

Resolve the earliest successful on-chain boundary for the four already-frozen Drift v2 liquidation instruction classes using SQD Solana mainnet finalized archive enumeration, with Official Solana RPC RAW verification.

This supersedes the operationally inconclusive early-anchor RPC probe that timed out before producing a receipt. It does not alter scientific identity, source-code decoder boundaries, or the protected outcome firewall.

## Program and frozen source boundary

Program:
`dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`

Lower boundary inclusive:
`2022-11-04T15:17:54Z`

Upper boundary exclusive:
`2025-01-01T00:00:00Z`

## Frozen instruction classes

1. `liquidate_perp`
   - discriminator: `4b2377f7bf128b02`

2. `liquidate_spot`
   - discriminator: `6b00802923e5fb12`

3. `liquidate_borrow_for_perp_pnl`
   - discriminator: `a911205acf94d11b`

4. `liquidate_perp_pnl_for_deposit`
   - discriminator: `ed4bc6ebe9ba4b23`

The 2025 `liquidate_spot_with_swap_begin/end` pair is outside the frozen window and MUST NOT enter this population.

## Source route

Primary enumeration:
- `https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream`

Timestamp resolver:
- `https://portal.sqd.dev/datasets/solana-mainnet/timestamps/{unix_timestamp}/block`

RAW adjudication:
- Official Solana mainnet RPC `getTransaction`
- finalized commitment

## Stream query and local identity rule

For each requested UTC partition:
- filter on exact Drift program ID;
- request transactions and instructions;
- locally base58-decode every returned Drift instruction;
- match only the exact frozen 8-byte discriminator prefixes above;
- preserve outer and inner/CPI `instructionAddress`;
- no current-IDL inference beyond the already-frozen discriminator identities.

Server-side discriminator filtering MAY be added only as an exact-equivalent transport optimization after a source-only calibration proves no loss versus programId-only enumeration. V0.1 uses programId-only enumeration to avoid undocumented OR-semantics assumptions.

## Time/slot rule

SQD timestamp resolver is transport seeding only.

For each partition:
1. resolve lower timestamp to a slot seed;
2. resolve upper timestamp to a slot seed;
3. query through upper seed +16 slots;
4. determine scientific membership locally with exact UTC timestamps;
5. enforce `lower <= timestamp < upper`;
6. never admit an event before `2022-11-04T15:17:54Z` or at/after `2025-01-01T00:00:00Z`.

## Completion semantics

- HTTP 204 => documented stream termination.
- HTTP 200 + empty NDJSON => documented filtered-stream termination.
- HTTP 200 + rows => process and advance to `last block + 1`.
- non-advancing stream, malformed payload, missing parent transaction, bad timestamp, duplicate-key collision, or inconsistent execution semantics => fail closed.
- 429 / retryable 5xx may receive bounded transport retries.

## Event semantics

Instruction identity key:
`class + signature + instructionAddress`

Successful provisional candidate:
`SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION`

Requires:
- exact Drift program;
- exact frozen discriminator;
- signature present;
- transaction `err == null`;
- instruction `isCommitted == true`;
- instruction error null.

Failed exact matches:
`LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED`

Anomaly:
`SOURCE_ANOMALY_FAIL_CLOSED`

## First-success proof

Each of the four classes is resolved independently.

For a class:
1. inspect partitions in strict chronological order from the frozen lower boundary;
2. all earlier partitions through the candidate partition must be complete, gap-free and anomaly-free;
3. the earliest successful exact match is the provisional class boundary;
4. Official Solana RPC RAW reconciliation is mandatory;
5. RAW must confirm exact signature, slot, blockTime, meta.err null, exact program, exact discriminator and outer/inner path class.

Only then classify:
- `DRIFT_LIQUIDATE_PERP_FIRST_SUCCESS_BOUNDARY_SQD_PASS`
- `DRIFT_LIQUIDATE_SPOT_FIRST_SUCCESS_BOUNDARY_SQD_PASS`
- `DRIFT_LIQUIDATE_BORROW_FOR_PERP_PNL_FIRST_SUCCESS_BOUNDARY_SQD_PASS`
- `DRIFT_LIQUIDATE_PERP_PNL_FOR_DEPOSIT_FIRST_SUCCESS_BOUNDARY_SQD_PASS`

Combined:
`DRIFT_FOUR_CLASS_FIRST_SUCCESS_SOURCE_PASS`

If a class has no successful exact match after complete enumeration through the frozen upper bound:
`DRIFT_<CLASS>_NO_MATCH_IN_COMPLETE_SQD_WINDOW`

This is a source/event-population finding, not NO_EDGE.

## Partition policy

Initial probe:
- `[2022-11-04T15:17:54Z, 2022-12-01T00:00:00Z)`

If any class remains unresolved after that clean partition, continue using prospectively declared monthly partitions in strict chronological scientific order.

Operational parallelism is allowed, but earliest-boundary adjudication is always chronological and cannot skip an earlier missing/blocked partition.

## Firewall

prices=false
balances=false
token_amounts=false
returns=false
pnl=false
direction=false
economic_outcomes=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false

A source, transport, or coverage blocker is never NO_EDGE.
