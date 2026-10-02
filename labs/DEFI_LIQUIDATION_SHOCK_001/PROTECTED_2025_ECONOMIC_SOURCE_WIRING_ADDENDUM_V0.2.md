# DLS PROTECTED-2025 ECONOMIC HOLDOUT — SOURCE WIRING ADDENDUM V0.2

Date: 2026-10-02
Status: TECHNICAL WIRING ONLY / SCIENCE FROZEN

Problem:
The original workflow dls-protected-2025-economic-holdout-v01.yml is hardcoded to cancelled source run
36547754265. It cannot consume the recovered Protected-2025 source authority even if that authority PASSes.

Scientific authority remains unchanged:
- STRATEGY_TRANSLATION_FREEZE_V0.1.md
- EXECUTION_COST_FREEZE_V0.1.md
- PROTECTED_2025_ECONOMIC_HOLDOUT_IMPLEMENTATION_FREEZE_V0.1.md
- OOS_ADJUDICATION_LOCK_V0.1.json
- DIRECTION_SOURCE_AUDIT_LOCK_V0.1.json
- MEXC_API_FUTURES_FEE_AUTHORITY_RECEIPT_V0.1.json

Frozen economic runner:
- path: labs/DEFI_LIQUIDATION_SHOCK_001/source/run_protected_2025_economic_holdout_v0_1.py
- Git blob: 88b46b3dfa058c85d52f99cd62a14ee550a99e30

V0.2 wiring may only:
1. read SOURCE_RUN_ID from a launch marker;
2. download artifact dls-protected-2025-source-authority-v03-hybrid from that exact run;
3. fail closed unless PROTECTED_2025_SOURCE_AUTHORITY_RECEIPT_V0.2.json classification is
   PROTECTED_2025_SOURCE_AUTHORITY_PASS with all market-outcome firewalls false;
4. verify the frozen economic runner Git blob;
5. execute the frozen runner with the same OOS lock, direction lock and fee authority.

No strategy parameter, cost, direction, horizon, serialization rule, bootstrap, price source or gate may change.
2026 remains closed unless 2025 classification is SURVIVES_2025_ECONOMIC_HOLDOUT.

No live trading/orders/wallets/exchange mutation/main merge.
Trading authority: NONE.
