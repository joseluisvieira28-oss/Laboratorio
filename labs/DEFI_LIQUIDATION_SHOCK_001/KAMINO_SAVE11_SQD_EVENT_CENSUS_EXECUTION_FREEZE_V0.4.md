# DEFI-LIQUIDATION-SHOCK-001 — KAMINO + SAVE11 SQD EVENT CENSUS EXECUTION FREEZE V0.4

Date: 2026-09-23
Status: FROZEN PRE-CENSUS / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

This execution freeze is written before any full-range SQD candidate count is opened.

It is subordinate to:
- `BOUNDED_CENSUS_PLAN_V0.1`;
- `HISTORICAL_DECODER_AUTHORITY_MATRIX_V0.3`;
- closed RAW first-success receipts for Kamino and Save/Solend 0x11.

Execution is authorized only if `KAMINO_SAVE11_SQD_BOUNDARY_CALIBRATION_RECEIPT_V0.3.json` classifies `SQD_BOUNDARY_CALIBRATION_PASS`.

## Source

Public SQD Portal finalized Solana archive:

`https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream`

Timestamp-to-slot resolver:

`GET https://portal.sqd.dev/datasets/solana-mainnet/timestamps/{unix_timestamp}/block`

No API key, paid source or account creation is permitted.

SQD is an indexed archive/census source. Canonical RAW reconciliation remains official Solana RPC transaction data for the prospectively selected validation sample.

## Frozen populations

### Kamino
- program: `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`
- exact filter: `d8 = 0xb1479abce2854a37`
- authoritative start: `2023-11-17T14:48:24Z`
- authoritative start slot: `230572965`
- known first signature: `2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv`
- end: `2025-01-01T00:00:00Z` exclusive

### Save / Solend 0x11
- program: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`
- exact filter: `d1 = 0x11`
- authoritative start: `2024-07-19T19:30:52Z`
- authoritative start slot: `278496102`
- known first signature: `WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L`
- end: `2025-01-01T00:00:00Z` exclusive

The known first-success transaction is part of each population.

## Frozen chunk policy

Initial execution remains one UTC calendar day per chunk, preserving `BOUNDED_CENSUS_PLAN_V0.1`.

For every UTC day:
1. resolve the next UTC midnight to the first slot at or after that timestamp;
2. current day interval is inclusive start slot through `next_day_start_slot - 1`;
3. first day starts at the authoritative first-success slot rather than midnight;
4. final day ends at the slot immediately before the first slot at or after `2025-01-01T00:00:00Z`;
5. use `finalized-stream`;
6. follow SQD stream continuation until the entire slot interval is consumed;
7. preserve an explicit chunk receipt even when zero exact matches are returned;
8. no day may be skipped or reordered in the completeness manifest.

HTTP 429/5xx may be retried with bounded exponential backoff. A persistent failure marks that UTC chunk `SOURCE_CHUNK_BLOCKED` and global census cannot pass.

No chunk size may be changed based on candidate count or market outcomes.

## Frozen requested fields

Block:
- number;
- timestamp.

Transaction:
- transactionIndex;
- signatures;
- err.

Instruction:
- programId;
- data;
- transactionIndex;
- instructionAddress;
- isCommitted;
- error.

No accounts, balances, token balances, fees, prices, token amounts or market data are requested.

## Exact instruction validation

Every returned row is locally base58-decoded.

Kamino:
`decoded_data[0:8] == b1479abce2854a37`.

Save11:
`decoded_data[0:1] == 11`.

A Portal-filtered row that fails local prefix validation is `SOURCE_ANOMALY_FAIL_CLOSED`.

Outer and inner/CPI calls are both retained.
`instructionAddress` is preserved exactly as the instruction path.

## Frozen execution-state classification

For every exact match:

### Realized reference candidate

All must hold:
- parent transaction is deterministically linked by `transactionIndex`;
- transaction signature exists;
- transaction `err == null`;
- instruction `isCommitted == true`;
- instruction `error == null`.

Classification:

`SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION`

### Failed attempt

If:
- transaction `err != null`;
- instruction `isCommitted == false`;
- or instruction `error != null`;

and the failure fields are mutually consistent.

Classification:

`LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED`

### Consistency anomaly

Examples:
- transaction `err == null` but `isCommitted == false`;
- transaction `err == null` but instruction `error != null`;
- transaction `err != null` but `isCommitted == true`;
- missing parent transaction/signature;
- missing instruction path;
- timestamp outside authoritative interval.

Classification:

`SOURCE_ANOMALY_FAIL_CLOSED`

Any anomaly blocks census promotion until reconciled.

## Deduplication

Two ledgers are retained:

1. **instruction ledger**
   - unique key: `protocol + signature + instructionAddress`;
   - preserves every exact outer/CPI matching call.

2. **transaction RAW queue**
   - unique key: `protocol + signature`;
   - successful candidate transactions are deduplicated by signature only for RAW verification work, matching `BOUNDED_CENSUS_PLAN_V0.1`.

No instruction-level evidence is discarded when the transaction queue is deduplicated.

## Completeness requirements

A global census can classify `SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE` only if:
- every required UTC chunk has a terminal receipt;
- no missing/reordered day;
- every chunk fully streamed to its frozen end slot;
- no persistent transport block;
- no source anomaly;
- both known first-success signatures are recovered in their correct protocol class;
- no returned row lies outside its authoritative interval;
- successful and failed ledgers are separately preserved;
- manifest hashes all chunk receipts and ledgers.

Zero-candidate chunks are valid only when stream completeness is proven.

## Prospectively frozen RAW validation sample

For each protocol, use the deduplicated successful transaction-signature set.

Mandatory:
- known first-success signature;
- chronologically last successful signature.

Hash sample:
- compute lowercase hex `SHA256(protocol + ":" + signature)`;
- sort ascending by that hash;
- select first 30 signatures not already mandatory.

If fewer than 32 distinct successful signatures exist, verify all of them.

Thus target validation sample is at most 32 unique signatures per protocol and is fully deterministic before candidate counts are known.

RAW verification must use official Solana RPC transaction bytes/JSON and confirm:
- signature;
- slot/time;
- transaction success;
- exact program;
- exact instruction prefix;
- exact instruction path class outer/CPI.

Any mismatch is fail-closed and blocks source promotion.

## No economic outcomes

This censo is source construction only.

Forbidden:
prices; returns; PnL; future direction; liquidation USD size; collateral/debt profitability; post-event price movement; strategy thresholds; trading; orders; wallets; exchange mutation; paid sources; account creation; merge main.

No `NO_EDGE`, `EDGE`, promotion or “quase diamante” classification may be issued from this census.
