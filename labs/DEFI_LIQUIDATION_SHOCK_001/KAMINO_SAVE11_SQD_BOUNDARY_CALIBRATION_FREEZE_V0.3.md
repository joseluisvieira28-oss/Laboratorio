# DEFI-LIQUIDATION-SHOCK-001 — SQD BOUNDARY CALIBRATION FREEZE V0.3

Date: 2026-09-23
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose

Calibrate the public SQD Portal Solana archive against two already-closed RAW-verified first-success boundaries before SQD is allowed to contribute to the historical event census.

SQD is a candidate index/census source, not a replacement for canonical RAW validation.

Endpoint:
`https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream`

No API key is supplied.

## Frozen controls

### Kamino
Program:
`KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`

Filter:
- programId exact;
- `d8 = 0xb1479abce2854a37`;
- slot range `[230572957, 230572973]`.

Expected known RAW authority:
- slot `230572965`;
- signature `2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv`;
- timestamp `2023-11-17T14:48:24Z`.

### Save/Solend 0x11
Program:
`So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`

Filter:
- programId exact;
- `d1 = 0x11`;
- slot range `[278496094, 278496110]`.

Expected known RAW authority:
- slot `278496102`;
- signature `WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L`;
- timestamp `2024-07-19T19:30:52Z`.

## Requested fields

Only:
- block number + timestamp;
- transaction signatures + err;
- instruction programId + data + transactionIndex + instructionAddress + isCommitted + error.

No accounts, balances, token balances, prices, amounts, returns, PnL or direction.

The instruction filter requests its parent transaction so the instruction can be joined deterministically to the transaction signature/error state.

## PASS rule

`SQD_BOUNDARY_CALIBRATION_PASS` requires BOTH controls to:
1. return HTTP 200;
2. include the expected exact slot;
3. include the expected exact signature linked to the matching instruction;
4. preserve the exact program ID;
5. preserve the frozen discriminator/tag;
6. show transaction `err = null`;
7. show instruction `isCommitted = true`;
8. expose a non-empty `instructionAddress` so outer/CPI location is reconstructible.

Any contradiction => `SOURCE_ANOMALY_FAIL_CLOSED`.
Transport/filter rejection => `SQD_BOUNDARY_CALIBRATION_BLOCKED`.
Only one control matching => `SQD_BOUNDARY_CALIBRATION_PARTIAL`.

No edge/no-edge classification is possible.

## Firewall

prices=false; token_balances=false; balances=false; amounts=false; returns=false; pnl=false; direction=false; economic_outcomes=false; protected_2025_2026_market_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; account_creation=false; merge_main=false.
