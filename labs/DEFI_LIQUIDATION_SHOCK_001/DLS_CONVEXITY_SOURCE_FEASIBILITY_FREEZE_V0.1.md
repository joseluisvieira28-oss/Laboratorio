# DEFI-LIQUIDATION-SHOCK-001 — CONVEXITY SOURCE FEASIBILITY FREEZE V0.1

Date: 2026-09-29
Branch: dls-convexity-source-gate-v01
Family ID: DLS-CONVEXITY-001
Status: SOURCE-FIRST / NO OPTION OUTCOMES OPENED

## Purpose

Determine whether the already-proven direction-agnostic liquidation volatility effect can be tested as an
executable delta-neutral options/convexity strategy using public/free historical data.

This is not a direction strategy and not a rescue of:
- DLS V0.2 executable breakout;
- DLS Signed Return V0.1;
- DLS Basis Dislocation V0.1.

## Required executable evidence

A future options experiment is authorized only if public/free historical data can provide, for every
candidate trade:

1. exact option instrument identity and listing/expiry metadata;
2. strike, option type and expiry known at decision time;
3. contemporaneous executable bid/ask or equivalent top-of-book quote at entry;
4. contemporaneous executable bid/ask or equivalent top-of-book quote at exit;
5. underlying/hedge market price source;
6. defensible option and hedge fee schedule/model;
7. enough temporal coverage to construct development and independent OOS without opening protected 2025/2026.

Trade prints alone are insufficient because they do not prove that the strategy could transact at those
prices or establish the spread at the required timestamp.

End-of-day implied volatility alone is insufficient.

## Preferred underlying

SOL, because the canonical DLS event population and already-proven volatility effect are strongest and
most source-complete for SOL-primary liquidation clusters.

## Temporal feasibility

Preferred existing development history:
2021-12-08 through 2023-12-31.

If SOL options did not exist in that interval, a 2024-only alternative may be considered only if:
- options existed early enough in 2024;
- public/free executable quotes exist;
- a prospective split can reserve an independent 2024 OOS;
- 2025/2026 remain unopened.

## Source classification

DLS_CONVEXITY_SOURCE_PASS:
all required executable evidence is publicly/free and historically available with enough independent time.

DLS_CONVEXITY_SOURCE_PARTIAL:
option history exists but executable quote/spread or independent temporal coverage is incomplete.

DLS_CONVEXITY_SOURCE_BLOCKED:
the free/public source set cannot support a defensible executable options test.

## Firewall

option_prices_opened=false
option_returns_opened=false
option_pnl_opened=false
market_2025_opened=false
market_2026_opened=false
paid_source=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
