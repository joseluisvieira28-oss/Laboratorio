# DLS — MARGINFI JUPITER POST-LIQUIDATION ROUTE CLASS FREEZE V0.1

Date: 2026-09-29
Status: FROZEN BEFORE JAN-2024 CLASS MEMBERSHIP CENSUS
Branch: dls-signed-flow-authority-v01
Parent: SIGNED_FLOW_SOURCE_AUTHORITY_FREEZE_V0.1.md

## Discovery evidence

A deterministic 64-event December-2023 Marginfi source-only sample was frozen before transaction composition was read.

Run:
36531548552

Classification:
MARGINFI_SAME_TX_PROGRAM_SAMPLE_PASS

Observed source-only discovery:
- sample = 64
- exact transactions complete = 64
- identity conflicts = 0
- 45 / 64 sample transactions contain Jupiter V6 after the canonical liquidation instruction.

This is class-discovery evidence only.
No amount, price, return, PnL or market direction was inspected.

## Program identity authority

Official Jupiter repository:
jup-ag/instruction-parser

Pinned source:
jup-ag/instruction-parser@e6f77951377847c579112e6a16d8c17c5c092485

Its README identifies:
JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4
as Jupiter V6 contract version 6.0.7 and describes the library as a parser for the Jupiter V6 swap instruction.

Therefore this program ID is source-authorized as:
JUPITER_V6_SWAP_PROGRAM.

No downstream DEX program is needed for class membership.

## Marginfi semantic authority

Pinned Marginfi source:
0dotxyz/marginfi-v2@f6d3d5616e293c9468333571c3ceb90bb2410b00

For lending_account_liquidate it states the accounting semantics:
- liquidator removes liability-token balance L;
- liquidator receives collateral asset-token balance A;
- liquidatee removes A and receives liability repayment.

This internal Marginfi transfer alone is NOT market pressure.

## Frozen class

Class ID:
MARGINFI_JUPITER_POST_LIQUIDATION_ROUTE_V0_1

An event belongs to this class only if all are true:
1. it is a canonical successful Marginfi lending_account_liquidate event;
2. exact canonical signature + instructionAddress are recovered;
3. exact parent transaction is successful;
4. the exact same transaction contains at least one committed Jupiter V6 instruction;
5. the Jupiter instructionAddress sorts strictly after the canonical Marginfi liquidation instructionAddress.

Class membership uses only transaction/program semantics.
No token amount, token balance delta, price, return, or later wallet behavior is used.

## Independent validation population

Use exactly:
- canonical field-enrichment run: 36263998920
- artifact: dls-field-enrichment-ms-marginfi-202401
- artifact ID: 10918871581
- digest: sha256:2f48b0d494bdf7d76f349e7469498ee8215fb81f2421de75533c3fa5c9453b55
- interval: 2024-01-01T00:00:00Z <= timestamp < 2024-02-01T00:00:00Z
- classification: FIELD_ENRICHMENT_PARTITION_PASS
- canonical class: lending_account_liquidate
- observed population count before this freeze: 10,381

December-2023 discovery events are not used as the validation population.

## Source census

Query only:
- canonical Marginfi liquidation instruction identity;
- Jupiter V6 instruction identity;
- transaction signature/error;
- transaction/instruction index and instructionAddress.

No token balances in this stage.

Every canonical Jan-2024 Marginfi event must be reconciled against the source stream.

## PASS

MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_PASS if:
- all 10,381 canonical Marginfi events are recovered exactly;
- identity conflicts = 0;
- source transport errors = 0;
- class member count > 0.

PASS authorizes a separately frozen source-only realized-flow/direction calibration for this class.

If all canonical events reconcile but member_count = 0:
MARGINFI_JUPITER_ROUTE_CLASS_EMPTY.

If reconciliation cannot be completed:
MARGINFI_JUPITER_ROUTE_CLASS_BLOCKED.

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
