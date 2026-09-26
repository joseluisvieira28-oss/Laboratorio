# DEFI-LIQUIDATION-SHOCK-001 — GLOBAL PRE-DISCOVERY FIELD COVERAGE FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SCHEMA/PROVENANCE REQUIREMENTS / SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Define the minimum event-field and provenance requirements that MUST be satisfied before FINAL PRE-DISCOVERY AUTHORITY may open any economic outcome data.

This document does not choose event-size thresholds, return horizons, direction, PnL, protocol weights or market-response criteria.

## Frozen protocol universe

The source universe remains:
- Save/Solend
- marginfi
- Kamino
- Drift v2

No protocol may be added or dropped because of observed market outcomes.

## Canonical event identity

Every realized liquidation event must retain:
- protocol
- exact frozen instruction class
- signature
- slot
- UTC block timestamp
- transactionIndex when available
- instructionAddress
- outer/inner path class
- exact frozen program ID
- exact discriminator/tag
- transaction success state
- instruction committed/error state
- source artifact provenance
- RAW verification status where sampled/mandatory

Canonical instruction key:
`protocol + instruction_class + signature + instructionAddress`

## Required reconstruction schema

The pre-Discovery data layer must explicitly adjudicate availability for each canonical event field below.

### Temporal / ordering
- exact block timestamp UTC
- slot
- transaction index
- instruction path ordering
- same-signature multi-instruction ordering
- deterministic global ordering key

### Liquidation participant/account context
- liquidated account / obligation / margin account identity where encoded
- liquidator identity where encoded
- protocol market/reserve/bank identifiers used by the instruction
- source accounts required to resolve asset identities

### Asset identity
- debt / liability asset identity
- collateral / deposit asset identity
- perp market identity for Drift perp liquidation classes
- spot market / bank / reserve identity where relevant
- explicit `NOT_APPLICABLE` for structurally absent sides
- explicit `SOURCE_NOT_RECONSTRUCTABLE` if the historical source cannot defensibly resolve a required identity

### Native instruction amount fields
For each frozen instruction class, determine from historically pinned source/IDL whether the instruction encodes:
- requested liquidation amount
- max liquidation amount
- collateral amount
- debt amount
- transfer amount
- limit amount
- or no directly encoded amount

At this stage record schema/availability and raw integer representation only if required for decoder validation. Do NOT convert to USD/notional, do NOT attach market price, and do NOT use amount magnitude for sample selection.

### Decimal / unit metadata
Before economic use, document whether amount units can be reconstructed using:
- mint decimals
- protocol bank/reserve decimals
- market precision constants
- fixed-point/scaling rules

Missing unit metadata must fail closed for any later notional calculation; it must not be guessed.

## Per-protocol decoder authority requirements

For each frozen instruction class:
1. pin historical source/IDL commit or byte-level schema authority;
2. map exact discriminator/tag to decoder;
3. map argument byte offsets/types;
4. map relevant account positions to semantic roles;
5. document version applicability interval;
6. test against at least one RAW-success transaction already inside source authority;
7. prove decoder output is deterministic;
8. report fields as `DIRECT`, `DERIVED_FROM_ACCOUNT_METADATA`, `NOT_APPLICABLE`, or `SOURCE_NOT_RECONSTRUCTABLE`.

No current mutable IDL may silently reinterpret historical bytes.

## Missing-data policy

Missingness is data, not permission to infer.

Allowed statuses:
- `FIELD_PRESENT_DIRECT`
- `FIELD_PRESENT_DERIVED_WITH_PINNED_AUTHORITY`
- `FIELD_NOT_APPLICABLE`
- `FIELD_SOURCE_NOT_RECONSTRUCTABLE`
- `FIELD_SOURCE_CONFLICT_FAIL_CLOSED`

A required field that is source-conflicted blocks economic use of that event/class until resolved.

A non-required field may remain explicitly missing, but the missingness rate must be reported before Sample Gate freeze.

## Cascade / clustering prerequisites

Before defining the numerical cascade rule, the source layer must prove it can deterministically order events using source-only fields.

Permitted prospective clustering inputs:
- protocol
- frozen instruction class
- exact UTC time
- slot
- transaction identity
- account/obligation identity when defensibly reconstructable
- asset/market identity when defensibly reconstructable

Forbidden at this stage:
- price movement
- return sign/magnitude
- realized/future PnL
- post-event volatility
- outcome-conditioned cluster definitions

## Required pre-Discovery report

Before FINAL PRE-DISCOVERY AUTHORITY, produce per protocol/class:
- realized event count
- calendar coverage
- unique signatures
- outer vs inner counts
- field availability counts/rates
- source-conflict counts
- explicit missingness counts/rates
- account/asset reconstruction coverage
- amount-schema availability
- deterministic ordering coverage

These are source-population diagnostics only.

## Gate

This schema freeze does NOT authorize Discovery.

Discovery remains CLOSED until:
1. all source censuses have explicit final PASS receipts;
2. recovery evidence is reconciled;
3. this field-coverage audit is complete;
4. a numerical Sample/Experiment Gate is frozen prospectively;
5. FINAL PRE-DISCOVERY AUTHORITY is committed before any economic outcomes are accessed.

## Firewall

prices=false
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
