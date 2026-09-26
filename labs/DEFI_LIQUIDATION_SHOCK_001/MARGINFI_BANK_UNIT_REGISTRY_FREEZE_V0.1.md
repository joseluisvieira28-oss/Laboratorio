# DEFI-LIQUIDATION-SHOCK-001 — MARGINFI BANK UNIT REGISTRY FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Historical authority

Pinned Marginfi source:
`0dotxyz/marginfi-v2@f6d3d5616e293c9468333571c3ceb90bb2410b00`

For `lending_account_liquidate` the frozen fixed accounts are:
- 1 asset_bank
- 2 liab_bank
- 7 bank_liquidity_vault

The historical Accounts constraints derive `bank_liquidity_vault` from
`liab_bank.key()` using the liquidity-vault seed. Therefore account 7 is source-authoritative
as the liability bank's SPL liquidity vault.

The same source uses `Bank.mint_decimals` for unit scaling.

## Source-only registry construction

For every frozen realized Marginfi liquidation event:
1. exact-join the canonical event identity;
2. recover fixed accounts 1, 2 and 7;
3. use exact d8 + isCommitted + transactionTokenBalances relation;
4. from account 7 tokenBalance identity/unit metadata, recover:
   - mint
   - decimals
5. emit registry observation:
   `liab_bank -> mint + decimals`.

No preAmount/postAmount is requested.

## Asset-bank coverage rule

Separately collect every `asset_bank` and every `liab_bank` appearing in the frozen realized population.

After all partitions:
- build the unique liability-bank registry;
- require zero conflicting mint/decimals for any bank;
- join every asset_bank against that registry.

If every asset_bank has also appeared as a liability bank with a source-authoritative registry observation:
`MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS`

If one or more asset banks never receive a liability-side registry observation:
`MARGINFI_BANK_UNIT_REGISTRY_PARTIAL_SOURCE_COVERAGE`

The missing banks remain explicit and may be attacked by a separate historical Bank-state or Bank-initialization source route. They MUST NOT be guessed.

## Event population rule

The registry process must exact-join the frozen Marginfi source population:
266,647 successful events.

No event may be added or removed based on unit metadata availability.

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
