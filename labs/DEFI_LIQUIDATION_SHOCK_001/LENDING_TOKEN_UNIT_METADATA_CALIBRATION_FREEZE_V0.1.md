# DEFI-LIQUIDATION-SHOCK-001 — LENDING TOKEN UNIT METADATA CALIBRATION FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Calibrate whether exact historical liquidation transactions expose token mint identity and decimals
for protocol token accounts using SQD token-balance metadata only.

No token amounts, balances, prices, USD notional, returns or PnL are requested.

## Source fields authorized

TokenBalance identity/unit fields only:
- account
- preMint
- postMint
- preDecimals
- postDecimals

Forbidden:
- preAmount
- postAmount

## Frozen references

### Save0c
Slot 110526981
Signature 3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V
Program So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo
Prefix 0c
Token-account positions to calibrate:
- 0 source_liquidity_token_account
- 1 destination_collateral_token_account
- 3 repay_reserve_liquidity_supply
- 5 withdraw_reserve_collateral_supply

### Save11
Slot 278496102
Signature WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L
Program So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo
Prefix 11
Token-account positions:
- 0 source_liquidity
- 1 destination_collateral
- 4 repay_reserve_liquidity_supply
- 8 withdraw_reserve_liquidity_supply

### Kamino
Slot 230572965
Signature 2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv
Program KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD
Prefix b1479abce2854a37
Token-account positions:
- 5 repay_reserve_liquidity_supply
- 9 withdraw_reserve_liquidity_supply
- 11 user_source_liquidity
- 13 user_destination_liquidity

## Exact PASS

For each frozen reference:
1. recover the exact successful instruction and account list at the exact slot;
2. target only the frozen token-account positions above;
3. query token-balance identity/unit fields at the same slot;
4. require every target account to have at least one record with non-empty mint and integer decimals;
5. if both pre and post metadata exist, require mint and decimals consistency.

PASS:
`LENDING_TOKEN_UNIT_METADATA_12_OF_12_ACCOUNT_PASS`

Any missing identity, missing decimals, conflict, signature/program/prefix mismatch:
`LENDING_TOKEN_UNIT_METADATA_CALIBRATION_FAIL_CLOSED`

## Scope

PASS proves historical token-account mint+decimals retrieval for the calibrated account roles only.
It does not yet prove reserve/bank state metadata population-wide.

## Firewall

prices=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
token_amounts=false
token_balance_amounts=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
