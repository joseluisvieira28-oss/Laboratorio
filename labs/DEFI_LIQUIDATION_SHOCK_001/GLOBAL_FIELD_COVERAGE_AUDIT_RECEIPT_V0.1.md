# DEFI-LIQUIDATION-SHOCK-001 — GLOBAL FIELD COVERAGE AUDIT RECEIPT V0.1

Date: 2026-09-26
Status: SOURCE-ONLY / OUTCOME-BLIND / PARTIAL PASS WITH ENRICHMENT BLOCKER

## Purpose

Audit the fields actually preserved by the frozen SQD census collectors against
`GLOBAL_PRE_DISCOVERY_FIELD_COVERAGE_FREEZE_V0.1.md`.

This audit does not open prices, returns, PnL, market direction or protected outcomes.

## Collector evidence reviewed

Frozen collectors:
- Kamino + Save11: `source/run_sqd_event_census_partition_v0_4_3.py`
- Marginfi + Save0c: `source/run_sqd_first_success_partition_v0_1.py`
- Drift v2: `source/run_drift_sqd_first_success_partition_v0_1.py`

Historical decoder authority:
- `HISTORICAL_DECODER_AUTHORITY_MATRIX_V0.3.md`
- prior matrices V0.1/V0.2 preserved for audit history.

## Fields preserved directly in census rows

All three collector families preserve the following source fields for each matched instruction:

- protocol identity;
- instruction class where the protocol has multiple frozen classes;
- transaction signature;
- slot;
- exact UTC block timestamp;
- transaction index;
- instruction address;
- outer/inner path derivable deterministically from instruction address;
- transaction error state;
- instruction committed state;
- instruction error state;
- decoded frozen discriminator/tag prefix;
- realized-success / failed-attempt / anomaly classification.

Classification:

`SOURCE_EVENT_IDENTITY_ORDERING_EXECUTION_FIELDS_PASS`

## Fields available from pinned authority rather than copied into every row

The following are deterministic from the frozen protocol/class registry and historical authority:

- program ID;
- frozen instruction name;
- discriminator/native tag;
- decoder applicability lower boundary;
- protocol family.

Classification:

`FIELD_PRESENT_DERIVED_WITH_PINNED_AUTHORITY`

## Proven ordering capability

The source layer can deterministically order realized events by:

1. exact UTC timestamp;
2. slot;
3. transaction index;
4. instruction address;
5. signature as deterministic final tie-break.

This is sufficient to freeze a future source-only cascade/clustering rule without consulting market outcomes.

Classification:

`DETERMINISTIC_SOURCE_ORDERING_PASS`

## Critical field-coverage gap found

The frozen SQD queries request instruction fields:

- `programId`
- `data`
- `transactionIndex`
- `instructionAddress`
- `isCommitted`
- `error`

They do **not** request/persist instruction account references.

Therefore the current full-census artifacts do not, by themselves, provide population-wide:

- liquidated account / obligation / margin account;
- liquidator;
- debt reserve / bank / spot market;
- collateral reserve / bank / market;
- debt asset identity;
- collateral/deposit asset identity;
- perp market identity;
- account-position mapping needed for protocol-specific semantic roles.

Classification:

`ACCOUNT_ROLE_AND_ASSET_IDENTITY_ENRICHMENT_REQUIRED`

This is a source-field blocker, not a scientific failure and not NO_EDGE.

## Native instruction amount schema

The census rows preserve the full Base58 instruction `data` only transiently for decoding the frozen prefix; the normalized rows currently persist only `decoded_prefix_hex`.

Therefore population-wide instruction arguments such as liquidation amount, max amount, market index or other class-specific argument fields are not yet recoverable from the normalized census receipts alone.

Historical source commits are pinned for instruction applicability, but a separate decoder extraction must freeze, per instruction class:

- argument byte layout and types;
- account-position semantic roles;
- version applicability;
- unit / precision interpretation.

Classification:

`INSTRUCTION_ARGUMENT_AND_AMOUNT_ENRICHMENT_REQUIRED`

## Decimal / unit metadata

No price or USD conversion is authorized.

Before any notional use, the enrichment layer must separately source-pin:
- mint decimals where SPL mint identity is recoverable;
- protocol bank/reserve decimals or scaling rules;
- Drift market precision constants where applicable.

Current classification:

`UNIT_METADATA_PENDING_SOURCE_ONLY_ENRICHMENT`

## Current per-family source authority

### Kamino + Save11
- full census source authority: PASS;
- independent authority audit: PASS;
- RAW reconciliation: 64/64 PASS.

### Marginfi + Save0c
- full reconstructed census source authority: PASS;
- final classification: `MARGINFI_SAVE0C_EVENT_CENSUS_SOURCE_PASS`;
- RAW reconciliation: 64/64 PASS;
- Marginfi successful instructions: 266,647;
- Save0c successful instructions: 66,628;
- gap count: 0;
- anomaly count: 0.

### Drift
- four frozen classes historically source-supported;
- fourth class first-success boundary formally PASS;
- all timeout recovery waves complete;
- final full-census authority reassembly is still being adjudicated at the time of this receipt.

## Enrichment rule frozen by this audit

The existing census population MUST NOT be reselected or filtered based on enrichment availability.

A new source-only enrichment layer may:
1. take the already frozen canonical event identities;
2. retrieve or decode only source/protocol/account metadata required by the field-coverage freeze;
3. attach explicit field status:
   - `FIELD_PRESENT_DIRECT`
   - `FIELD_PRESENT_DERIVED_WITH_PINNED_AUTHORITY`
   - `FIELD_NOT_APPLICABLE`
   - `FIELD_SOURCE_NOT_RECONSTRUCTABLE`
   - `FIELD_SOURCE_CONFLICT_FAIL_CLOSED`
4. preserve every canonical event even when enrichment fails;
5. report missingness by protocol/class before Sample Gate freeze.

The enrichment layer MUST NOT:
- query market prices;
- compute USD notional;
- compute returns/PnL;
- discard events because amount/account fields are missing;
- choose thresholds from event magnitudes;
- select protocols/classes based on later outcomes.

## Verdict

`FIELD_COVERAGE_STATIC_SCHEMA_PARTIAL_PASS_ENRICHMENT_REQUIRED`

Passed:
- event identity;
- timestamp/slot ordering;
- instruction path;
- success/failure semantics;
- discriminator/program authority;
- deterministic source ordering.

Still required before FINAL PRE-DISCOVERY:
- protocol-specific account-role decoder map;
- asset identity reconstruction;
- instruction argument/amount decoder map;
- unit/precision metadata;
- population-wide enrichment coverage and explicit missingness report;
- terminal Drift census authority.

This receipt does NOT authorize economic Discovery.
