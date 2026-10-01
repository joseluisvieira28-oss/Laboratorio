# DLS — MARGINFI Q1-2025 LIABILITY-REGIME SOURCE PERSISTENCE V0.1 — FREEZE

Date: 2026-10-01
Branch: dls-marginfi-2025-q1-regime-source-v01
Status: FROZEN SOURCE-ONLY / NO 2025 MARKET OUTCOMES

## Motivation

A source/feature-only audit of Oct-Nov-Dec 2024 showed a structural December regime:
- forced SOL cascade size increased by orders of magnitude;
- December liability composition became overwhelmingly stablecoin-denominated;
- USDC mint EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v accounted for 1,835 / 2,040
  source-proven Orca SOL liquidation events;
- USDT mint Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB accounted for another 183 / 2,040.

This probe asks only whether the Marginfi SOL-collateral / liability-mint regime persists into Q1 2025.

It does NOT read:
- Orca/Jupiter route outcomes;
- token amounts;
- market prices;
- returns;
- PnL;
- funding;
- market direction.

## Window

2025-01-01T00:00:00Z <= timestamp < 2025-04-01T00:00:00Z

Exactly three calendar-month partitions:
- 202501 [2025-01-01, 2025-02-01)
- 202502 [2025-02-01, 2025-03-01)
- 202503 [2025-03-01, 2025-04-01)

## Canonical instruction authority

Protocol:
Marginfi program MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA

Instruction:
lending_account_liquidate

Anchor discriminator:
d6a997d5fba756db

Historical fixed account roles:
- account[1] = asset_bank
- account[2] = liab_bank

Only successful committed matching instructions belong to the population.

## Bank-to-mint source authority

For every unique asset_bank and liab_bank:
- finalized Solana account owner MUST equal the Marginfi program;
- dataSlice offset 8 length 33;
- first 32 bytes = mint pubkey;
- byte 32 = decimals.

No oracle value, balance quantity, price or token amount is decoded.

## Required output

For every canonical instruction:
- signature
- instructionAddress
- slot
- timestamp
- transactionIndex
- asset_bank
- liab_bank
- asset_mint
- asset_decimals
- liab_mint
- liab_decimals

## Q1 source PASS

Each month:
MARGINFI_2025_Q1_LIABILITY_REGIME_MONTH_PASS

only if:
- full frozen month is scanned to source termination;
- duplicate canonical identities = 0;
- structural errors = 0;
- every event resolves both asset and liability mint;
- canonical timestamp belongs to exact month window.

Global:
MARGINFI_2025_Q1_LIABILITY_REGIME_SOURCE_PASS

only if all three months PASS and global duplicates = 0.

## Frozen descriptive diagnostics

For each month and Q1 total:
- successful Marginfi liquidation count;
- SOL-collateral event count;
- liability mint counts among SOL-collateral events;
- USDC liability count/share;
- USDT liability count/share;
- combined USDC+USDT liability count/share;
- top-1 liability mint/share;
- top-3 liability mints/share;
- distinct liability mint count.

These diagnostics are SOURCE-ONLY.
No trading-edge conclusion is authorized.

## Consequence

If Q1 source PASS shows the stablecoin-liability regime persists, that may justify a separately frozen
2025 source-route/feature validation before any 2025 market outcome is opened.

If it does not persist, December remains a localized 2024 source regime and no 2025 market validation
is authorized from this probe.

## Firewall

prices_2025_opened=false
returns_2025_opened=false
pnl_2025_opened=false
funding_2025_opened=false
market_direction_2025_opened=false
prices_2026_opened=false
returns_2026_opened=false
token_amounts=false
oracle_values=false
post_outcome_tuning=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
