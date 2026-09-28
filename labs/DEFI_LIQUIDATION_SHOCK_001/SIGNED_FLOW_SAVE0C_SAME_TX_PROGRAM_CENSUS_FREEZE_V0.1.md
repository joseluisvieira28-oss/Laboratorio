# DLS — SAVE0C SAME-TRANSACTION PROGRAM CENSUS FREEZE V0.1

Date: 2026-09-28
Status: FROZEN SOURCE-ONLY DIAGNOSTIC

## Population

Use exactly the same deterministic 64-event Save0c sample frozen by:
SIGNED_FLOW_SAVE0C_POPULATION_SAMPLE_FREEZE_V0.1.md

Do not resample.

## Query

For each sampled exact slot:
- request all instructions in the finalized block using the SQD Portal exact-slot query;
- request transaction signatures/errors;
- find the exact canonical liquidation by signature + instructionAddress;
- read its transactionIndex;
- retain only instructions with that exact transactionIndex.

## Output

For each event report:
- ordered instruction program IDs;
- instructionAddress;
- whether each instruction occurs before, at, or after the canonical liquidation instruction;
- count of distinct non-system/token programs after the liquidation.

Aggregate:
- program ID frequency across sampled transactions;
- program ID frequency strictly after liquidation;
- exact ordered program-sequence frequency.

No program is labeled a DEX, swap, redeem or market action in this census unless a separate source identity authority proves that label.

## PASS

SAVE0C_SAME_TX_PROGRAM_CENSUS_PASS if:
- all 64 canonical transactions are recovered exactly;
- instruction transactionIndex binding is complete;
- identity conflicts = 0.

Otherwise fail closed.

## Firewall

prices=false
returns=false
direction=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
