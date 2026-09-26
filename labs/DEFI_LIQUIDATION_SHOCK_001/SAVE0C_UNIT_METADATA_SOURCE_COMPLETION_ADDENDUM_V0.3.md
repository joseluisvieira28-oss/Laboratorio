# DEFI-LIQUIDATION-SHOCK-001 — SAVE0C UNIT METADATA SOURCE COMPLETION ADDENDUM V0.3

Date: 2026-09-26
Status: FROZEN CONDITIONAL SOURCE-ONLY REMEDIATION / OUTCOME-BLIND

## Trigger

V0.3 may launch only if the V0.1 population aggregate is exactly:

`SAVE0C_UNIT_METADATA_PARTIAL_SOURCE_COVERAGE`

with canonical join/direct unit metadata complete and zero source/query conflicts.

It MUST NOT launch for a BLOCKED result.

## Source order

For each exact aggregate-listed `unmapped_reserve` only:

1. historical official SDK registry, if
   `SAVE0C_HISTORICAL_RESERVE_REGISTRY_SOURCE_PASS`;
2. calibrated finalized Solana RPC reserve dataslices only when the reserve is absent from the historical registry.

No other reserves may be queried or added.

## Historical registry route

Source:
`solendprotocol/solend-sdk/src/configs/production.json`
history over 2021-12-08 through 2024-12-31.

For a target reserve, require a single frozen registry identity:
- underlying_mint;
- underlying_decimals;
- collateral_mint.

## RPC fallback route

Only for target reserves absent from the historical registry:

- offset 42, length 33:
  - liquidity mint Pubkey
  - liquidity mint decimals
- offset 227, length 32:
  - collateral mint Pubkey

Require owner == frozen Save/Solend program.

No other reserve-state bytes may be requested.

## Event reconciliation

For every previously incomplete frozen event:
- select recovered metadata for its withdraw_reserve;
- observed event collateral-token mint MUST equal recovered collateral_mint;
- attach collateral-underlying mint+decimals;
- do not add/drop any event.

If historical and RPC sources are both available for a reserve through independent diagnostics, they may be compared, but a conflict fails closed.

## Terminal taxonomy

All 66,628 frozen events complete:
`SAVE0C_UNIT_METADATA_POPULATION_PASS`

Some target reserves remain source-unresolved:
`SAVE0C_UNIT_METADATA_PARTIAL_SOURCE_COVERAGE`

Any source/layout/mint contradiction:
`SAVE0C_UNIT_METADATA_BLOCKED_FAIL_CLOSED`

## Firewall

prices=false
oracle_values=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
reserve_amounts=false
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
