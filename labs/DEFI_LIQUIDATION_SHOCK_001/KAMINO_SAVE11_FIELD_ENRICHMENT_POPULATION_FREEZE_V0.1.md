# DEFI-LIQUIDATION-SHOCK-001 — KAMINO SAVE11 FIELD ENRICHMENT POPULATION FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Preconditions

- KAMINO_SAVE11_EVENT_CENSUS_SOURCE_PASS
- KAMINO_SAVE11_V043_AUTHORITY_AUDIT_PASS
- RAW sample reconciliation 64/64 PASS
- FIELD_ENRICHMENT_TRANSPORT_8_OF_8_PASS
- FIELD_ENRICHMENT_CANONICAL_JOIN_3_OF_3_FAMILY_PASS
- FIELD_DECODER_AUTHORITY_8_OF_8_CLASS_PASS
- FIELD_DECODER_IMPLEMENTATION_8_OF_8_PASS
- UNIT_METADATA_SOURCE_FEASIBILITY_PASS

## Population

Frozen realized-event populations:
- Kamino Lend: [2023-11-17T14:48:24Z, 2025-01-01T00:00:00Z)
- Save/Solend 0x11: [2024-07-19T19:30:52Z, 2025-01-01T00:00:00Z)

Expected realized-event totals:
- Kamino: 60,699
- Save11: 13,300

No event may be added, removed, ranked or filtered by enrichment availability.

## Partition rule

Use the accepted monthly source artifacts from authoritative run 35958824070:
- Kamino: k202311 through k202412 = 14 partitions
- Save11: s202407 through s202412 = 6 partitions

The first partition of each protocol starts at its frozen first-success boundary.

## Query rule

Re-query SQD finalized-stream over the exact frozen partition interval using:
- exact frozen program ID;
- programId-only instruction enumeration with local exact prefix decoding;
- exact UTC local filtering;
- same success-state semantics;
- instruction accounts;
- full instruction data;
- existing identity/execution fields.

Do not request token amounts, balances, decimals, prices or market outcomes.

## Canonical exact join

Key:
`protocol + instruction_class + signature + instructionAddress`

Per partition PASS requires:
- missing=0
- extra=0
- duplicate=0
- identity conflict=0
- source anomaly=0
- non-empty accounts and full instruction data for every realized event

## Semantic mapping

### Kamino
Exact 16 accounts:
0 liquidator
1 obligation
2 lending_market
3 lending_market_authority
4 repay_reserve
5 repay_reserve_liquidity_supply
6 withdraw_reserve
7 withdraw_reserve_collateral_mint
8 withdraw_reserve_collateral_supply
9 withdraw_reserve_liquidity_supply
10 withdraw_reserve_liquidity_fee_receiver
11 user_source_liquidity
12 user_destination_collateral
13 user_destination_liquidity
14 token_program
15 instruction_sysvar_account

Argument schema:
- liquidity_amount:u64
- min_acceptable_received_collateral_amount:u64
- max_allowed_ltv_override_percent:u64

Numeric values are not emitted.

### Save11
Exact 15 accounts:
0 source_liquidity
1 destination_collateral
2 destination_reward_liquidity
3 repay_reserve
4 repay_reserve_liquidity_supply
5 withdraw_reserve
6 withdraw_reserve_collateral_mint
7 withdraw_reserve_collateral_supply
8 withdraw_reserve_liquidity_supply
9 withdraw_reserve_fee_receiver
10 obligation
11 lending_market
12 lending_market_authority
13 transfer_authority
14 token_program

Argument schema:
- liquidityAmount:u64

Numeric value is not emitted.

## Aggregate PASS

All 20 partitions must PASS and totals must equal exactly:
- Kamino 60,699
- Save11 13,300

Terminal:
`KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_PASS`

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
