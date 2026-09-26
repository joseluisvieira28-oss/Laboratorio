# DEFI-LIQUIDATION-SHOCK-001 — KAMINO HISTORICAL ACCOUNT LAYOUT ADDENDUM V0.2

Date: 2026-09-27
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND / HISTORICAL ABI VERSIONING

## Trigger

Population field enrichment partition `kamino-202406` returned:

- baseline_success_count = 3,122
- enriched_success_count = 3,122
- missing_count = 0
- extra_count = 0
- duplicate_count = 0
- baseline_anomaly_count = 0
- semantic_conflict_count = 1,248

The 1,248 conflicts were account-shape conflicts only.

Observed account-count distribution:

- 16 accounts: 1,874
- 20 accounts: 149
- 21 accounts: 985
- 22 accounts: 81
- 23 accounts: 22
- 24 accounts: 8
- 25 accounts: 2
- 26 accounts: 1

All 3,122 instructions retained the frozen 32-byte instruction-data shape.

## Official source lineage

Repository:
`Kamino-Finance/klend`

Instruction:
`liquidate_obligation_and_redeem_reserve_collateral`

### Legacy layout

Official Program v1 commit:
`57074f4599a36ab0b433a71599b206c73efe1fd7`
Date: 2023-11-17.

The Accounts struct contains exactly 16 fixed accounts.

Frozen positions:

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

### Release 1.6.0 layout

Official commit:
`509e98aac6f909cf3e7977e613e503904cf77d00`
Date: 2024-06-19T15:31:40Z
Message: `Release 1.6.0 (#13)`

This source changes the fixed account layout and explicitly passes:

`ctx.remaining_accounts.iter()`

into liquidation processing.

Frozen fixed positions:

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

Accounts at positions >=20 are:
`remaining_accounts`

They are retained verbatim but receive no unsupported fixed semantic role.

Official Release 1.7.0 commit:
`c02bcf7dfe932af27d429df4111b3a3ca05a0dd3`
Date: 2024-08-19.
It preserves the same 20 fixed account layout.

No further commit touching this liquidation handler was found before 2025-01-01.

## On-chain population transition evidence

Within the frozen June-2024 realized population:

Last observed successful legacy-layout event:
- UTC: 2024-06-18T19:56:29Z
- slot: 272635400
- signature: 5ERAADUmx7KzK1dYdVkkRNvZzLAz82p5WLeKrm5L95wfW6TU7etV6rHffcoXfGiXW4yu2HFZbQPkddowHhwtaYE
- instructionAddress: [8]
- account_count: 16

First observed successful Release-1.6-style event:
- UTC: 2024-06-19T19:15:17Z
- slot: 272824392
- signature: 2EEbTu6qrA6rofxGeTiYKs8XDdmp911S3k8UGa9KVVdk64ouNsFaRnJFx2NaJFtS7zw1moEufBhjNgUPfnDMjSzD
- instructionAddress: [9]
- account_count: 21

Across all 1,248 observed Release-1.6-style June events:
- account_count is 20..26;
- account[16], account[17], account[18] are the SPL Token program in every observed event;
- account[19] is Instructions Sysvar in every observed event;
- account[20:] has length 0..6 and is retained as dynamic remaining_accounts.

Across all 1,874 observed legacy June events:
- account_count == 16;
- account[14] is SPL Token program;
- account[15] is Instructions Sysvar.

## Decoder selection rule

Do NOT infer an exact deployment timestamp from source commit time alone.

Select historical account decoder from the instruction's own source-observed shape:

### KAMINO_LAYOUT_LEGACY_16
Required:
- account_count == 16
- account[14] == SPL Token program
- account[15] == Instructions Sysvar
- instruction data length == 32 bytes

### KAMINO_LAYOUT_V1_6_PLUS
Required:
- account_count >= 20
- account[19] == Instructions Sysvar
- token-program positions 16..18 are source-valid token program accounts
- instruction data length == 32 bytes
- accounts[20:] retained as dynamic_remaining_accounts

Account counts 17, 18 or 19:
`KAMINO_ACCOUNT_LAYOUT_UNSUPPORTED_FAIL_CLOSED`

Any event failing its selected layout:
`FIELD_SOURCE_CONFLICT_FAIL_CLOSED`

## Unit-metadata role correction

Legacy token-unit pair positions remain:

- debt_underlying: [5, 11]
- collateral_token: [8, 12]
- collateral_underlying: [9, 13]

Release 1.6+ token-unit pair positions become:

- debt_underlying: [6, 13]
- collateral_token: [10, 14]
- collateral_underlying: [11, 15]

The new direct mint accounts at positions 5 and 8 may be retained for reconciliation but do not replace the frozen token-balance pair authority in V0.2.

## Argument schema versioning

Both layouts retain 32 bytes:
- 8-byte discriminator
- three u64 arguments

Legacy source names the second u64:
`min_acceptable_received_collateral_amount`

Release 1.6+ source names it:
`min_acceptable_received_liquidity_amount`

Neither name/value is treated as realized economic flow.

## Recovery rule

The original failing receipt remains immutable audit history.

Authoritative population enrichment may use a V0.2 recovery receipt for Kamino intervals containing Release-1.6+ events only when:
- exact canonical event set equals frozen census;
- decoder selection follows this addendum;
- missing=extra=duplicate=0;
- unsupported layout count=0;
- core semantic positions validate;
- unit metadata uses layout-specific frozen pair positions.

No source event is added or removed.

## Firewall

prices=false
returns=false
pnl=false
direction=false
economic_outcomes=false
requested_amount_values=false
realized_amounts=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
post_outcome_tuning=false
merge_main=false
