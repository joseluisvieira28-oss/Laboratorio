# DEFI-LIQUIDATION-SHOCK-001 — KAMINO + SAVE11 HISTORICAL FIELD AUTHORITY FREEZE V0.1

Date: 2026-09-23  
Status: SOURCE-ONLY / OUTCOME-BLIND / FIELD-AUTHORITY PARTIAL / FAIL-CLOSED

Purpose: freeze historical instruction-field reconstruction rules before opening census counts/outcomes.

This document does NOT alter event identity, census inclusion, success semantics, date windows or the already-frozen RAW sample.

## Kamino V1 — discriminator `b1479abce2854a37`

Official source: `Kamino-Finance/klend`.

### Layout A — source-supported from 2023-11-17

Commit:
`57074f4599a36ab0b433a71599b206c73efe1fd7`

Instruction args:
1. `liquidity_amount: u64`
2. `min_acceptable_received_collateral_amount: u64`
3. `max_allowed_ltv_override_percent: u64`

Accounts, in Anchor order:
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

The same account-field list and process signature were checked at:
- `550fc235d3e68cde112f654a84523aff709dd8f6` — 2024-03-21
- `29d0aedc8a2cab11379df897ebdad2e819f377da` — 2024-05-07

### Layout B — source-supported by 2024-06-19

Commit:
`509e98aac6f909cf3e7977e613e503904cf77d00`

Instruction args remain three u64 values but the second source name becomes:
`min_acceptable_received_liquidity_amount`.

Accounts become 20 entries:
0. liquidator
1. obligation
2. lending_market
3. lending_market_authority
4. repay_reserve
5. repay_reserve_liquidity_mint
6. repay_reserve_liquidity_supply
7. withdraw_reserve
8. withdraw_reserve_liquidity_mint
9. withdraw_reserve_collateral_mint
10. withdraw_reserve_collateral_supply
11. withdraw_reserve_liquidity_supply
12. withdraw_reserve_liquidity_fee_receiver
13. user_source_liquidity
14. user_destination_collateral
15. user_destination_liquidity
16. collateral_token_program
17. repay_liquidity_token_program
18. withdraw_liquidity_token_program
19. instruction_sysvar_account

The 20-account field list and three-u64 process signature were checked again at:
`c02bcf7dfe932af27d429df4111b3a3ca05a0dd3` — 2024-08-19.

### Kamino field decoder rule

Do NOT infer account positions from timestamp alone.

For each RAW instruction:
- discriminator must first equal the frozen V1 discriminator;
- account-vector shape must be reconciled against the historically supported layouts;
- 16-account shape may use Layout A names;
- 20-account shape may use Layout B names;
- any other shape is `KAMINO_FIELD_LAYOUT_UNRESOLVED_FAIL_CLOSED`;
- the three u64 argument bytes may be preserved losslessly, but the second argument semantic label must follow the reconciled historical layout;
- no token/USD valuation is authorized.

The exact on-chain deployment transition between source commits is not inferred from commit timestamps. Structural account shape is the primary per-event layout discriminator.

## Save / Solend 0x11

Program:
`So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`

Instruction tag:
`0x11`.

Official repo:
`solendprotocol/public`.

### Identity authority

Commit `91d2936930b412ce752be71c6d166deba65489cc`, dated 2024-07-19T17:54:33Z, adds:
`LiquidateObligationAndRedeemReserveCollateral = 17`.

The exact first successful on-chain call is already RAW-verified at:
2024-07-19T19:30:52Z, slot 278496102.

### Field-layout authority

The public SDK constructor file
`solend-sdk/src/instructions/liquidateObligationAndRedeemReserveCollateral.ts`
is first present in repository history at commit:
`d01b24d70b24638bc8544a34e3c244918f797122`,
dated 2024-08-06T11:54:18Z.

It documents:
- instruction byte `0x11`;
- one `u64 liquidityAmount`;
- 15 accounts:
  0 sourceLiquidity
  1 destinationCollateral
  2 destinationRewardLiquidity
  3 repayReserve
  4 repayReserveLiquiditySupply
  5 withdrawReserve
  6 withdrawReserveCollateralMint
  7 withdrawReserveCollateralSupply
  8 withdrawReserveLiquiditySupply
  9 withdrawReserveFeeReceiver
  10 obligation
  11 lendingMarket
  12 lendingMarketAuthority
  13 transferAuthority (signer)
  14 tokenProgram

The same constructor is present at 2024-09-09.

### Save11 field decoder rule

For event identity, tag `0x11` remains authoritative from the already-closed first-success boundary.

For account/argument semantic enrichment:
- do NOT silently back-apply the 2024-08-06 constructor to 2024-07-19 through 2024-08-05;
- events before source-layout support remain `SAVE11_FIELD_LAYOUT_PENDING_RAW_RECONCILIATION` unless RAW structure is independently reconciled;
- events at/after the supported constructor state may use the documented 15-account/u64 layout only after RAW account-vector shape is consistent;
- any unexpected shape is fail-closed.

## Firewall

This is source-field reconstruction only.

Forbidden:
prices; USD notional; returns; PnL; direction; future outcomes; protocol selection by performance; trading; orders; wallets; exchange mutation; paid sources; account creation; main merge.

No edge or promotion inference is authorized.
