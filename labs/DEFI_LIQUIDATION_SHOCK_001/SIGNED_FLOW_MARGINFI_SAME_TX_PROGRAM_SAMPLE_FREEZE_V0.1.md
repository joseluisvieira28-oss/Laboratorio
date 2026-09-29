# DLS — SIGNED FLOW MARGINFI SAME-TX PROGRAM SAMPLE FREEZE V0.1

Date: 2026-09-29
Status: FROZEN SOURCE-ONLY SAMPLE / NO MARKET OUTCOMES
Branch: dls-signed-flow-authority-v01

## Population source

Canonical Marginfi field-enrichment partition:
- run 36263998920
- artifact dls-field-enrichment-ms-marginfi-202312
- artifact ID 10918650346
- digest sha256:702dc416a7b030900820189366a07126b8e0c80f5d5675c442a46978fbbcb242
- classification FIELD_ENRICHMENT_PARTITION_PASS
- class lending_account_liquidate
- December 2023

## Deterministic sample

Rank every canonical enriched row by ascending SHA256 of:

signature || "|" || JSON-canonical instructionAddress

Select first 64 events.

No event is selected from amount, token identity, price, return, later wallet behavior or transaction composition.

## Exact transaction census

For each sample event:
- query the exact finalized slot;
- recover the exact successful parent transaction by canonical signature;
- retain only instructions with that transactionIndex;
- bind the canonical Marginfi liquidation by exact program ID + instructionAddress;
- report ordered program IDs before/at/after the canonical liquidation.

Program identity is not interpreted as DEX/swap unless separately source-authorized.

## PASS

MARGINFI_SAME_TX_PROGRAM_SAMPLE_PASS if:
- all 64 canonical transactions are recovered;
- canonical instruction binding is complete;
- identity conflicts = 0.

PASS is transport/source evidence only.
It does not assign direction.

## Firewall

prices=false
returns=false
amount_labeling=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
