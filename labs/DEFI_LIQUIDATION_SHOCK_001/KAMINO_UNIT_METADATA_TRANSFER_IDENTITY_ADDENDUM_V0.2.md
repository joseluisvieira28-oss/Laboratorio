# DEFI-LIQUIDATION-SHOCK-001 — KAMINO UNIT METADATA TRANSFER-IDENTITY ADDENDUM V0.2

Date: 2026-09-27
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND / NARROW MISSING-METADATA FALLBACK

## Trigger

Original Kamino unit partition 2024-03:
- baseline_success_count = 13,061
- enriched_success_count = 13,061
- unit_complete_event_count = 13,059
- missing = 0
- extra = 0
- query anomalies = 0
- unit conflicts = 2

Both incomplete events have the same pattern:
- withdraw_reserve_liquidity_supply token-balance metadata resolves exactly to wrapped SOL, decimals 9;
- user_destination_liquidity has no SQD token-balance metadata record;
- no contradictory mint/decimals is present.

This is metadata absence on one account, not an identity contradiction.

## Official Kamino transfer semantics

Historical official source:
`Kamino-Finance/klend@57074f4599a36ab0b433a71599b206c73efe1fd7`

Legacy liquidation calls:
`redeem_reserve_collateral_transfer(... reserve_liquidity_supply, destination_liquidity ...)`

The token-transfer implementation executes:
`token::transfer { from: reserve_liquidity_supply, to: destination_liquidity }`

A successful SPL Token transfer requires source and destination token accounts to have the same mint.

The same source path also directly transfers:
- user_source_liquidity -> repay_reserve_liquidity_supply
- withdraw_reserve_collateral_supply -> user_destination_collateral

Release 1.6+ preserves equivalent source/destination token identity constraints, using token-interface / transfer_checked semantics for liquidity transfers.

## Frozen fallback rule

For each Kamino unit pair already frozen by historical account layout:

1. If both token accounts have exactly one mint+decimals pair:
   - require exact equality;
   - resolution = TOKEN_BALANCE_PAIR_DIRECT.

2. If exactly one side has exactly one mint+decimals pair and the other side has zero metadata records:
   - require the instruction is a realized successful frozen Kamino liquidation;
   - require the two account positions are the exact source-linked transfer pair for that historical layout;
   - inherit mint+decimals from the observed side;
   - resolution = SINGLE_TOKEN_BALANCE_PLUS_SUCCESSFUL_TRANSFER_IDENTITY.

3. If either side exposes >1 conflicting metadata pair:
   FAIL_CLOSED.

4. If both sides expose zero metadata:
   SOURCE_PARTIAL / FAIL partition under the current population gate.

5. If both sides expose one pair but differ:
   FAIL_CLOSED.

This fallback does not use token amounts.

## Scope

Kamino only.

Save11 retains the original exact two-account pair rule unless separately frozen by source evidence.

## Audit requirement

Population receipts must count:
- direct pair resolutions;
- single-side transfer-identity fallback resolutions;
- unresolved pairs;
- conflicts.

Fallback resolution count is reported and never hidden.

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
post_outcome_tuning=false
live_trading=false
merge_main=false
