# DEFI-LIQUIDATION-SHOCK-001 — SOLANAFM INDEX TRANSPORT EQUIVALENCE FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-ACCESS / SOURCE-ONLY / OUTCOME-BLIND / ZERO-COST

## Purpose

Evaluate SolanaFM's historical account-transactions index as a free transport/index layer for the already-frozen Kamino first-success boundary search.

SolanaFM is NOT accepted as final event authority. Final classification remains based on official/public Solana JSON-RPC raw transaction verification using the exact frozen program ID and instruction discriminator.

## Frozen science unchanged

Lab: DEFI-LIQUIDATION-SHOCK-001
Protocol: kamino_lend
Program ID: KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD
Instruction: liquidate_obligation_and_redeem_reserve_collateral
Discriminator: b1479abce2854a37
Source-supported-from: 2023-11-17T13:25:35Z
Historical end exclusive: 2025-01-01T00:00:00Z
Max chronological chunk: 7 UTC days

## Equivalence audit window

Only the already-open source-only reference day:
[2024-12-15T00:00:00Z, 2024-12-16T00:00:00Z)

Known corrected BigQuery population:
- 41 candidate rows/signatures;
- 16 successful;
- 25 failed;
- 0 source anomalies;
- all 16 successful subsequently RAW verified against official public Solana RPC.

## Candidate index endpoint

GET https://api.solana.fm/v0/accounts/{program_id}/transactions

Frozen query parameters for equivalence:
- utcFrom = 1734220800
- utcTo = 1734307200
- limit = 1000
- page = 1..N until exhaustion

No API key, account creation, payment or wallet is authorized.

## Equivalence requirements

The index route may advance only if:
1. the exact 41 known BigQuery candidate signatures are all present in the SolanaFM program-account day population;
2. known slots/timestamps are compatible where those fields are exposed;
3. known success/failure state is compatible where exposed;
4. pagination terminates deterministically with no transport error;
5. every indexed row needed for final classification has a signature usable with public Solana getTransaction;
6. after public-RPC RAW verification of the complete indexed day population (or a deterministic source-preserving subset proven by raw instruction data), the exact corrected discriminator population can be reproduced.

Missing known signatures => SOLANAFM_INDEX_EQUIVALENCE_FAIL_CLOSED.
Authentication/payment requirement => SOLANAFM_INDEX_ACCESS_BLOCKED.
Transport/schema insufficiency => SOLANAFM_INDEX_INSUFFICIENT.
Exact/superset reproducibility => SOLANAFM_INDEX_EQUIVALENCE_PASS.

Only after PASS may a separate prospective transport amendment authorize scanning the frozen 2023-11-17..2025-01-01 chronology.

## Firewall

No prices, returns, PnL, direction, event-size threshold tuning, 2025/2026 market outcomes, live trading, orders, wallets, exchange mutation, paid data, merge to main.
