# TRADINGVIEW STRATEGY CENSUS V0.1 — PRE-FREEZE

Mission ID: `TVSC-001`  
Date frozen: `2026-09-23`  
Status: `SOURCE_CENSUS_FROZEN / RESEARCH_ONLY`

## Purpose

Use TradingView's public/open-source ecosystem as a hypothesis-discovery surface, never as evidence of profitability.

Popularity, views, likes, Strategy Tester output, author claims and screenshots are NOT promotion evidence. They may only motivate a prospectively frozen Crypto Lab experiment.

## Governance

Authority: CRYPTO LAB Governance V4 / Death Policy remains controlling.

Hard boundaries:
- no live trading;
- no exchange mutation;
- no wallet action;
- no paid data;
- no merge to main;
- no protected 2024/2025/2026 outcome access from this mission;
- no parameter rescue after discovery outcomes;
- no copying a failed classic-indicator implementation under a new name.

## Anti-duplication finding

The repository already contains `CLASSIC_INDICATORS_GAP_LAB_V0.1` with prospectively frozen classic families including VWAP, ADX and Bollinger Bands, plus implementation freezes for ATR, RSI, Stochastic, MACD, OBV, Ichimoku and SuperTrend.

Therefore TVSC-001 does NOT open generic RSI/MACD/SuperTrend/BB parameter searches.

## Census interpretation

The source ledger records approximate public page-view counts observed around 2026-09-23. Counts are dynamic and are used only as an adoption/popularity proxy, never as PnL evidence.

## Mechanism clusters

1. volatility compression -> expansion
2. ATR trailing/reversal trend state
3. nearest-neighbour / ML classification
4. smoothed trend baseline / Hull
5. momentum confirmation / QQE-WaveTrend
6. multi-indicator stacking
7. mean reversion
8. breakout / channel
9. market-structure heuristics
10. volume / flow confirmation

## First attack selected prospectively

`TVSQZ-001 — VOLATILITY COMPRESSION RELEASE`

Rationale:
- materially distinct from the existing Bollinger mean-reversion implementation;
- tests a causal market state (relative compression of BB inside KC) before any directional trading rule;
- exact public reference implementation and defaults are recoverable;
- can be reproduced independently from OHLCV;
- requires no paid/proprietary data;
- Discovery can be run using only 2022-2023, leaving 2024/2025/2026 sealed.

The first gate is non-directional: does squeeze release predict abnormal future realized volatility?

Only if that mechanism gate passes may the already-frozen directional momentum test be evaluated on the same Discovery block.

## Follow-up queue if scientifically distinct

After TVSQZ-001:
- `TVATR-UT-001`: UT Bot / ATR trailing-state family, subject to contamination review against existing ATR/SuperTrend freezes.
- `TVML-LOR-001`: Lorentzian-distance classifier, only with strict leakage/ablation controls and a fresh LAB_ID.
- `TVSTACK-001`: QQE + SSL + Waddah ablation study, only if each component's incremental information can be tested without parameter tuning.

No follow-up receives inherited promotion credit from TradingView popularity or from TVSQZ-001.
