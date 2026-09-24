# DEFI-LIQUIDATION-SHOCK-001 — MARGINFI + SAVE0C EVENT CENSUS RAW SAMPLE PLAN V0.1

Date: 2026-09-24
Status: FROZEN PRE-CENSUS-OUTCOME / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose
Freeze the deterministic Official Solana RPC RAW reconciliation sample before the Marginfi+Save0c event census results are known. This document does not inspect or depend on prices, amounts, returns, PnL, direction, economic outcomes, or protected 2025/2026 market outcomes.

## Eligible population
Only rows from the complete, gap-free, hash-valid, anomaly-free source census whose classification is SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION and whose exact frozen protocol identity matches.

Failed attempts are never promoted into the successful population and remain separately preserved.

## Deterministic sample
For each protocol independently, after a complete census is assembled:
1. sort successful unique instruction identities by timestamp, slot, signature, instructionAddress;
2. mandatory chronological first successful identity;
3. mandatory chronological last successful identity;
4. from all remaining unique successful identities, compute SHA256(protocol + ":" + signature + ":" + compact_json(instructionAddress));
5. sort ascending by that digest and select the first 30 identities;
6. deduplicate the union by protocol+signature+instructionAddress;
7. if fewer than 32 unique successful identities exist, reconcile all.

The first-success identity must equal the already-adjudicated boundary authority for that protocol. Any mismatch fails closed.

## RAW authority and checks
Authority: official public Solana RPC getTransaction, commitment finalized, bounded retry for 429/retryable 5xx only.

Every sampled identity must verify:
- exact signature;
- exact slot;
- exact blockTime;
- meta.err == null;
- exact frozen program ID;
- exact discriminator/tag;
- expected outer/inner path class is observed.

A null/unavailable transaction after bounded retries, mismatch, provenance inconsistency, or path-class mismatch fails closed.

## Terminal semantics
This plan alone grants no census PASS and no economic inference.

Census source authority may be issued only after:
- all 60 logical partitions are accounted for exactly once, including reuse of the 2 authoritative first partitions from run 36012206541;
- exact contiguous UTC coverage, no gap/overlap;
- stream_complete=true and SOURCE_PARTITION_PASS for every partition;
- anomaly_count=0 everywhere;
- rows_sha256 integrity verified;
- global dedup collision check passes;
- this frozen RAW sample reconciles successfully.

Source/data/transport blocker is never NO_EDGE.

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
