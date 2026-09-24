# DEFI-LIQUIDATION-SHOCK-001 — MARGINFI + SAVE0C SQD FIRST-SUCCESS BOUNDARY FREEZE V0.1

Date: 2026-09-24
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose

Resolve the historical first-success boundary for the already-frozen Marginfi and Save/Solend 0x0c liquidation instruction identities using SQD Solana mainnet finalized archive enumeration instead of brute-force `getSignaturesForAddress` pagination.

The prior official-public-RPC route is preserved as valid evidence but terminally classified `RPC_HISTORY_BLOCKED` after the frozen 5,000-page cap. That is a source-route blocker, not NO_EDGE.

## Source authority

Primary enumeration source:
- SQD Portal dataset: `solana-mainnet`
- endpoint: `https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream`
- timestamp resolver: `https://portal.sqd.dev/datasets/solana-mainnet/timestamps/{unix_timestamp}/block`

RAW adjudication authority:
- official public Solana RPC
- endpoint: `https://api.mainnet-beta.solana.com`
- method: `getTransaction`
- commitment: finalized

## Frozen scientific identities

### Marginfi
- program: `MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`
- instruction class: `lending_account_liquidate`
- discriminator: `d6a997d5fba756db`
- lower boundary inclusive: `2023-02-07T15:47:04Z`
- upper boundary exclusive: `2025-01-01T00:00:00Z`
- SQD filter: programId + d8 server-side discriminator filter
- preserve outer and inner/CPI instructionAddress paths returned by SQD

### Save/Solend 0x0c
- program: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`
- instruction class: `LiquidateObligation`
- native tag: `0x0c`
- lower boundary inclusive: `2021-12-08T00:00:00Z`
- upper boundary exclusive: `2025-01-01T00:00:00Z`
- SQD filter: programId only
- local base58 decode of every returned program instruction; accept only data beginning byte `0c`
- preserve outer and inner/CPI instructionAddress paths

## Frozen time/slot boundary rule

SQD timestamp resolver is a transport seed only, not scientific membership authority.

For each calendar partition:
1. obtain a lower slot seed from the exact UTC partition start;
2. obtain an upper slot seed from the exact UTC partition end;
3. query through upper seed +16 slots;
4. determine scientific membership locally from exact block timestamp:
   `partition_start <= timestamp < partition_end`;
5. the first partition also enforces the exact frozen lower boundary timestamp;
6. no event at or after `2025-01-01T00:00:00Z` is admissible.

The +16 slot envelope is transport-only and does not alter population.

## Partition rule

- logical partition = one UTC calendar month
- first and last partial months are clipped by frozen scientific timestamps
- all partitions are declared prospectively in the workflow
- no omission, reordering, cherry-picking, or post-result partition changes

Parallel execution is operational only. Scientific chronology is reconstructed by the aggregator.

## SQD stream-completion rule

Following documented SQD continuation semantics:
- HTTP 204 => documented stream termination
- HTTP 200 + zero NDJSON lines => documented filtered-stream termination
- HTTP 200 + rows => process rows and advance from `last block number + 1`
- non-advancing response => fail closed
- 429 / retryable 5xx => bounded transport retries
- malformed JSON, missing parent transaction, bad timestamp, decode/provenance inconsistency => fail closed

A zero-match partition is valid only after documented stream termination and exact local timestamp filtering.

## Candidate semantics

Instruction identity key:
`protocol + signature + instructionAddress`

A row is a successful first-success candidate only when:
- exact frozen program ID matches
- exact frozen discriminator/tag matches
- transaction signature is present
- transaction `err == null`
- instruction `isCommitted == true`
- instruction error is null

Failed attempts are preserved separately as:
`LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED`

Inconsistency is:
`SOURCE_ANOMALY_FAIL_CLOSED`

Successful pre-RAW classification:
`SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION`

## Earliest-boundary proof

For each protocol:
1. aggregate all completed monthly partitions;
2. sort successful exact instruction candidates by timestamp, slot, signature, instructionAddress;
3. identify the chronologically earliest successful candidate;
4. require every monthly partition from the frozen lower boundary through the candidate timestamp to be complete, hash-valid, anomaly-free and gap-free;
5. later partitions are not required to prove the first-success boundary, but if they ran they remain preserved as non-authoritative surplus evidence;
6. if all partitions through the upper boundary complete with no successful exact match, classification is `NO_MATCH_IN_COMPLETE_SQD_WINDOW`, not NO_EDGE;
7. any missing/incomplete required earlier partition => `SQD_FIRST_SUCCESS_BOUNDARY_BLOCKED`.

## Mandatory RAW reconciliation

The earliest SQD successful candidate for each protocol must be verified with official Solana RPC `getTransaction`:
- exact signature
- exact slot
- exact blockTime
- `meta.err == null`
- exact program ID
- exact discriminator/tag
- path class outer/inner consistent with SQD evidence

RAW match => protocol boundary PASS.
RAW mismatch/null/unavailable after bounded retries => fail closed.

## Valid terminal classifications

Per protocol:
- `MARGINFI_FIRST_SUCCESS_BOUNDARY_SQD_PASS`
- `SAVE0C_FIRST_SUCCESS_BOUNDARY_SQD_PASS`
- `MARGINFI_FIRST_SUCCESS_BOUNDARY_NO_MATCH_IN_COMPLETE_SQD_WINDOW`
- `SAVE0C_FIRST_SUCCESS_BOUNDARY_NO_MATCH_IN_COMPLETE_SQD_WINDOW`
- `SQD_FIRST_SUCCESS_BOUNDARY_BLOCKED`
- `SOURCE_ANOMALY_FAIL_CLOSED`

Combined:
- `MARGINFI_SAVE0C_SQD_FIRST_SUCCESS_SOURCE_PASS` only if both protocol boundary PASS states are RAW-reconciled
- otherwise fail closed with exact per-protocol source state

## Fallback hierarchy

If SQD cannot provide defensible historical coverage for a frozen lower boundary, do not alter the scientific window. Open a separate prospective Source Gate for a public/free historical archive (first candidate: solarchive.org Parquet transaction archive) and retain official Solana RPC only for RAW verification.

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

A SOURCE/DATA/TRANSPORT blocker is never NO_EDGE.
