# DEFI-LIQUIDATION-SHOCK-001 — SOLARCHIVE SOURCE RECON CLOSEOUT V0.1

Date: 2026-09-22
Status: **SOURCE_BLOCKED_CURRENT_COVERAGE**

## Executed probe

GitHub Actions run: 35698535534

Frozen source-only probe attempted:
- transaction schema;
- transaction partition index for 2024-12-15.

Observed result:
- HTTP 404 on the frozen 2024 transaction route;
- machine classification in the original receipt: SOLARCHIVE_SOURCE_RECON_BLOCKED.

## Current official coverage adjudication

The current SolArchive public coverage page states that transaction history is not presently published for 2024. The 2024 monthly rows expose Accounts and Tokens, but no Transactions. Current transaction publication is visible for selected earlier periods and 2025-11/12, while the project roadmap states historical transaction backfill is still in progress.

Therefore the 2024-12-15 DLS transaction partition cannot be repaired by changing path syntax. The required transaction dataset is currently absent for the frozen period.

Classification:
SOURCE_BLOCKED_CURRENT_COVERAGE

This is not:
- SOURCE_DATA_PASS;
- NO_EDGE;
- a liquidation-census failure;
- permission to substitute Accounts/Tokens snapshots;
- permission to change the frozen period.

## Reopening trigger

Reopen only if SolArchive publishes Transactions for the frozen 2021-2024 DLS period with discoverable partition indexes and raw fields sufficient for program/instruction/log provenance.

## Firewalls

source_data_pass=false
prices=false
returns=false
pnl=false
direction=false
market_response=false
liquidation_events_decoded=false
first_success_boundary_adjudicated=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
main_merge=false
