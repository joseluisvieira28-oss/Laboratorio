# DEFI-LIQUIDATION-SHOCK-001 — KAMINO TEMPORAL DECODER & UNIT AUTHORITY ADDENDUM V0.3

Date: 2026-09-27
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Why this addendum exists

The original Kamino field decoder was frozen from the first supported source state:

- repository: `Kamino-Finance/klend`
- commit: `57074f4599a36ab0b433a71599b206c73efe1fd7`
- date: 2023-11-17
- liquidation layout: exactly 16 fixed instruction accounts

Population enrichment later proved:
- June 2024 canonical event join: 3,122 / 3,122 exact identities;
- missing=0, extra=0, duplicate=0;
- instruction data remains exactly 32 bytes;
- account counts evolve from 16 to 20+.

This is decoder-version evolution, not event-population failure.

## Source proof of V1.6 account evolution

Official commit:

`509e98aac6f909cf3e7977e613e503904cf77d00`

- date: 2024-06-19T15:31:40Z
- message: `Release 1.6.0 (#13)`
- file: `programs/klend/src/handlers/handler_liquidate_obligation_and_redeem_reserve_collateral.rs`

The diff explicitly:
- adds `repay_reserve_liquidity_mint`;
- adds `withdraw_reserve_liquidity_mint`;
- replaces one token program with three token-program accounts;
- passes `ctx.remaining_accounts` into liquidation;
- retains the same frozen liquidation instruction/discriminator and 32-byte argument encoding.

V1.6 fixed account prefix is 20 accounts, followed by zero or more dynamic remaining accounts.

Population source-only shape evidence in June 2024:
- 16 accounts: 1,874 events, latest 2024-06-18T19:56:29Z;
- first 20+ account event: 2024-06-19T19:15:17Z;
- observed V1.6 counts: 20,21,22,23,24,25,26;
- all retain 32-byte instruction data.

Frozen on-chain deployment-shape boundary:
`2024-06-19T19:15:17Z`

This boundary is source/event-structure metadata only. No market outcomes are consulted.

## Temporal decoder V1 — legacy

Applicable before:
`2024-06-19T19:15:17Z`

Require exactly 16 accounts.

0 liquidator
1 obligation
2 lending_market
3 lending_market_authority
4 repay_reserve
5 repay_reserve_liquidity_supply
6 withdraw_reserve
7 withdraw_reserve_collateral_mint
8 withdraw_reserve_collateral_supply
9 withdraw_reserve_liquidity_supply
10 withdraw_reserve_liquidity_fee_receiver
11 user_source_liquidity
12 user_destination_collateral
13 user_destination_liquidity
14 token_program
15 instruction_sysvar_account

## Temporal decoder V2 — Release 1.6+

Applicable from:
`2024-06-19T19:15:17Z`

Require at least 20 accounts.

0 liquidator
1 obligation
2 lending_market
3 lending_market_authority
4 repay_reserve
5 repay_reserve_liquidity_mint
6 repay_reserve_liquidity_supply
7 withdraw_reserve
8 withdraw_reserve_liquidity_mint
9 withdraw_reserve_collateral_mint
10 withdraw_reserve_collateral_supply
11 withdraw_reserve_liquidity_supply
12 withdraw_reserve_liquidity_fee_receiver
13 user_source_liquidity
14 user_destination_collateral
15 user_destination_liquidity
16 collateral_token_program
17 repay_liquidity_token_program
18 withdraw_liquidity_token_program
19 instruction_sysvar_account
20+ remaining_accounts

Any 20+ account event before the official V1.6 source commit is fail-closed.
Any 16-account event at/after the frozen on-chain V2 boundary is fail-closed.

## Unit metadata authority correction

The original unit runner required matching token metadata from both:
- protocol reserve vault; and
- user token account.

Two March 2024 realized events had canonical joins 13,061 / 13,061 and only failed because
`user_destination_liquidity` had no token-balance metadata while the protocol reserve liquidity supply
unambiguously carried SOL mint + 9 decimals.

Historical handler authority shows the reserve supply vault is constrained by the Reserve account:
- legacy `repay_reserve_liquidity_supply` = reserve liquidity supply vault;
- legacy `withdraw_reserve_liquidity_supply` = reserve liquidity supply vault;
- V1.6 preserves these vault constraints and adds explicit liquidity mint accounts.

Frozen unit rule:

For each semantic unit role use the protocol-controlled reserve/supply account as PRIMARY authority.

Legacy:
- debt_underlying primary account 5; optional user cross-check 11
- collateral_token primary account 8; optional user cross-check 12
- collateral_underlying primary account 9; optional user cross-check 13

V1.6+:
- debt_underlying primary account 6; optional user cross-check 13
- collateral_token primary account 10; optional user cross-check 14
- collateral_underlying primary account 11; optional user cross-check 15

PRIMARY must resolve to exactly one (mint, decimals) token metadata pair.

Optional user cross-check semantics:
- zero metadata pairs: allowed, reported as unavailable optional cross-check;
- exactly one pair: must equal PRIMARY;
- more than one pair or a different pair: fail closed.

No token amount fields are requested.

## Required recovery result

Known field failure `kamino-202406` must be re-run under this temporal decoder.
Known unit failure `kamino-202403` must be re-run under the primary-vault rule.

Recovery is authority-valid only with:
- canonical missing=0;
- extra=0;
- duplicates=0;
- semantic/source conflicts=0.

## Firewall

prices=false
oracle_values=false
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
