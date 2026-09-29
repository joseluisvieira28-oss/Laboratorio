# DLS — MARGINFI JUPITER FEB-MAR 2024 SIGNED-FLOW TEMPORAL SOURCE EXTENSION V0.1

Date: 2026-09-29
Branch: dls-marginfi-transient-reversion-v01
Status: FROZEN SOURCE-ONLY BEFORE ANY FEB-MAR 2024 MARKET RETURN IS OPENED

Parent authorities:
- FIELD_DECODER_AUTHORITY_MATRIX_V0.2.md
- MARGINFI_JUPITER_MULTI_HOP_DIRECTION_CALIBRATION_FREEZE_V0.2.md
- MARGINFI_JUPITER_MULTI_HOP_SIGNED_FLOW_SOURCE_PASS from canonical Jan-2024 run 36558125697
- source-authoritative Marginfi bank->mint registry from run 36312418451

## Purpose

Determine whether the exact Jan-2024 Marginfi -> Jupiter signed-flow semantics remain source-valid in a
strictly later, outcome-unopened source period:

[2024-02-01T00:00:00Z, 2024-04-01T00:00:00Z)

This mission opens source transactions only.
It does NOT open price, return, PnL, volatility or any market outcome.

## Frozen Marginfi population

Program:
MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA

Instruction:
lending_account_liquidate

Anchor discriminator:
d6a997d5fba756db

Historical fixed account authority:
0 marginfi_group
1 asset_bank
2 liab_bank
3 liquidator_marginfi_account
4 signer
5 liquidated_marginfi_account
6 bank_liquidity_vault_authority
7 bank_liquidity_vault
8 bank_insurance_vault
9 token_program

Every successful committed instruction matching the exact program + discriminator inside the frozen
window belongs to the canonical source population.

No amount, token, direction or market outcome may filter the canonical population.

## Frozen Jupiter route class

Jupiter V6 program:
JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4

A Marginfi liquidation becomes a route-class member iff its exact successful transaction contains at
least one committed successful Jupiter V6 instruction whose canonical instructionAddress is strictly
after the Marginfi liquidation instructionAddress.

Program presence alone does not prove direction.

## Frozen multi-hop direction semantics

Use exactly the V0.2 source semantics already validated in Jan-2024:

1. Require exactly one post-liquidation Jupiter route root.
2. Decode source-valid Jupiter SwapEvent records only beneath that root.
3. Sort by canonical instructionAddress execution order.
4. Each event must have:
   - inputMint != outputMint
   - inputAmount > 0
   - outputAmount > 0
5. Multiple events must form one ordered simple chain:
   Ei.outputMint == E(i+1).inputMint
6. No duplicate pair and no mint-cycle/repeated endpoint path.
7. Realized route endpoints are:
   I = first SwapEvent.inputMint
   O = final SwapEvent.outputMint.
8. Bank identity:
   A = source-authoritative mint of Marginfi asset_bank
   L = source-authoritative mint of Marginfi liab_bank.
9. If I == A and O == L:
   COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN
   asset = SIGNED_SELL_PRESSURE_PROVEN
   liability = SIGNED_BUY_PRESSURE_PROVEN.
10. If I == L and O == A:
   LIABILITY_TO_COLLATERAL_MULTI_HOP_PROVEN
   liability = SIGNED_SELL_PRESSURE_PROVEN
   asset = SIGNED_BUY_PRESSURE_PROVEN.
11. Otherwise:
   DIRECTION_AMBIGUOUS.

Any missing bank mapping, route-root ambiguity, event decode failure, broken chain or cycle:
SOURCE_EVIDENCE_INCOMPLETE.

No semantic rule may change after this source period is opened.

## Frozen source shards

Exactly 12 non-overlapping five-day shards:

fm-01 [2024-02-01, 2024-02-06)
fm-02 [2024-02-06, 2024-02-11)
fm-03 [2024-02-11, 2024-02-16)
fm-04 [2024-02-16, 2024-02-21)
fm-05 [2024-02-21, 2024-02-26)
fm-06 [2024-02-26, 2024-03-02)
fm-07 [2024-03-02, 2024-03-07)
fm-08 [2024-03-07, 2024-03-12)
fm-09 [2024-03-12, 2024-03-17)
fm-10 [2024-03-17, 2024-03-22)
fm-11 [2024-03-22, 2024-03-27)
fm-12 [2024-03-27, 2024-04-01)

Sharding changes transport only.

## Shard requirements

Each shard must:
- cover its exact frozen timestamp interval;
- stream the finalized Solana source continuously from resolved start slot to end boundary;
- recover unique successful Marginfi liquidation identities;
- preserve exact signature, slot, timestamp, transactionIndex, instructionAddress and accounts;
- record all route-class members and source direction adjudications;
- have zero population identity duplicates;
- have zero structural source conflicts.

Shard classification:
MARGINFI_FEBMAR_SOURCE_SHARD_COMPLETE
or
MARGINFI_FEBMAR_SOURCE_SHARD_BLOCKED.

Direction incompleteness itself does not block a shard; it is adjudicated by the global gate.

## Global source PASS

MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_PASS only if ALL are true:

1. all 12 shard receipts are COMPLETE;
2. intervals cover the frozen source window with no gap/overlap;
3. merged population identity duplicates = 0;
4. route-class member count > 0;
5. source-complete direction evidence among route members >= 95%;
6. deterministic direction among source-complete route members >= 90%;
7. contradictions = 0.

Threshold miss with valid source:
MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_PARTIAL

Transport/layout/identity/source conflict:
MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_BLOCKED

## Consequence

PASS authorizes a separately frozen NEW transient-impact/mean-reversion return experiment using
Feb-Mar 2024 as its first market-outcome Development period.

Jan-2024 may not be reused to validate that new hypothesis because Jan outcomes have already been seen.

No return rule, entry, side, hold, threshold or cost is authorized by this source freeze.

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
