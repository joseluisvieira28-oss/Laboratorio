# DLS — MARGINFI JUPITER ROUTE CLASS TRANSPORT SHARDING ADDENDUM V0.2

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01
Status: FROZEN OPERATIONAL CORRECTION BEFORE SHARDED RERUN
Parent: MARGINFI_JUPITER_POST_LIQUIDATION_ROUTE_CLASS_FREEZE_V0.1.md

## Reason

Canonical run 36532597421 was cancelled at the workflow timeout after roughly 70 minutes.

No receipt or class-membership artifact was produced.
No token balance, amount, price, return, PnL or market direction was opened.

This addendum changes transport only. It does not change the scientific population or class definition.

## Scientific invariants unchanged

Global validation population remains exactly:
- canonical field-enrichment run 36263998920
- artifact dls-field-enrichment-ms-marginfi-202401
- artifact ID 10918871581
- interval [2024-01-01T00:00:00Z, 2024-02-01T00:00:00Z)
- canonical lending_account_liquidate population = 10,381

Class membership remains exactly:
1. canonical successful Marginfi lending_account_liquidate;
2. exact signature + instructionAddress recovered;
3. successful parent transaction;
4. same transaction contains committed Jupiter V6;
5. Jupiter instructionAddress sorts strictly after the canonical Marginfi liquidation instructionAddress.

## Frozen transport shards

Assign canonical events by canonical event timestamp to exactly one half-open interval:

- mfi-01: [2024-01-01T00:00:00Z, 2024-01-05T00:00:00Z)
- mfi-02: [2024-01-05T00:00:00Z, 2024-01-09T00:00:00Z)
- mfi-03: [2024-01-09T00:00:00Z, 2024-01-13T00:00:00Z)
- mfi-04: [2024-01-13T00:00:00Z, 2024-01-17T00:00:00Z)
- mfi-05: [2024-01-17T00:00:00Z, 2024-01-21T00:00:00Z)
- mfi-06: [2024-01-21T00:00:00Z, 2024-01-25T00:00:00Z)
- mfi-07: [2024-01-25T00:00:00Z, 2024-01-29T00:00:00Z)
- mfi-08: [2024-01-29T00:00:00Z, 2024-02-01T00:00:00Z)

No event may move shards based on Jupiter presence or any later outcome.

## Shard PASS

Each shard must:
- recover every canonical event assigned to its interval;
- have missing_count = 0;
- extra_count = 0;
- anomaly_count = 0;
- source transport complete.

Shard membership count may be zero without invalidating the shard.

## Global merge PASS

MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_PASS only if:
- all 8 shard receipts PASS;
- union canonical count = 10,381;
- union recovered count = 10,381;
- duplicate canonical identity count = 0;
- global missing/extra/anomaly count = 0;
- global class member count > 0.

Otherwise fail closed.

## Firewall

token_balances=false
token_amounts=false
prices=false
returns=false
pnl=false
market_direction=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_class_change=false
