# DEFI-LIQUIDATION-SHOCK-001 — KAMINO SAVE11 UNIT METADATA POPULATION FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Preconditions

- KAMINO_SAVE11_EVENT_CENSUS_SOURCE_PASS
- KAMINO_SAVE11_V043_AUTHORITY_AUDIT_PASS
- FIELD_DECODER_AUTHORITY_8_OF_8_CLASS_PASS
- LENDING_TOKEN_UNIT_METADATA_12_OF_12_ACCOUNT_PASS
- INSTRUCTION_TOKEN_BALANCE_RELATION_3_OF_3_REFERENCE_PASS

## Population

Exact frozen realized populations:
- Kamino: 60,699
- Save11: 13,300
- total: 73,999

Canonical key:
`protocol + instruction_class + signature + instructionAddress`

No event may be added, removed, ranked or filtered by metadata availability.

## Query route

Re-query exact accepted monthly intervals with:
- exact program;
- exact d8/d1 discriminator;
- isCommitted=true;
- transaction=true;
- transactionTokenBalances=true;
- instruction accounts/data/identity;
- tokenBalance fields ONLY:
  - account
  - preMint
  - postMint
  - preDecimals
  - postDecimals

Forbidden:
- preAmount
- postAmount
- prices
- USD notional
- returns / PnL

## Kamino event unit identities

Historical account roles:
- debt underlying: account 5 repay_reserve_liquidity_supply and account 11 user_source_liquidity
- collateral token: account 8 withdraw_reserve_collateral_supply and account 12 user_destination_collateral
- collateral underlying: account 9 withdraw_reserve_liquidity_supply and account 13 user_destination_liquidity

Per event require:
- both debt accounts resolve to exactly one identical mint+decimals pair;
- both collateral-token accounts resolve to exactly one identical mint+decimals pair;
- both collateral-underlying accounts resolve to exactly one identical mint+decimals pair.

## Save11 event unit identities

Historical account roles:
- debt underlying: account 0 source_liquidity and account 4 repay_reserve_liquidity_supply
- collateral token: account 1 destination_collateral and account 7 withdraw_reserve_collateral_supply
- collateral underlying: account 2 destination liquidity and account 8 withdraw_reserve_liquidity_supply

Apply the same exact pair-consistency rule.

## Partition PASS

Each monthly partition requires:
- canonical missing=0
- canonical extra=0
- duplicates=0
- source anomalies=0
- unit metadata conflicts=0
- every realized event has all 3 unit identities

Classification:
`KAMINO_SAVE11_UNIT_METADATA_PARTITION_PASS`

## Aggregate PASS

All 20 accepted monthly partitions must PASS.
Totals must equal exactly:
- Kamino 60,699 / 60,699 unit-complete
- Save11 13,300 / 13,300 unit-complete

Terminal:
`KAMINO_SAVE11_UNIT_METADATA_POPULATION_PASS`

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
