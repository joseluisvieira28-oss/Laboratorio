# DEFI-LIQUIDATION-SHOCK-001 — FIELD DECODER AUTHORITY MATRIX V0.1

Date: 2026-09-26
Status: SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose

Freeze protocol/class-specific source authority for account roles and instruction arguments needed by the pre-Discovery field-enrichment layer.

This matrix does **not** equate instruction request/max amounts with realized transfer amounts and does not authorize prices, USD notional, returns or PnL.

Transport prerequisite:
`FIELD_ENRICHMENT_TRANSPORT_8_OF_8_PASS`

Historical applicability authority remains:
`HISTORICAL_DECODER_AUTHORITY_MATRIX_V0.3.md`

---

## Kamino Lend

Historical source:
- repository: `Kamino-Finance/klend`
- commit: `57074f4599a36ab0b433a71599b206c73efe1fd7`
- date: 2023-11-17
- file: `programs/klend/src/handlers/handler_liquidate_obligation_and_redeem_reserve_collateral.rs`

Instruction:
`liquidate_obligation_and_redeem_reserve_collateral`

Discriminator:
`b1479abce2854a37`

### Fixed account order

0. liquidator
1. obligation
2. lending_market
3. lending_market_authority
4. repay_reserve
5. repay_reserve_liquidity_supply
6. withdraw_reserve
7. withdraw_reserve_collateral_mint
8. withdraw_reserve_collateral_supply
9. withdraw_reserve_liquidity_supply
10. withdraw_reserve_liquidity_fee_receiver
11. user_source_liquidity
12. user_destination_collateral
13. user_destination_liquidity
14. token_program
15. instruction_sysvar_account

Historical first-success calibration returned exactly 16 accounts.

### Instruction args

After the 8-byte Anchor discriminator:
- `liquidity_amount: u64`
- `min_acceptable_received_collateral_amount: u64`
- `max_allowed_ltv_override_percent: u64`

Observed first-success data length: 32 bytes = 8 discriminator + 24 argument bytes.

Semantics:
- `liquidity_amount` = requested liquidation liquidity amount;
- it is NOT frozen as realized repayment;
- actual realized amounts require source-state/event reconstruction and remain separate.

Classification:

`KAMINO_ACCOUNT_AND_ARGUMENT_DECODER_SOURCE_PASS`

---

## marginfi v2

Historical source:
- repository history preserved at `0dotxyz/marginfi-v2`
- exact historical commit: `f6d3d5616e293c9468333571c3ceb90bb2410b00`
- message: `fix(sc): update the marginfi mainnet pk`
- date: 2023-02-07
- file: `programs/marginfi/src/instructions/marginfi_account/liquidate.rs`

Instruction:
`lending_account_liquidate`

Discriminator:
`d6a997d5fba756db`

### Fixed account order

0. marginfi_group
1. asset_bank
2. liab_bank
3. liquidator_marginfi_account
4. signer
5. liquidatee_marginfi_account
6. bank_liquidity_vault_authority
7. bank_liquidity_vault
8. bank_insurance_vault
9. token_program

Additional `remaining_accounts` are dynamic.

The historical handler explicitly consumes:
- remaining account 0 as the asset-bank price feed;
- remaining account 1 as the liability-bank price feed;
- later remaining accounts as risk-engine account context split between liquidator and liquidatee.

Observed first-success instruction contains 20 total accounts, consistent with fixed + dynamic account context.

### Instruction args

After the 8-byte Anchor discriminator:
- `asset_quantity: u64`

Observed first-success data length: 16 bytes = 8 discriminator + 8 argument bytes.

Historical handler states `asset_quantity` is the collateral quantity requested to be liquidated.

Semantics:
- direct requested collateral quantity;
- NOT automatically realized liability repayment;
- liability quantity is computed by protocol logic and must not be inferred from the requested amount without source-state reconstruction.

Asset/liability bank identities are directly recoverable from accounts 1 and 2.
Mint identity/decimals require pinned Bank account metadata.

Classification:

`MARGINFI_CORE_ACCOUNT_AND_ARGUMENT_DECODER_SOURCE_PASS`

---

## Drift v2 — four frozen classes

Historical source:
- history preserved at `velocity-exchange/protocol-v2`
- exact historical commit: `e77518dec79b9ade13680d1d8da1a479aca759b1`
- message: `sdk: update mainnet program id`
- date: 2022-11-04
- IDL: `sdk/src/idl/drift.json`

Common fixed accounts for all four frozen liquidation instructions:

0. state
1. authority — signer
2. liquidator
3. liquidatorStats
4. user — liquidated user account
5. userStats

Additional remaining accounts carry market/oracle context and are not assigned semantic positions by this fixed-account IDL section.

### liquidate_perp

