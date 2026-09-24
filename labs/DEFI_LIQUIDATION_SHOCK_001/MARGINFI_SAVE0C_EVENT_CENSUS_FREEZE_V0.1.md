# DEFI-LIQUIDATION-SHOCK-001 — MARGINFI + SAVE0C EVENT CENSUS FREEZE V0.1

Date: 2026-09-24
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Authority inherited
First-success source authority is already closed by the frozen boundary program:
- MARGINFI_FIRST_SUCCESS_BOUNDARY_SQD_PASS
- SAVE0C_FIRST_SUCCESS_BOUNDARY_SQD_PASS
- combined MARGINFI_SAVE0C_SQD_FIRST_SUCCESS_SOURCE_PASS

The event census reuses without alteration the frozen identities, exact UTC membership rule, SQD finalized-stream semantics, +16 transport envelope, success/failure/anomaly semantics, dedup identity, and firewall from MARGINFI_SAVE0C_SQD_FIRST_SUCCESS_BOUNDARY_FREEZE_V0.1.md.

## Census population
Marginfi: [2023-02-07T15:47:04Z, 2025-01-01T00:00:00Z)
Save0c: [2021-12-08T00:00:00Z, 2025-01-01T00:00:00Z)

The already-authoritative first partitions from run 36012206541 are reused and MUST NOT be recomputed:
- Marginfi 2023-02-07T15:47:04Z to 2023-03-01T00:00:00Z
- Save0c 2021-12-08T00:00:00Z to 2022-01-01T00:00:00Z

This workflow enumerates only the remaining months:
- Marginfi 2023-03 through 2024-12: 22 partitions
- Save0c 2022-01 through 2024-12: 36 partitions
- total new partitions: 58

Together with the 2 authoritative first partitions, expected complete census = 60 logical partitions.

## Terminal census requirements
No census PASS may be issued merely from GitHub Actions color.
Before terminal authority:
1. every expected partition exactly once;
2. exact contiguous UTC coverage with no gaps/overlaps;
3. every partition stream_complete=true;
4. every partition classification=SOURCE_PARTITION_PASS;
5. anomaly_count=0 for every partition;
6. rows_sha256 present and recomputable from rows;
7. dedup key protocol+signature+instructionAddress unique and collision-free;
8. successful and failed-attempt classes remain separate;
9. deterministic Official Solana RPC RAW reconciliation plan must be frozen before any RAW sample execution;
10. no price, amount, return, PnL, direction, economic outcome, or protected outcome may be opened.

Any missing/incomplete/hash-invalid/anomalous partition => fail closed with exact source state. A source blocker is never NO_EDGE.

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
