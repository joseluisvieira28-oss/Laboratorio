# DLS — MARGINFI SOL FEB-MAR SOURCE PREREQUISITE ADDENDUM V0.2

Date: 2026-09-29
Branch: dls-marginfi-transient-reversion-v01
Status: FROZEN BEFORE ANY FEB-MAR 2024 MARKET OUTCOME IS OPENED

Parent:
- MARGINFI_SOL_POST_CASCADE_REVERSION_V0_1_DEVELOPMENT_FREEZE_2026-09-29.md
- MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_TEMPORAL_SOURCE_EXTENSION_FREEZE_V0.1.md
- canonical historical Marginfi field-enrichment run 36263998920
- canonical Marginfi bank registry run 36312418451

## Purpose

The return family is frozen to native SOL collateral only.

Therefore its source prerequisite is narrowed to the exact tested universe rather than requiring
direction authority for unrelated non-SOL collateral liquidations.

This is a source-only operational/scientific scoping correction made before any Feb-Mar market price,
return or PnL is opened.

It is not based on Feb-Mar market outcomes.

## Canonical source population

Use the already-completed canonical field-enrichment partitions:

February 2024:
- run 36263998920
- artifact dls-field-enrichment-ms-marginfi-202402
- artifact ID 10918739012
- digest sha256:06328187b685956c40be75d9d24145ac7cbd996b8e2d9b3d2556bdc132d85e3
- FIELD_ENRICHMENT_PARTITION_PASS
- 29,212 / 29,212 enriched successful Marginfi liquidations
- missing=0, extra=0, duplicate=0, semantic conflicts=0

March 2024:
- run 36263998920
- artifact dls-field-enrichment-ms-marginfi-202403
- artifact ID 10920215502
- digest sha256:1e78d2203b553c429534b3444567cd4fdf3e202091fb7652618021cbc09f060d
- FIELD_ENRICHMENT_PARTITION_PASS
- 29,962 / 29,962 enriched successful Marginfi liquidations
- missing=0, extra=0, duplicate=0, semantic conflicts=0

No new population scan may redefine these partitions.

## Frozen SOL selection

A canonical Marginfi liquidation belongs to the SOL source population iff its source-authoritative
asset_bank maps in the frozen Marginfi bank registry to:

So11111111111111111111111111111111111111112

No amount, liability mint, hop count, timestamp pattern, market price or return participates in this
selection.

The bank registry is the same source authority already used for Jan-2024 signed-flow validation.

## Exact transaction source rule

For every SOL-population liquidation:
- recover its exact historical successful transaction by signature/slot;
- require exact canonical Marginfi instruction identity;
- identify committed successful Jupiter V6 instructions strictly after the liquidation instruction;
- if none exist, the liquidation is not a Jupiter-route member;
- for route members, apply exactly the already-frozen V0.2 ordered simple-chain SwapEvent decoder.

Direction semantics remain unchanged:
- route endpoint asset mint -> liability mint =
  COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN / SOL SIGNED_SELL_PRESSURE_PROVEN;
- opposite endpoint order =
  LIABILITY_TO_COLLATERAL_MULTI_HOP_PROVEN;
- mismatch = DIRECTION_AMBIGUOUS;
- missing route ownership/decode/bank evidence = SOURCE_EVIDENCE_INCOMPLETE.

## Global SOL source gate

MARGINFI_SOL_FEBMAR_SIGNED_FLOW_SOURCE_PASS only if ALL:
1. both monthly canonical field-enrichment partitions are PASS;
2. every frozen SOL-population identity is adjudicated for Jupiter membership;
3. population duplicate identities = 0;
4. Jupiter route-member count > 0;
5. source-complete evidence among route members >= 95%;
6. deterministic direction among source-complete route members >= 90%;
7. contradictions = 0.

Threshold miss with valid source:
MARGINFI_SOL_FEBMAR_SIGNED_FLOW_SOURCE_PARTIAL

Source/identity/transport conflict:
MARGINFI_SOL_FEBMAR_SIGNED_FLOW_SOURCE_BLOCKED

## Return-family binding

For MARGINFI SOL POST-CASCADE TRANSIENT REVERSION V0.1 only, this PASS supersedes the broader prerequisite
MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_PASS.

All return-side rules remain exactly unchanged:
- SOL only;
- source-only 5-minute cascade construction;
- LONG;
- first full minute after cascade end;
- 15-minute hold;
- nominal costs unchanged;
- Development Feb-Mar only;
- Jan not validation;
- Apr-Jun closed unless Development SURVIVES.

## Firewall

prices=false
returns=false
pnl=false
feb_mar_market_outcomes_opened=false
jan_2024_validation_used=false
apr_jun_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