Discriminator: `4b2377f7bf128b02`

Args:
- `marketIndex: u16`
- `liquidatorMaxBaseAssetAmount: u64`
- `limitPrice: Option<u64>`

Classification:
`DRIFT_LIQUIDATE_PERP_DECODER_SOURCE_PASS`

### liquidate_spot

Discriminator: `6b00802923e5fb12`

Args:
- `assetMarketIndex: u16`
- `liabilityMarketIndex: u16`
- `liquidatorMaxLiabilityTransfer: u128`
- `limitPrice: Option<u64>`

Classification:
`DRIFT_LIQUIDATE_SPOT_DECODER_SOURCE_PASS`

### liquidate_borrow_for_perp_pnl

Discriminator: `a911205acf94d11b`

Args:
- `perpMarketIndex: u16`
- `spotMarketIndex: u16`
- `liquidatorMaxLiabilityTransfer: u128`
- `limitPrice: Option<u64>`

Classification:
`DRIFT_LIQUIDATE_BORROW_FOR_PERP_PNL_DECODER_SOURCE_PASS`

### liquidate_perp_pnl_for_deposit

Discriminator: `ed4bc6ebe9ba4b23`

Args:
- `perpMarketIndex: u16`
- `spotMarketIndex: u16`
- `liquidatorMaxPnlTransfer: u128`
- `limitPrice: Option<u64>`

Classification:
`DRIFT_LIQUIDATE_PERP_PNL_FOR_DEPOSIT_DECODER_SOURCE_PASS`

### Drift semantic rule

Market indexes are direct instruction arguments.

The `liquidatorMax*` fields are caps/requested maxima, not frozen as realized transfer values.

Actual market mint/precision metadata requires historical Drift market-state authority keyed by market index.

Common account-role mapping plus direct market-index args is sufficient to identify:
- liquidated user account;
- liquidator account;
- perp/spot market index roles.

---

## Save / Solend 0x11

Historical source:
- repository: `solendprotocol/public`
- exact commit: `91d2936930b412ce752be71c6d166deba65489cc`
- date: 2024-07-19
- file: `liquidator/src/models/instructions/LiquidateObligationAndRedeemReserveCollateral.ts`

Instruction tag:
`0x11`

### Fixed account order

0. source_liquidity
1. destination_collateral
2. destination_reward_liquidity
3. repay_reserve
4. repay_reserve_liquidity_supply
5. withdraw_reserve
6. withdraw_reserve_collateral_mint
7. withdraw_reserve_collateral_supply
8. withdraw_reserve_liquidity_supply
9. withdraw_reserve_fee_receiver
10. obligation
11. lending_market
12. lending_market_authority
13. transfer_authority
14. token_program

Observed first-success instruction contains exactly 15 accounts.

### Instruction args

Native layout:
- byte 0: instruction tag `0x11`
- bytes 1..8: `liquidityAmount: u64`

Observed first-success data length: 9 bytes.

Semantics:
- `liquidityAmount` = requested amount to repay/liquidate;
- NOT frozen as realized collateral or liquidity received.

Classification:

`SAVE11_ACCOUNT_AND_ARGUMENT_DECODER_SOURCE_PASS`

---

## Save / Solend 0x0c

Historical authority already proves:
- archived SDK commit `c93fbc81fcc68610ad64fbce4a170a38335b7d7f`, dated 2021-12-08;
- `LiquidateObligation = 12`.

Transport calibration of the RAW-verified first success shows:
- 12 instruction accounts;
- 9-byte instruction data;
- prefix `0c`;
- committed successful execution.

However the 2021-12-08 pinned SDK snapshot reviewed here exposes the enum tag but does not expose a source builder sufficient to freeze exact account-position semantics and the post-tag argument layout from that commit alone.

Therefore:
- do NOT infer the 8 trailing bytes as a u64 solely from data length;
- do NOT back-apply Save11 account order;
- do NOT use current SDK semantics as historical authority without an explicit pinned lineage proof.

Classification:

`SAVE0C_TAG_AND_TRANSPORT_PASS_ACCOUNT_ARGUMENT_SEMANTICS_PENDING_SOURCE_AUTHORITY`

This is the only unresolved class in this V0.1 field-decoder matrix.

---

## Global status

Source-supported account/argument decoder:
- Kamino: PASS
- Marginfi: PASS for fixed core + dynamic-context rule
- Drift four core classes: PASS
- Save11: PASS
- Save0c: PENDING exact account/argument source authority

Population enrichment transport:
`FIELD_ENRICHMENT_TRANSPORT_8_OF_8_PASS`

Current field-decoder verdict:

`FIELD_DECODER_AUTHORITY_7_OF_8_CLASS_PASS_SAVE0C_PENDING`

No economic Discovery is authorized.
