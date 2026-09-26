# DEFI-LIQUIDATION-SHOCK-001 — GLOBAL FIELD COVERAGE FINAL GATE FREEZE V0.1

Date: 2026-09-26
Status: PROSPECTIVELY FROZEN / SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Freeze the exact terminal requirements for closing the pre-Discovery source/field layer.
This gate is frozen before the population enrichment and unit-metadata aggregates are known.

No economic outcome access is authorized by this document.

## A. Source census authority — all mandatory

- Kamino + Save11:
  - KAMINO_SAVE11_EVENT_CENSUS_SOURCE_PASS
  - KAMINO_SAVE11_V043_AUTHORITY_AUDIT_PASS
  - RAW reconciliation PASS
- Marginfi + Save0c:
  - MARGINFI_SAVE0C_EVENT_CENSUS_SOURCE_PASS
  - RAW reconciliation PASS
- Drift:
  - DRIFT_FOUR_CLASS_EVENT_CENSUS_SOURCE_PASS
  - DRIFT_RAW_SAMPLE_RECONCILIATION_PASS
  - all four frozen classes observed successfully

These are already closed and cannot be reinterpreted based on later results.

## B. Decoder and transport authority — all mandatory

- FIELD_ENRICHMENT_TRANSPORT_8_OF_8_PASS
- FIELD_ENRICHMENT_CANONICAL_JOIN_3_OF_3_FAMILY_PASS
- FIELD_DECODER_AUTHORITY_8_OF_8_CLASS_PASS
- FIELD_DECODER_IMPLEMENTATION_8_OF_8_PASS

## C. Population field enrichment — all mandatory

Terminal PASS receipts required:
- KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_PASS
- MARGINFI_SAVE0C_FIELD_ENRICHMENT_POPULATION_PASS
- DRIFT_FIELD_ENRICHMENT_POPULATION_PASS

Each must prove:
- exact canonical population equality;
- missing=0;
- extra=0;
- duplicates=0;
- source/semantic conflicts=0;
- every realized event retains full source identity;
- required source-authoritative semantic account/market roles are present.

A partial or blocked population enrichment is NOT sufficient for the global gate.

## D. Unit / precision metadata — all mandatory

### Kamino + Save11
Required:
KAMINO_SAVE11_UNIT_METADATA_POPULATION_PASS

Every event must have source-defensible:
- debt underlying mint+decimals;
- collateral token mint+decimals;
- collateral underlying mint+decimals.

### Save0c
Required terminal state:
SAVE0C_UNIT_METADATA_POPULATION_PASS

SAVE0C_UNIT_METADATA_PARTIAL_SOURCE_COVERAGE is NOT sufficient for the global gate.
If V0.1 returns partial, the exact unmapped reserves must be resolved prospectively by additional
source authority without changing the event population.

Every event must ultimately have:
- debt underlying mint+decimals;
- collateral token mint+decimals;
- collateral underlying mint+decimals or equivalent pinned reserve-native unit identity.

### Marginfi
Required:
MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS

Every asset_bank and liab_bank used by the frozen realized population must map to one non-conflicting
mint+decimals identity. Partial registry coverage is not sufficient.

### Drift
Required future terminal receipt:
DRIFT_MARKET_UNIT_REGISTRY_POPULATION_PASS

Every spot market index observed in the frozen realized population must map to one source-defensible
mint+decimals identity.

Every perp market index observed must map to the frozen protocol-native precision semantics:
- base/perp precision = 1e9 / PERP_DECIMALS 9;
- quote precision = 1e6;
plus source-defensible market identity.

No market index may be guessed from symbol/name alone.

## E. Missingness / conflicts

Global PASS requires:
- unresolved required-field missingness = 0;
- source conflicts = 0;
- guessed decimals = 0;
- guessed mint/market mappings = 0;
- events dropped due to missing metadata = 0.

Non-applicable fields must be explicitly marked FIELD_NOT_APPLICABLE and are not missingness.

## F. Amount semantics firewall

This gate does NOT require or authorize use of:
- requested/max instruction amount numerical values;
- realized token transfer amounts;
- prices;
- USD notional;
- returns;
- PnL;
- direction.

Full instruction bytes may remain as audit evidence.

## G. Terminal verdict

PASS only if every mandatory condition A–E is satisfied:

`GLOBAL_FIELD_COVERAGE_FINAL_PASS`

Otherwise:
- source/semantic contradiction:
  `GLOBAL_FIELD_COVERAGE_BLOCKED_FAIL_CLOSED`
- incomplete but attackable source registry:
  `GLOBAL_FIELD_COVERAGE_PENDING_SOURCE_COMPLETION`

There is no promotion by workflow-green status alone.

## H. After PASS

Only after GLOBAL_FIELD_COVERAGE_FINAL_PASS may the lab freeze the numerical Sample/Experiment Gate
and FINAL PRE-DISCOVERY authority.

Economic outcomes remain closed until those later prospective freezes are committed.

## Firewall

prices=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
token_amounts=false
requested_amount_values=false
realized_transfer_amounts=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
