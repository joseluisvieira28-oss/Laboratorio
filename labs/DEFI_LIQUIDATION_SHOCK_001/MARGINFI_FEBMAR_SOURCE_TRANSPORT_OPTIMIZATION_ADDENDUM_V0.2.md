# DLS — MARGINFI FEB-MAR SOURCE TRANSPORT OPTIMIZATION ADDENDUM V0.2

Date: 2026-09-29
Branch: dls-marginfi-transient-reversion-v01
Status: FROZEN OPERATIONAL ADDENDUM / NO SCIENTIFIC CHANGE

Parent:
MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_TEMPORAL_SOURCE_EXTENSION_FREEZE_V0.1.md

## Reason

The V0.1 transport streams both Marginfi and all Jupiter instructions continuously across each five-day
shard. This is scientifically valid but operationally expensive because unrelated Jupiter traffic dominates.

V0.2 changes transport only.

No source result from the Feb-Mar period is used to define this correction.

## Canonical population unchanged

For each frozen shard, first stream ONLY successful committed Marginfi
lending_account_liquidate instructions matching:
- program MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA
- discriminator d6a997d5fba756db
- exact frozen timestamp interval.

Preserve the same account roles and exact identity.

This first pass defines the identical canonical population that V0.1 would recover.

## Exact-slot Jupiter recovery

For each canonical Marginfi population row:
- query only the exact Solana slot of that row;
- recover the exact successful parent transaction;
- recover committed successful Jupiter V6 instructions from that exact transaction;
- apply the unchanged post-liquidation route membership rule;
- apply the unchanged V0.2 multi-hop SwapEvent decoder and direction rule.

No neighboring slots or later wallet activity are used.

## Population and direction gates unchanged

All shard intervals, source-completeness threshold, direction threshold, contradiction rule and global
PASS/PARTIAL/BLOCKED classifications remain exactly as frozen in V0.1.

## Cross-transport reconciliation

If both V0.1 and V0.2 complete, they must reconcile on:
- canonical Marginfi population identity set;
- Jupiter route member identity set;
- direction classifications.

Any mismatch is SOURCE_BLOCKED pending source reconciliation.

A V0.2 PASS may be used if V0.1 remains operationally unfinished, because V0.2 independently covers the
same frozen population with stricter exact-slot retrieval.

## Firewall

prices=false
returns=false
pnl=false
market_outcomes_feb_mar_2024=false
jan_2024_reused_for_reversion_validation=false
apr_jun_2024_holdout_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
