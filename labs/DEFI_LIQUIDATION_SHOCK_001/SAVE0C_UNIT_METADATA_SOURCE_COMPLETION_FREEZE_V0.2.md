# DEFI-LIQUIDATION-SHOCK-001 — SAVE0C UNIT METADATA SOURCE COMPLETION FREEZE V0.2

Date: 2026-09-26
Status: FROZEN CONDITIONAL SOURCE-ONLY REMEDIATION / OUTCOME-BLIND

## Trigger

This remediation may launch only if V0.1 population adjudication returns exactly:

`SAVE0C_UNIT_METADATA_PARTIAL_SOURCE_COVERAGE`

with:
- canonical event join complete;
- direct debt/collateral-token metadata complete;
- zero query/source conflicts;
- one or more explicit unmapped withdraw reserves.

It MUST NOT launch for `SAVE0C_UNIT_METADATA_BLOCKED_FAIL_CLOSED`.

## Calibrated source route

Prerequisite:
`SAVE_RESERVE_METADATA_DATASLICE_3_OF_3_PASS`

Official Solana RPC finalized account data slices for Save/Solend Reserve state:

- offset 42, length 33:
  - bytes 0..31 = liquidity mint Pubkey
  - byte 32 = liquidity mint decimals
- offset 227, length 32:
  - collateral mint Pubkey

Only these slices may be requested.

Do NOT request or decode:
- reserve liquidity available amount;
- borrowed amount;
- cumulative borrow rate;
- market price;
- token balances/amounts;
- any economic state.

## Conditional target population

Targets are ONLY the exact `unmapped_reserves` emitted by
`SAVE0C_UNIT_METADATA_POPULATION_RECEIPT_V0.1.json`.

No other reserve may be added based on convenience or market outcomes.

## Reserve metadata PASS

For each target reserve:
- current account exists;
- owner == frozen Save/Solend program;
- slice lengths exact 33 and 32 bytes;
- liquidity mint non-empty;
- liquidity decimals is a byte value;
- collateral mint non-empty.

If a reserve no longer exists or owner/layout conflicts:
`SAVE0C_RESERVE_METADATA_SOURCE_COMPLETION_PENDING`
for that reserve; do not guess historical metadata.

## Event-level reconciliation

Using the already frozen V0.1 partition receipts:
- for every event whose withdraw_reserve was previously unmapped,
- observed collateral-token mint must equal the recovered reserve collateral mint;
- attach recovered collateral-underlying liquidity mint+decimals;
- no event is added or removed.

Terminal PASS only if all 66,628 events become unit-complete:

`SAVE0C_UNIT_METADATA_POPULATION_PASS`

Any mint/layout/source contradiction:
`SAVE0C_UNIT_METADATA_BLOCKED_FAIL_CLOSED`

## Firewall

prices=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
reserve_amounts=false
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
