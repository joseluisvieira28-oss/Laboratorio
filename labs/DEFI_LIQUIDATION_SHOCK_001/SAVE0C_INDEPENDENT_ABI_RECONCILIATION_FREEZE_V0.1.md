# DEFI-LIQUIDATION-SHOCK-001 — SAVE0C INDEPENDENT ABI RECONCILIATION FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose

Attempt to close the remaining Save/Solend native `0x0c` field-decoder gap using independent historical ABI reconciliation rather than silently back-applying a current Solend SDK.

## Evidence frozen before adjudication

### Direct Solend historical evidence

Archived `solendprotocol/solend-sdk` commit:

`c93fbc81fcc68610ad64fbce4a170a38335b7d7f`

Date: 2021-12-08.

It assigns:

`LiquidateObligation = 12`

Therefore byte 0 = `0x0c` is direct Solend historical authority.

### Independent upstream ABI source

Historical Solana Program Library token-lending commit:

`fd662e5f878d58ad06d3cb6365171ebaec41b39d`

Date: 2021-08-18.

Its `LiquidateObligation` ABI specifies:

Data:
- tag 12;
- `liquidity_amount: u64` little-endian.

Accounts:
0. source liquidity token account
1. destination collateral token account
2. repay reserve
3. repay reserve liquidity supply
4. withdraw reserve
5. withdraw reserve collateral supply
6. obligation
7. lending market
8. derived lending market authority
9. user transfer authority
10. Clock sysvar
11. Token program

This upstream source is NOT, by itself, Solend historical authority.

### Solend on-chain first-success evidence

Frozen RAW-verified Save0c first success:

- slot: 110526981
- timestamp: 2021-12-08T00:03:43Z
- signature: 3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V
- program: So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo
- instruction address: [3]

Field-enrichment calibration already proves:
- instruction account count = 12;
- instruction data byte length = 9;
- byte 0 = `0x0c`;
- account 10 = `SysvarC1ock11111111111111111111111111111111`;
- account 11 = `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`.

## Required RPC ownership reconciliation

Using official Solana mainnet RPC on the exact 12 accounts:

Expected owner pattern:
- accounts 0,1,3,5: SPL Token program;
- accounts 2,4,6,7: frozen Solend program;
- account 10: exact Clock sysvar identity;
- account 11: exact Token program identity.

Accounts 8 and 9 are role-structural:
- 8 derived lending-market authority;
- 9 transfer authority;
and are not required to have a specific account owner for this calibration.

## Exact PASS rule

`SAVE0C_INDEPENDENT_ABI_RECONCILIATION_PASS` only if:

1. direct Solend source proves tag 12;
2. exact on-chain data is 9 bytes with tag 12;
3. exact on-chain account count is 12;
4. Clock and Token Program tail positions match the historical upstream ABI;
5. all token-account positions resolve to SPL Token ownership;
6. reserve/obligation/lending-market positions resolve to frozen Solend program ownership;
7. transaction is successful and already RAW-authoritative.

If any required check fails:

`SAVE0C_INDEPENDENT_ABI_RECONCILIATION_FAIL_CLOSED`

## Consequence

PASS permits the pre-Discovery field decoder to interpret Save0c as:
- byte 0: native tag 12;
- bytes 1..8: requested `liquidity_amount: u64`;
- account roles 0..11 according to the reconciled ABI above.

This remains source-field authority only.

The requested liquidity amount MUST NOT be equated to realized transfer, USD notional, price impact, return or PnL.

## Firewall

prices=false
returns=false
pnl=false
direction=false
economic_outcomes=false
balances=false
token_amounts=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
