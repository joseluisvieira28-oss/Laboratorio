# DEFI-LIQUIDATION-SHOCK-001 — FIELD ENRICHMENT POPULATION FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Preconditions

- MARGINFI_SAVE0C_EVENT_CENSUS_SOURCE_PASS
- MARGINFI_SAVE0C_RAW_SAMPLE_RECONCILIATION_PASS 64/64
- FIELD_ENRICHMENT_TRANSPORT_8_OF_8_PASS
- FIELD_ENRICHMENT_CANONICAL_JOIN_3_OF_3_FAMILY_PASS
- FIELD_DECODER_AUTHORITY_8_OF_8_CLASS_PASS
- FIELD_DECODER_IMPLEMENTATION_8_OF_8_PASS
- UNIT_METADATA_SOURCE_FEASIBILITY_PASS

## Population

This V0.1 execution attacks the already frozen realized-event populations for:
- marginfi v2: [2023-02-07T15:47:04Z, 2025-01-01T00:00:00Z)
- Save/Solend 0x0c: [2021-12-08T00:00:00Z, 2025-01-01T00:00:00Z)

Expected final realized-event counts from frozen source authority:
- marginfi: 266,647
- save0c: 66,628

No event may be added, removed, ranked or filtered by enrichment availability.

## Partition rule

Use the same calendar-month scientific intervals as the final source census:
- marginfi: 23 monthly partitions, with the first beginning at 2023-02-07T15:47:04Z;
- save0c: 37 monthly partitions, with the first beginning at 2021-12-08T00:00:00Z.

For Save0c 2022-02 and 2024-10/11/12, canonical baseline identities are taken only from the already accepted sharded recovery evidence. Failed/cancelled monthly transport remnants remain excluded.

## Query rule

Re-query SQD finalized-stream over the exact frozen partition interval using:
- exact frozen program ID;
- programId-only instruction enumeration;
- exact UTC local filtering;
- same success-state semantics as source authority;
- instruction accounts;
- full instruction data;
- existing identity/execution fields.

No token amounts, token balances, decimals, prices or market outcomes are requested.

## Canonical exact join

Key:
`protocol + instruction_class + signature + instructionAddress`

For every partition:
- baseline successful key count;
- enriched successful key count;
- missing keys = 0;
- extra keys = 0;
- duplicate keys = 0;
- identity conflicts = 0;
- source anomalies = 0.

PASS:
`FIELD_ENRICHMENT_PARTITION_PASS`

Any mismatch:
`FIELD_ENRICHMENT_PARTITION_FAIL_CLOSED`

## Semantic mapping

### marginfi
Direct accounts:
- group = account 0
- asset_bank = account 1
- liab_bank = account 2
- liquidator_marginfi_account = account 3
- signer = account 4
- liquidated_marginfi_account = account 5
- liquidity vault authority/vault/insurance vault = accounts 6/7/8
- token program = account 9
- remaining accounts retained as dynamic risk/oracle context

Argument schema:
`asset_quantity: u64`
Numeric value is NOT emitted.

### Save0c
Direct accounts:
- source_liquidity_token_account = 0
- destination_collateral_token_account = 1
- repay_reserve = 2
- repay_reserve_liquidity_supply = 3
- withdraw_reserve = 4
- withdraw_reserve_collateral_supply = 5
- obligation = 6
- lending_market = 7
- derived_lending_market_authority = 8
- user_transfer_authority = 9
- clock_sysvar = 10
- token_program = 11

Argument schema:
`liquidity_amount: u64 little-endian`
Numeric value is NOT emitted.

## Aggregate PASS

Population enrichment PASS requires:
- all 60 frozen partitions PASS;
- summed baseline/enriched counts equal exactly:
  - marginfi 266,647
  - save0c 66,628;
- zero missing, extra, duplicate, conflict or anomaly counts;
- all realized events have non-empty instruction accounts and full instruction data;
- semantic core account positions satisfy their historical decoder minimum account counts.

Terminal classification:
`MARGINFI_SAVE0C_FIELD_ENRICHMENT_POPULATION_PASS`

## Firewall

prices=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
token_balances=false
token_amounts=false
token_decimals=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
