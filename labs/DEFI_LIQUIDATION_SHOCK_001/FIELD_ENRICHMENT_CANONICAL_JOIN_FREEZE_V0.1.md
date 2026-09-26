# DEFI-LIQUIDATION-SHOCK-001 — FIELD ENRICHMENT CANONICAL JOIN FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Define the only permitted population-wide enrichment rule for accounts, full instruction data and source metadata after the source census is frozen.

## Immutable event population

The enrichment layer receives the canonical realized-event identities from the terminal source census.

Canonical key:

`protocol + instruction_class + signature + instructionAddress`

For single-class protocol partitions, `instruction_class` is the frozen protocol liquidation instruction/tag identity.

The enrichment process is forbidden from adding, removing, ranking or filtering canonical events.

## Allowed re-query

For each exact frozen source partition/chunk, the enrichment re-query may add only source fields such as:

- instruction `accounts`;
- full instruction `data`;
- transaction account keys when needed for source reconciliation;
- source-state metadata later authorized by a pinned decoder.

The re-query must use:
- the same frozen program ID;
- same historical decoder/tag/discriminator;
- same exact UTC membership;
- same transaction-success semantics;
- same instruction-address identity.

## Exact join rule

For each enrichment unit compute:

`CANONICAL_KEY_SET_OLD`

from the accepted source-census evidence, restricted to realized successful events.

Compute:

`CANONICAL_KEY_SET_ENRICHED`

from the enrichment stream using the same realized-success semantics.

PASS requires:

- missing canonical keys = 0;
- extra enriched keys = 0;
- duplicate canonical keys = 0;
- duplicate enriched keys = 0;
- identity conflicts = 0.

Only then may enrichment fields be attached.

PASS classification:

`FIELD_ENRICHMENT_CANONICAL_KEY_SET_EXACT_PASS`

Any mismatch:

`FIELD_ENRICHMENT_CANONICAL_JOIN_FAIL_CLOSED`

## Missing field policy

A canonical event remains in the population even if an enrichment field is unavailable.

Field status must be one of:

- `FIELD_PRESENT_DIRECT`
- `FIELD_PRESENT_DERIVED_WITH_PINNED_AUTHORITY`
- `FIELD_NOT_APPLICABLE`
- `FIELD_SOURCE_NOT_RECONSTRUCTABLE`
- `FIELD_SOURCE_CONFLICT_FAIL_CLOSED`

Enrichment failure is never permission to drop the event.

## Amount rule

Instruction-request or max-transfer arguments may be decoded only under `FIELD_DECODER_AUTHORITY_MATRIX`.

They remain semantically distinct from realized transfer amounts.

No USD conversion, price attachment or size-based filtering is authorized.

## Scaling rule

Before full population execution:
1. transport calibration must PASS;
2. at least one exact canonical-key join calibration must PASS for each collector family;
3. only then may the same frozen implementation fan out over all accepted source partitions.

## Firewall

prices=false
returns=false
pnl=false
direction=false
economic_outcomes=false
balances=false
token_amounts=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
