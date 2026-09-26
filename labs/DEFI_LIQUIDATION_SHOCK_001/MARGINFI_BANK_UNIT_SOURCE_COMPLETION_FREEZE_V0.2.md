# DEFI-LIQUIDATION-SHOCK-001 — MARGINFI BANK UNIT SOURCE COMPLETION FREEZE V0.2

Date: 2026-09-26
Status: FROZEN CONDITIONAL SOURCE-ONLY REMEDIATION / OUTCOME-BLIND

## Trigger

This remediation may launch only if:
1. `MARGINFI_BANK_METADATA_DATASLICE_CALIBRATION_PASS`; and
2. V0.1 registry aggregate returns exactly:
   `MARGINFI_BANK_UNIT_REGISTRY_PARTIAL_SOURCE_COVERAGE`.

It MUST NOT launch if V0.1 returns `MARGINFI_BANK_UNIT_REGISTRY_BLOCKED_FAIL_CLOSED`.

## Calibrated route

Pinned historical Bank layout:
`0dotxyz/marginfi-v2@f6d3d5616e293c9468333571c3ceb90bb2410b00`

Minimal finalized account slice:
- offset 8
- length 33
- bytes 0..31 = Bank.mint
- byte 32 = Bank.mint_decimals

Only the exact `unmapped_asset_banks` listed by the V0.1 aggregate may be queried.

## PASS rule per target bank

- account exists;
- owner == frozen Marginfi program;
- returned slice length == 33;
- mint decodes to a non-empty Pubkey;
- decimals is one byte.

No other Bank fields may be requested or decoded.

## Registry reconciliation

Merge recovered target mappings with the already source-authoritative liability-bank registry.

Terminal PASS only if:
- every asset_bank and liab_bank observed in the frozen 266,647-event population maps to exactly one mint+decimals pair;
- no bank has conflicting pairs;
- no bank remains unmapped;
- event population is unchanged.

PASS:
`MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS`

Missing/deleted account:
`MARGINFI_BANK_UNIT_REGISTRY_PARTIAL_SOURCE_COVERAGE`

Owner/layout/mint conflict:
`MARGINFI_BANK_UNIT_REGISTRY_BLOCKED_FAIL_CLOSED`

## Firewall

prices=false
oracle_values=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
bank_balances=false
share_values=false
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
