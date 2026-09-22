# DEFI-LIQUIDATION-SHOCK-001 — SAVE + MARGINFI UPPER ANCHOR PROBE FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Find one deterministic successful or failed transaction signature for each target program strictly at or after 2024-12-16T00:00:00Z, using only the official public Solana RPC. These signatures are cursor anchors only. They are not liquidation candidates and do not establish any scientific event.

Target programs:
- Save/Solend: So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo
- marginfi v2: MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA

The date is intentionally after the already-validated 2024-12-15 liquidation sample day. Therefore any anchor on or after 2024-12-16 is a valid upper cursor for historical first-success walks that seek events at or before 2024-12-15.

## Fixed transport

RPC: https://api.mainnet-beta.solana.com

A known Solana reference point is used only to estimate the target slot:
- slot 307588986
- blockTime 2024-12-15T07:32:56Z

The probe must:
1. converge to a produced slot with blockTime >= 2024-12-16T00:00:00Z;
2. scan forward through produced blocks;
3. inspect only transaction account keys/program IDs;
4. stop after one transaction for each target program;
5. persist signature, slot, blockTime, transaction status and RAW block-response hash;
6. fail closed if 5,000 produced blocks are scanned without both anchors.

## Classification

- both anchors found: SAVE_MARGINFI_UPPER_ANCHOR_PASS
- only one found: SAVE_MARGINFI_UPPER_ANCHOR_PARTIAL
- none / transport exhausted: SAVE_MARGINFI_UPPER_ANCHOR_BLOCKED
- malformed or chronology inconsistency: SAVE_MARGINFI_UPPER_ANCHOR_SOURCE_ANOMALY_FAIL_CLOSED

## Firewall

prices=false; returns=false; pnl=false; direction=false; economic_outcomes=false; 2025_2026_market_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; account_creation=false; merge_main=false.
