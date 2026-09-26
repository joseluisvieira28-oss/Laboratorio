# DEFI-LIQUIDATION-SHOCK-001 — MARKET DATA MAPPING SAMPLE ADEQUACY ADDENDUM V0.2

Date: 2026-09-27
Status: FROZEN / SOURCE-ONLY / OUTCOME-BLIND

This addendum refines MARKET_DATA_MAPPING_REGISTRY_FREEZE_V0.1.md before any market outcome is opened.

## Correction

A target with no defensible direct market is allowed to remain:

`MARKET_MAPPING_UNAVAILABLE`

even if it contributed to the original source-only cluster census.

It MUST NOT be replaced by a correlated proxy.

The scientific requirement is not that every source target be mapped. The requirement is that the
prospectively retained directly mapped population still satisfies the already frozen independent-sample gates.

## Post-mapping source sample gate

Using source cluster counts only, before price payloads:

### Primary pooled population
Retained directly mapped clusters must satisfy:
- Discovery >= 1,000
- OOS >= 500

Otherwise:
`MARKET_DATA_MAPPING_SAMPLE_BLOCKED`

### Protocol/class subgroup authority

For every subgroup previously marked `INFERENTIAL_DISCOVERY_AND_OOS`:
- retained mapped Discovery >= 200
- retained mapped OOS >= 100

If below, that subgroup is downgraded prospectively to:
`DESCRIPTIVE_ONLY_AFTER_MARKET_MAPPING`

This downgrade is source-only and occurs before outcomes.

For `EXTERNAL_CONFIRMATORY_INFERENTIAL`:
- retained mapped OOS >= 200
- otherwise downgrade to descriptive-only.

Subgroup downgrade does NOT by itself block the pooled experiment.

### No threshold rescue

Thresholds are unchanged from SOURCE_SAMPLE_GATE_FREEZE_V0.1.md.
They may not be lowered to rescue mapping coverage.

## Registry validation

MARKET_DATA_MAPPING_REGISTRY_PASS requires:
- one deterministic row per target;
- all claimed direct mappings source-defensible;
- unavailable targets explicitly evidenced;
- retained directly mapped primary Discovery/OOS counts satisfy 1,000 / 500;
- all source contradictions fail closed.

The validation receipt must report:
- original cluster counts;
- retained mapped counts;
- excluded unavailable counts;
- source-only subgroup status after mapping.

## Route feasibility

Later MARKET_DATA_SOURCE_PASS repeats primary mapped-sample adequacy after route metadata probing.
A claimed direct mapping whose venue/product identity contradicts source metadata is a conflict, not a silent exclusion.

## Firewall

archive_payload_downloaded=false
candles_opened=false
prices_opened=false
returns_computed=false
pnl_computed=false
economic_outcomes_opened=false
protected_2025_2026_opened=false
post_outcome_tuning=false
live_trading=false
merge_main=false
