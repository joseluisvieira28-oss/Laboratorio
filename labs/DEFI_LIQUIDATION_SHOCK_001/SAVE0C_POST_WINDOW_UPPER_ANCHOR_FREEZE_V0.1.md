# DEFI-LIQUIDATION-SHOCK-001 — SAVE 0x0c POST-WINDOW UPPER ANCHOR FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND

Purpose: find one Save/Solend program transaction at or after `2025-01-01T00:00:00Z` solely as an exclusive upper cursor for the frozen 2021-2024 first-success walk of native tag `0x0c`.

Program: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`
Frozen scientific window end exclusive: `2025-01-01T00:00:00Z`
First-success lower boundary later used by the separate resolver: `2021-12-08T00:00:00Z`

The anchor is not a liquidation candidate and its 2025 transaction content is not inspected for economic or liquidation outcomes. Only signature, slot, blockTime, status and raw block hash may be persisted.

Transport: official public Solana RPC only.
Classification: PASS if one program transaction is found at/after the target; otherwise BLOCKED / fail-closed anomaly as applicable.

Firewall: prices=false; returns=false; pnl=false; direction=false; economic_outcomes=false; protected_2025_2026_market_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; merge_main=false.
