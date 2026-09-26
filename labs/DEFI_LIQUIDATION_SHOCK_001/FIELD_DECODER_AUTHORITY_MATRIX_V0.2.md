# DEFI-LIQUIDATION-SHOCK-001 — FIELD DECODER AUTHORITY MATRIX V0.2

Date: 2026-09-26
Status: SOURCE-ONLY / OUTCOME-BLIND / FIELD DECODER AUTHORITY COMPLETE

This supersedes V0.1 for future execution while preserving V0.1 unchanged as audit history.

## Unchanged V0.1 authorities

The following historical account/argument decoders remain unchanged from
`FIELD_DECODER_AUTHORITY_MATRIX_V0.1.md`:

- Kamino Lend — `KAMINO_ACCOUNT_AND_ARGUMENT_DECODER_SOURCE_PASS`
- marginfi v2 — `MARGINFI_CORE_ACCOUNT_AND_ARGUMENT_DECODER_SOURCE_PASS`
- Drift `liquidate_perp` — `DRIFT_LIQUIDATE_PERP_DECODER_SOURCE_PASS`
- Drift `liquidate_spot` — `DRIFT_LIQUIDATE_SPOT_DECODER_SOURCE_PASS`
- Drift `liquidate_borrow_for_perp_pnl` — `DRIFT_LIQUIDATE_BORROW_FOR_PERP_PNL_DECODER_SOURCE_PASS`
- Drift `liquidate_perp_pnl_for_deposit` — `DRIFT_LIQUIDATE_PERP_PNL_FOR_DEPOSIT_DECODER_SOURCE_PASS`
- Save/Solend `0x11` — `SAVE11_ACCOUNT_AND_ARGUMENT_DECODER_SOURCE_PASS`

All requested/max amount fields remain distinct from realized transfer amounts.

## Save / Solend 0x0c — independent historical ABI reconciliation closed

Direct Solend source authority:

- repository: `solendprotocol/solend-sdk`
- commit: `c93fbc81fcc68610ad64fbce4a170a38335b7d7f`
- date: 2021-12-08
- direct fact: `LiquidateObligation = 12`

Independent historical ABI source:

- repository: `solana-labs/solana-program-library`
- commit: `fd662e5f878d58ad06d3cb6365171ebaec41b39d`
- date: 2021-08-18
- instruction: `LiquidateObligation`
- layout: tag 12 + `liquidity_amount: u64`
- account count: 12

Frozen Save0c first-success on-chain reconciliation:

- program: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`
- signature: `3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V`
- slot: `110526981`
- timestamp: `2021-12-08T00:03:43Z`
- instruction address: `[3]`
- successful transaction
- exact 9-byte instruction data
- exact tag `0x0c`
- exact 12-account instruction
- Clock sysvar at position 10
- SPL Token program at position 11
- stable reserve/obligation/lending-market owner checks matched the frozen Solend program
- surviving token-account positions matched SPL Token ownership

Historical closed-user-token-account correction:

V0.1 current-state owner checking returned null for account positions 0 and 1 because those user token
accounts no longer exist today. The correction did not relax account semantics.

SQD was queried at the exact historical slot requesting only:
- `tokenBalance.account`
- `preMint`
- `postMint`

No amount or decimal fields were requested.

Receipt:

`SAVE0C_HISTORICAL_TOKEN_IDENTITY_2_OF_2_PASS`

Both account positions 0 and 1 had historical token-balance records with mint identity.

Combined receipt:

`SAVE0C_INDEPENDENT_ABI_RECONCILIATION_RECEIPT_V0.2.json`

Classification:

`SAVE0C_INDEPENDENT_ABI_RECONCILIATION_PASS`

### Frozen Save0c field decoder

Data:
- byte 0: tag `0x0c`
- bytes 1..8: requested `liquidity_amount: u64`, little-endian

Account roles:

0. source_liquidity_token_account
1. destination_collateral_token_account
2. repay_reserve
3. repay_reserve_liquidity_supply
4. withdraw_reserve
5. withdraw_reserve_collateral_supply
6. obligation
7. lending_market
8. derived_lending_market_authority
9. user_transfer_authority
10. clock_sysvar
11. token_program

The requested `liquidity_amount` is NOT frozen as realized repayment or economic notional.

Classification:

`SAVE0C_ACCOUNT_AND_ARGUMENT_DECODER_INDEPENDENT_RECONCILIATION_PASS`

## Global field-decoder verdict

Eight frozen liquidation classes / encodings are now source-defensable:

1. Save0c — PASS
2. Save11 — PASS
3. marginfi — PASS
4. Kamino — PASS
5. Drift liquidate_perp — PASS
6. Drift liquidate_spot — PASS
7. Drift liquidate_borrow_for_perp_pnl — PASS
8. Drift liquidate_perp_pnl_for_deposit — PASS

Terminal field-decoder classification:

`FIELD_DECODER_AUTHORITY_8_OF_8_CLASS_PASS`

This closes decoder semantics only. It does not by itself close population-wide enrichment coverage,
unit/precision metadata, realized-transfer reconstruction, the numerical Sample Gate, or economic Discovery.

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
