# DEFI-LIQUIDATION-SHOCK-001 — MARGINFI BANK METADATA DATASLICE CALIBRATION FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Historical authority

Pinned source:
`0dotxyz/marginfi-v2@f6d3d5616e293c9468333571c3ceb90bb2410b00`

Historical Bank layout:
- Anchor account discriminator: 8 bytes
- Bank.mint: Pubkey, first 32 bytes of zero-copy Bank struct
- Bank.mint_decimals: u8, immediately after mint

Candidate account slice:
- offset 8
- length 33
- bytes 0..31: mint
- byte 32: mint_decimals

No other Bank fields may be requested or decoded by this calibration.

## Calibration reference

Frozen Marginfi first success:
- slot 177590210
- signature 2aW2TWwxxzTTFixuYnvaA2NpentUDu6vCLxPjkvYBJWcrmB9TcRYu63uAswCrAjHJt7VXZxYUBaJsp3SGH3zNBmK
- program MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA
- instruction lending_account_liquidate
- fixed accounts:
  - asset_bank position 1
  - liab_bank position 2
  - bank_liquidity_vault position 7

## Independent reconciliation

At the exact historical transaction:
1. retrieve accounts and tokenBalance identity/unit metadata only;
2. derive the liquidity-vault mint+decimals from account 7;
3. query current finalized liab_bank account with only dataSlice offset 8 length 33;
4. require owner == Marginfi program;
5. require Bank slice mint+decimals exactly equals the historical liquidity-vault mint+decimals.

Also query asset_bank with the same slice only to verify:
- account exists;
- owner == Marginfi program;
- exact slice length 33;
- non-empty mint.

PASS:
`MARGINFI_BANK_METADATA_DATASLICE_CALIBRATION_PASS`

This proves the slice/layout route, not population coverage.

## Conditional use

If `MARGINFI_BANK_UNIT_REGISTRY_RECEIPT_V0.1.json` returns
`MARGINFI_BANK_UNIT_REGISTRY_PARTIAL_SOURCE_COVERAGE`,
this calibrated slice may be queried ONLY for the exact listed unmapped asset banks.

No bank may be selected based on outcomes.

## Firewall

prices=false
oracle_values=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
bank_balances=false
share_values=false
token_amounts=false
protected_market_outcomes_2025_2026=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
