# DEFI-LIQUIDATION-SHOCK-001 — FIELD ENRICHMENT EXECUTION SPEC V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY TECHNICAL SPEC / OUTCOME-BLIND

Prerequisites already demonstrated:
- FIELD_ENRICHMENT_TRANSPORT_8_OF_8_PASS
- FIELD_DECODER_AUTHORITY_8_OF_8_CLASS_PASS
- FIELD_DECODER_IMPLEMENTATION_8_OF_8_PASS
- FIELD_ENRICHMENT_CANONICAL_JOIN_3_OF_3_FAMILY_PASS
- UNIT_METADATA_SOURCE_FEASIBILITY_PASS

## Immutable population rule

Canonical key:
`protocol + instruction_class + signature + instructionAddress`

Enrichment must not add, remove, rank, filter or reclassify realized events.

## Required output fields

Preserve event identity, timing, execution provenance, full instruction data and raw account list.

Attach source-authoritative semantic fields where applicable:
- liquidated account / obligation / user
- liquidator / transfer authority
- debt/liability reserve, bank or market identity
- collateral/asset reserve, bank or market identity
- Drift spot/perp market indexes
- lending market / group identity
- instruction argument schema name and primitive type

Numerical requested/max amount values are not emitted as semantic analysis columns at this stage.
Full Base58 instruction data is retained only as source/audit evidence.

## Field statuses

Use only:
- FIELD_PRESENT_DIRECT
- FIELD_PRESENT_DERIVED_WITH_PINNED_AUTHORITY
- FIELD_NOT_APPLICABLE
- FIELD_SOURCE_NOT_RECONSTRUCTABLE
- FIELD_SOURCE_CONFLICT_FAIL_CLOSED

Missing enrichment never permits event deletion.

## Protocol-native asset identity

- Save / Kamino: repay_reserve and withdraw_reserve
- marginfi: liab_bank and asset_bank
- Drift: frozen spot/perp market indexes

Mint/symbol mapping remains a separate source-metadata step.

## Exact join

For every partition:
- old canonical key set from accepted source evidence;
- enriched canonical key set from re-query;
- missing=0;
- extra=0;
- duplicate=0;
- identity conflict=0.

Any mismatch is fail-closed.

Accepted partition classification:
`FIELD_ENRICHMENT_PARTITION_PASS`

## Aggregate report before Sample Gate

Report per protocol/class:
- canonical realized event count
- enriched event count
- exact-join result
- liquidated-account coverage
- liquidator coverage
- debt/liability asset identity coverage
- collateral/asset identity coverage
- argument-schema coverage
- unit-metadata reconstructability
- explicit missingness
- source conflict count

## Firewall

prices=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
