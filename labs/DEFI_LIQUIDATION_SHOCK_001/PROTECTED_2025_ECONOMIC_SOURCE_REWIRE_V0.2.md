# DLS PROTECTED-2025 — ECONOMIC HOLDOUT SOURCE REWIRE V0.2

Date: 2026-10-03
Status: FROZEN TECHNICAL WIRING / BEFORE 2025 MARKET OUTCOMES

## Scientific authority remains unchanged
The following frozen documents remain authoritative without modification:
- STRATEGY_TRANSLATION_FREEZE_V0.1.md
- EXECUTION_COST_FREEZE_V0.1.md
- PROTECTED_2025_ECONOMIC_HOLDOUT_IMPLEMENTATION_FREEZE_V0.1.md
- DIRECTION_SOURCE_AUDIT_LOCK_V0.1.json
- OOS_ADJUDICATION_LOCK_V0.1.json
- MEXC_API_FUTURES_FEE_AUTHORITY_RECEIPT_V0.1.json

Frozen strategy:
- source role: LIQUIDATED_COLLATERAL_SOL
- hypothesis direction: SHORT
- E = first exact UTC minute strictly after source-cluster T0
- X = E + 5 minutes
- price: Binance Spot SOLUSDT exact 1m OPEN
- gross short simple return
- primary all-in cost hurdle: 26 bps
- supportive stress: 40 bps
- non-overlap serialization unchanged
- >=500 serialized trades
- >=95% source/market coverage
- day-block bootstrap 5,000 reps
- inferential families: kamino, marginfi, save11
- all frozen PASS gates unchanged

## Source authority now satisfied
Canonical source authority:
- run: 37134450131
- artifact: 11277791628
- artifact name: dls-protected-2025-source-authority-final48-v02
- artifact ZIP SHA256: 738414881490b9232354f800893d10410d36b60f87fc2db5e5bb983e46c21ae4
- source authority receipt SHA256: 79f143c95d229b1ab8a75372d33fb48257e36a29100a5ddf15852d84ba5e8fea
- source cluster census SHA256: f89889c2b2f184e54ddd8b0ba83cfce47d75b0e5ba59c8fd863cbe8e0051717c
- classification: PROTECTED_2025_SOURCE_AUTHORITY_PASS
- 48 partitions
- 5,438 SOL clusters
- 133,089 SOL collateral liquidation events
- zero source errors
- 2025 market outcomes still closed at this freeze

## Runner binding
Economic runner:
- path: labs/DEFI_LIQUIDATION_SHOCK_001/source/run_protected_2025_economic_holdout_v0_1.py
- Git blob: 88b46b3dfa058c85d52f99cd62a14ee550a99e30

No economic code change is authorized.

## Technical change only
The old workflow referenced cancelled pre-recovery source run 36547754265.
The recovery workflow may instead download the exact PASS authority above and verify the exact receipt/census hashes before market access.

No other workflow/scientific change is allowed.

## Sequential firewall
If 2025 classification != SURVIVES_2025_ECONOMIC_HOLDOUT:
- 2026 remains CLOSED;
- no rescue/tuning;
- no live authority.

Only a genuine 2025 PASS may authorize the already-frozen 2026 final holdout.

## Firewall at freeze
protected_2025_market_outcomes_opened=false
protected_2026_outcomes_opened=false
post_outcome_tuning=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
trading_authority=NONE
