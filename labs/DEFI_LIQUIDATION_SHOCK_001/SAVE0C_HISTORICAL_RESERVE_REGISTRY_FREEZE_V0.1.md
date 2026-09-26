# DEFI-LIQUIDATION-SHOCK-001 — SAVE0C HISTORICAL RESERVE REGISTRY FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Build a historical source registry for Save/Solend reserves that may appear in the frozen Save0c liquidation population but are absent from the single 2021 production snapshot.

This is a metadata-source attack only. No price/oracle values, balances, token amounts, returns or PnL are accessed.

## Source authority

Repository:
`solendprotocol/solend-sdk`

File:
`src/configs/production.json`

Frozen history interval:
`2021-12-08T00:00:00Z <= commit_date < 2025-01-01T00:00:00Z`

Pinned initial authority:
`c93fbc81fcc68610ad64fbce4a170a38335b7d7f`

Program:
`So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`

## Extraction rule

For every authenticated commit touching `production.json` in the frozen interval:

1. read only:
   - top-level `programID`;
   - `assets[].symbol`;
   - `assets[].decimals`;
   - `assets[].mintAddress`;
   - `markets[].address`;
   - `markets[].reserves[].asset`;
   - `markets[].reserves[].address`;
   - `markets[].reserves[].collateralMintAddress`.
2. ignore the entire `oracles` object and any pricing/feed fields;
3. join each reserve's `asset` symbol to exactly one asset mint+decimals entry in the same snapshot;
4. emit:
   `reserve -> underlying_mint + underlying_decimals + collateral_mint`
   plus source commit/date and market address.

## Conflict rule

For a given reserve address:

- identical unit identity across snapshots is consistent;
- appearance/disappearance across snapshots is allowed;
- any change in underlying mint, underlying decimals or collateral mint is a source conflict and fails closed.

No reserve mapping may be inferred from symbol alone across different snapshots.

## Registry PASS

PASS requires:
- all snapshots parse;
- every extracted reserve joins to exactly one same-snapshot asset unit identity;
- zero reserve unit conflicts.

Classification:
`SAVE0C_HISTORICAL_RESERVE_REGISTRY_SOURCE_PASS`

Otherwise:
`SAVE0C_HISTORICAL_RESERVE_REGISTRY_BLOCKED_FAIL_CLOSED`

## Use in population completion

This registry may be used only after the frozen Save0c unit aggregate identifies the exact set of unmapped reserves.

For each aggregate-listed unmapped reserve:
- if present in this registry with a single unit identity, use it as source authority;
- observed event collateral-token mint must equal the registry collateral mint;
- otherwise continue to the calibrated on-chain reserve dataslice route or remain partial.

The event population must never change.

## Firewall

prices=false
oracle_values=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
balances=false
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
