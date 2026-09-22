# DEFI-LIQUIDATION-SHOCK-001 — SOLSCAN PLAYGROUND INDEX EQUIVALENCE FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-ACCESS / SOURCE-ONLY / OUTCOME-BLIND / ZERO-COST

Purpose: test the publicly documented Solscan enhanced-transactions playground strictly as an index/transport candidate for the frozen Kamino liquidation source gate.

No account creation, API key generation, payment, wallet, subscription or identity submission is authorized.

Frozen equivalence window:
[2024-12-15T00:00:00Z, 2024-12-16T00:00:00Z)

Frozen protocol:
- program: KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD
- instruction discriminator: b1479abce2854a37
- expected corrected BigQuery source-only population: 41 signatures, 16 Success, 25 Fail.

Candidate endpoint documented by Solscan:
https://pro-api.solscan.io/playground/account/transactions/enhanced

Allowed filters are fixed before access:
- address = frozen Kamino program
- from_time = 1734220800
- to_time = 1734307200
- instruction[] = frozen program ID + frozen 8-byte discriminator
- limit = provider maximum supported by the playground
- pagination only through returned cursor

Acceptance:
- public unauthenticated access must work;
- no paid/auth wall may be crossed;
- all 41 known reference signatures must be reproduced with compatible slots/status;
- any candidate used scientifically must still be RAW verified on public Solana RPC.

If authentication/payment is required: SOLSCAN_PLAYGROUND_ACCESS_BLOCKED.
If transport/schema cannot reproduce known population: SOLSCAN_PLAYGROUND_EQUIVALENCE_FAIL_CLOSED.
Only a successful equivalence audit permits a separate prospective transport amendment.

No economic outcome access is authorized.
