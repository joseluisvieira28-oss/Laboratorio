# DEFI-LIQUIDATION-SHOCK-001 — SAVE0C UNIT METADATA SOURCE COMPLETION CORRECTION V0.3.1

Date: 2026-09-27
Status: FROZEN TECHNICAL/SEMANTIC CORRECTION / SOURCE-ONLY / OUTCOME-BLIND

## Trigger

Historical registry V0.2 closed:
`SAVE0C_HISTORICAL_RESERVE_REGISTRY_PARTIAL_SOURCE_COVERAGE`

with:
- 11 source-proven reserves;
- conflict_count = 0;
- error_count = 0;
- explicit source retirement at 2022-01-10T01:15:03Z.

V0.3 originally required a full historical SOURCE_PASS and therefore cannot correctly consume this bounded partial authority.

## Corrected source precedence

For each exact V0.1 aggregate-listed unmapped reserve/event:

1. historical registry V0.2 may be applied only when the event timestamp is strictly before its frozen coverage_end;
2. calibrated finalized Solana RPC dataslices may be used for any target reserve whose current account is available and passes owner/layout checks;
3. if both historical and RPC metadata exist for the same reserve, compare:
   - underlying mint;
   - underlying decimals;
   - collateral mint.
   Any conflict is FAIL_CLOSED.

Historical metadata after coverage_end cannot be used as sole authority.

## RPC slices

Unchanged:
- offset 42 length 33 -> liquidity mint + liquidity mint decimals
- offset 227 length 32 -> collateral mint
- owner must equal frozen Save/Solend program

No reserve economic amount fields are requested.

## Event reconciliation

For each previously incomplete event:
- choose historical metadata only if temporally applicable;
- otherwise choose calibrated RPC metadata;
- event collateral-token mint must equal recovered collateral mint;
- preserve every canonical event.

## Terminal taxonomy

All 66,628 complete:
`SAVE0C_UNIT_METADATA_POPULATION_PASS`

Some remain unresolved:
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
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
