# DLS PROTECTED-2025 ECONOMIC HOLDOUT — PRELAUNCH IMPLEMENTATION BINDING V0.1

Date: 2026-10-02
Status: FROZEN BEFORE PROTECTED-2025 MARKET OUTCOME ACCESS
Branch: dls-field-enrichment-v01

Scientific authority:
- STRATEGY_TRANSLATION_FREEZE_V0.1.md
- EXECUTION_COST_FREEZE_V0.1.md
- PROTECTED_2025_ECONOMIC_HOLDOUT_IMPLEMENTATION_FREEZE_V0.1.md
- OOS_ADJUDICATION_LOCK_V0.1.json = SURVIVES_OOS
- DIRECTION_SOURCE_AUDIT_LOCK_V0.1.json = DIRECTION_SOURCE_ROLE_AUDIT_PASS
- MEXC_API_FUTURES_FEE_AUTHORITY_RECEIPT_V0.1.json = PASS

Bound runner:
- path: labs/DEFI_LIQUIDATION_SHOCK_001/source/run_protected_2025_economic_holdout_v0_1.py
- Git blob SHA: 88b46b3dfa058c85d52f99cd62a14ee550a99e30

Conformance:
- target = SOL collateral source clusters only
- direction = SHORT only
- E = first exact UTC minute boundary strictly after T0
- X = E + 5 minutes
- market research field = Binance Spot SOLUSDT 1m OPEN
- primary all-in hurdle = 26 bps
- supportive hard stress = 40 bps
- no leverage
- non-overlap serialization frozen
- source/market coverage gate = 95%
- serialized N gate = 500
- day-block bootstrap = 5,000
- inferential families = kamino, marginfi, save11
- 2026 remains closed unless 2025 survives

Workflow source pin is resolved only from the launch marker after a real PROTECTED_2025_SOURCE_AUTHORITY_PASS artifact exists.

At creation of this binding:
protected_2025_market_outcomes_opened=false
protected_2026_outcomes_opened=false
post_outcome_tuning=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
trading_authority=NONE
