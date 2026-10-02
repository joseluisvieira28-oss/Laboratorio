# DLS PROTECTED-2025 ECONOMIC HOLDOUT — SOURCE-PIN TRANSPORT ADDENDUM V0.2

Date: 2026-10-02
Status: FROZEN TECHNICAL WIRING ONLY / ECONOMIC SCIENCE UNCHANGED
Branch: dls-field-enrichment-v01

## Problem
The original economic workflow hardcodes cancelled legacy Protected-2025 source run 36547754265.
That wiring cannot consume a later scientifically equivalent source authority.

## Allowed correction
The economic launch marker must contain one immutable SOURCE_RUN_ID.
The workflow may download only artifact:
dls-protected-2025-source-authority-a3a-v01
from that exact run.

Before any Binance market payload:
- exactly one PROTECTED_2025_SOURCE_AUTHORITY_RECEIPT_V0.2.json must exist;
- classification must equal PROTECTED_2025_SOURCE_AUTHORITY_PASS;
- source receipt firewall must prove 2025 prices/returns/PnL false;
- exactly one PROTECTED_2025_SOURCE_CLUSTER_CENSUS_V0.2.ndjson must exist.

This is source-artifact pinning only.

## Scientific authority unchanged
Exactly inherit:
- STRATEGY_TRANSLATION_FREEZE_V0.1.md
- EXECUTION_COST_FREEZE_V0.1.md
- PROTECTED_2025_ECONOMIC_HOLDOUT_IMPLEMENTATION_FREEZE_V0.1.md
- OOS_ADJUDICATION_LOCK_V0.1.json
- DIRECTION_SOURCE_AUDIT_LOCK_V0.1.json
- MEXC_API_FUTURES_FEE_AUTHORITY_RECEIPT_V0.1.json
- runner source/run_protected_2025_economic_holdout_v0_1.py

No direction, timing, serialization, market source, cost, bootstrap, horizon or gate may change.

## Launch rule
The launch marker MUST NOT be created until a completed source run is independently inspected and
its scientific classification is PROTECTED_2025_SOURCE_AUTHORITY_PASS.

A green GitHub Actions status is not sufficient.

## Firewall
Until launch marker creation:
protected_2025_market_outcomes_opened=false
protected_2026_outcomes_opened=false
post_outcome_tuning=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
trading_authority=NONE
