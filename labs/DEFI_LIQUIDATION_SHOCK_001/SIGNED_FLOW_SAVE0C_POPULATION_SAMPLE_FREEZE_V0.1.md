# DLS — SIGNED FLOW SAVE0C POPULATION SAMPLE FREEZE V0.1

Date: 2026-09-28
Status: FROZEN SOURCE-ONLY SAMPLE / NO MARKET OUTCOME ACCESS

## Population source

Canonical artifact:
- workflow run 36263998920
- artifact dls-field-enrichment-ms-save0c-202205
- artifact ID 10927767752
- partition save0c-202205
- FIELD_ENRICHMENT_PARTITION_PASS

## Deterministic sample

Rank every canonical enriched row by ascending SHA256 of:

signature || "|" || JSON-canonical instructionAddress

Select first 64 events.

No event is selected from price, amount or later behavior.

## Exact event binding

For each sampled event, query exact slot from the already-calibrated SQD finalized stream using:
- Save/Solend program ID;
- d1 = 0x0c;
- isCommitted=true;
- transaction=true;
- transactionTokenBalances=true.

Find the exact canonical event by signature + instructionAddress.

Token-balance rows may omit transactionIndex under the already frozen relation-binding addendum.

A target token balance with omitted transactionIndex may bind only if:
1. the exact canonical event instruction is recovered;
2. among all successful matching Save0c liquidation instructions returned in that slot, the sampled event is the only one whose frozen four economic token-account roles contain that account.

Otherwise that target is SOURCE_EVIDENCE_INCOMPLETE.

## Frozen economic roles

From the canonical event:
- debt_source = source_liquidity_token_account
- debt_reserve = repay_reserve_liquidity_supply
- collateral_reserve = withdraw_reserve_collateral_supply
- collateral_destination = destination_collateral_token_account

For each role report raw pre/post delta.

Expected successful liquidation transfer pattern is descriptive only:
- debt_source <= 0
- debt_reserve >= 0
- collateral_reserve <= 0
- collateral_destination >= 0

The pattern does NOT prove market buy/sell pressure.

## Sample classifications

AMOUNT_TRANSFER_PATTERN_PROVEN:
- all four role deltas parseable;
- at least one nonzero delta;
- signs are consistent with the frozen role pattern.

AMOUNT_EVIDENCE_COMPLETE_PATTERN_OTHER:
- all four deltas parseable but signs differ.

SOURCE_EVIDENCE_INCOMPLETE:
- fewer than four role deltas can be unambiguously bound.

## Sample PASS

SAVE0C_SIGNED_FLOW_SAMPLE_SOURCE_PASS if:
- >=95% of 64 events have complete four-role amount evidence;
- contradictions in canonical event identity = 0.

PASS authorizes larger source-only coverage work.
It does not authorize signed return or trading.

## Firewall

prices=false
returns=false
2025_market_outcomes=false
2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
