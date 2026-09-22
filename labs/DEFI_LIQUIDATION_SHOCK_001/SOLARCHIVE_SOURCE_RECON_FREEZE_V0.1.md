# DEFI-LIQUIDATION-SHOCK-001 — SOLARCHIVE SOURCE RECON FREEZE V0.1

Date: 2026-09-22
Status: SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose

Evaluate SolArchive as a free/no-auth historical transaction transport candidate for the frozen DLS source gate.

SolArchive publicly states:
- no API keys or rate limits;
- Solana transaction history in Parquet;
- daily transaction partitions;
- index files for discovery/integrity;
- data sourced from Solana Foundation BigQuery exports.

This probe does NOT adopt SolArchive as authority.

## Frozen probe

Only:
1. GET transaction schema JSON.
2. GET transaction day index for 2024-12-15.
3. Record field names/types, file count, aggregate compressed bytes when available, and index metadata.
4. Do NOT download Parquet transaction bodies in V0.1.
5. Do NOT decode liquidation instructions.

URLs:
- https://data.solarchive.org/schemas/solana/transactions.json
- https://data.solarchive.org/txs/2024-12-15/index.json

## Required feasibility questions

- Is the frozen date present?
- Are immutable file URLs discoverable?
- Are file sizes/checksums or equivalent integrity metadata present?
- Does the transaction schema preserve enough raw structure to potentially identify program participation and instruction/log content?

A schema/index PASS does NOT prove discriminator filtering or census feasibility.

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
merge_main=false
