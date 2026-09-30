# DLS — MARGINFI SOL POST-LIQUIDATION ROUTE MIGRATION V0.1 — SOURCE FREEZE

Date: 2026-09-30
Branch: dls-marginfi-route-migration-v01
Status: FROZEN SOURCE-ONLY / NO MARKET OUTCOMES

Family ID:
DLS-MARGINFI-SOL-ROUTE-MIGRATION-001

## Motivation

Source-authoritative SOL liquidation evidence showed a sharp change in the share of Marginfi SOL
liquidations with a post-liquidation Jupiter V6 route:

- July 2024: 487 / 865
- August 2024: 277 / 7,677
- September 2024: 18 / 315

This probe asks whether the same-transaction post-liquidation program composition changed across
July/August/September, and whether another identifiable program or program family replaced Jupiter.

This is descriptive source research only.
No market edge, price effect or causality is assumed.

## Canonical source populations

Use only the already-audited canonical Marginfi field-enrichment partitions:

July:
- artifact ID 10924100354
- marginfi-202407
- 4,907 / 4,907 enriched

August:
- artifact ID 10925020784
- marginfi-202408
- 13,056 / 13,056 enriched

September:
- artifact ID 10924302485
- marginfi-202409
- 1,558 / 1,558 enriched

Use the source-authoritative Marginfi bank registry:
- run 36312418451
- artifact ID 10929339072

Restrict each monthly population to rows whose source-authoritative asset_bank maps exactly to:

So11111111111111111111111111111111111111112

No market outcome or post-liquidation program participates in population inclusion.

## Deterministic sample

For each month independently:

rank every canonical SOL-population row by ascending SHA256 of:

signature + "|" + canonical-json(instructionAddress)

Select exactly the first min(128, monthly SOL population count).

No sampling by:
- transaction composition;
- Jupiter presence;
- DEX/program identity;
- amount;
- timestamp cluster;
- price;
- return;
- PnL.

The sample is fixed before program composition is opened.

## Exact same-transaction census

For each sampled liquidation:
- query the exact finalized slot;
- recover the exact successful parent transaction by canonical signature;
- require one canonical Marginfi liquidation match by program ID + exact instructionAddress;
- retain all committed successful instructions belonging to the exact parent transaction;
- sort by canonical instructionAddress;
- classify each instruction relation as BEFORE / AT / AFTER relative to the canonical liquidation.

Report:
- every ordered programId;
- all AFTER programId frequencies;
- per-transaction unique AFTER program set;
- ordered program sequences;
- transactions with zero AFTER instructions.

No program ID is labeled as DEX, aggregator, router, swap or market protocol inside the source census
unless a separate source-identity lookup is performed after the immutable receipt is created.

## Cross-month outputs

For each month:
- sample count;
- complete transaction count;
- identity conflicts;
- AFTER program instruction frequency;
- AFTER program transaction-presence frequency;
- ordered sequence frequency.

Global:
- exact program IDs whose transaction-presence share changes materially between months;
- raw shares only, no causal interpretation.

Descriptive flag for investigation:
a program is marked ROUTE_MIGRATION_CANDIDATE if:
- present in >= 10% of sampled August transactions after liquidation; and
- August transaction-presence share is >= 2x July share;
OR
- present in >= 10% of sampled September transactions after liquidation; and
- September share is >= 2x July share.

This flag is source-descriptive only and does not establish swap semantics.

## PASS

MARGINFI_SOL_ROUTE_MIGRATION_SOURCE_PASS iff:
- July sample adjudicated exactly;
- August sample adjudicated exactly;
- September sample adjudicated exactly;
- all sampled parent transactions recovered;
- canonical instruction binding complete;
- identity conflicts = 0;
- unresolved transport failures = 0.

Otherwise:
MARGINFI_SOL_ROUTE_MIGRATION_SOURCE_BLOCKED

## Firewall

prices=false
ohlc=false
returns=false
pnl=false
market_2024_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
