# DEFI-LIQUIDATION-SHOCK-001 — KAMINO PUBLIC RPC RAW VERIFICATION FREEZE V0.1

Date: 2026-09-21  
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose

RAW-verify the 16 already-frozen successful Kamino reference candidates recovered from the corrected 2024-12-15 BigQuery smoke test.

This is a transport/source verification only. It does not search for new events and does not open market prices, future returns, direction, PnL or any economic outcome.

## Fixed source

Primary endpoint for this execution:
`https://api.mainnet-beta.solana.com`

RPC method:
`getTransaction`

Encoding:
`jsonParsed`

No API key, wallet, paid provider, exchange, identity submission or account creation is authorized.

## Fixed decoder

Protocol: Kamino Lend  
Program ID: `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`  
Instruction: `liquidate_obligation_and_redeem_reserve_collateral`  
Correct Anchor discriminator: `b1479abce2854a37`  
Source-supported-from boundary: `2023-11-17T13:25:35Z`

## Frozen candidate set

Exactly 16 BigQuery-success candidates from 2024-12-15 are authorized. No candidate addition, deletion or substitution is permitted after this freeze.

For each candidate, RAW verification requires all:

1. RPC result is non-null;
2. returned slot equals frozen BigQuery slot;
3. `meta.err == null`;
4. a top-level or inner instruction resolves to the frozen Kamino program ID;
5. that instruction's base58 data decodes to bytes beginning with `b1479abce2854a37`.

A candidate satisfying all five is `RAW_VERIFIED_SUCCESSFUL_KAMINO_LIQUIDATION_REFERENCE`.

Any mismatch is fail-closed. RPC `null`, rate limiting, transport failure or historical unavailability is a source transport blocker, not a scientific failure.

## Routing

- 16/16 RAW verified: `KAMINO_SMOKE_RAW_VERIFICATION_PASS`
- 1..15 RAW verified with remaining transport-unavailable rows: `KAMINO_SMOKE_RAW_VERIFICATION_PARTIAL_TRANSPORT_BLOCKED`
- deterministic content mismatch: `KAMINO_SMOKE_RAW_VERIFICATION_CONTENT_MISMATCH_FAIL_CLOSED`
- zero retrievable due endpoint history/transport: `KAMINO_PUBLIC_RPC_HISTORY_UNAVAILABLE`

None of these states grants global `SOURCE_DATA_PASS` for the lab. A pass establishes only that the corrected Kamino decoder has realized on-chain examples by 2024-12-15 and permits continuation of the pre-frozen first-success boundary search.

## Firewalls

- new candidate search: false
- prices queried: false
- returns computed: false
- PnL computed: false
- direction tested: false
- 2025/2026 market outcomes: false
- live trading: false
- orders: false
- wallets: false
- exchange mutation: false
- paid source: false
- merge main: false
