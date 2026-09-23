# USORB-001 — U.S. CASH OPEN OPENING-RANGE BREAKOUT — PRE-FREEZE

Date frozen: 2026-09-23
Status: PRE_DISCOVERY_FROZEN
Governance: CRYPTO-LAB-GOVERNANCE-V4.0-DEATH-FROZEN
Production impact: NONE
Live execution: FALSE

## Economic mechanism

The U.S. equity core open at 09:30 America/New_York is an exogenous market-structure clock with a formal opening auction and concentrated cross-asset price discovery. The exact hypothesis is that, in crypto perpetuals, the first confirmed break of the 15-minute range formed during 09:30–09:45 ET contains short-horizon directional continuation information.

This is not a generic Donchian/channel test:
- the range exists only because of an externally defined market-open event;
- the range resets every U.S. cash trading day;
- the event clock is fixed prospectively and DST-aware;
- no rolling lookback, adaptive channel length, or parameter search is allowed.

## External motivation

TradingView contains multiple open-source Opening Range Breakout implementations using a fixed first-15-minute range around the U.S. market open. These scripts are hypothesis-discovery references only; their backtest claims are not evidence for Crypto Lab.

Reference examples:
- https://www.tradingview.com/script/tZtCD3TM-Opening-Range-Breakout/
- https://www.tradingview.com/script/W5O2NhV3-ORB-Key-Session-Levels-Strategy/
- https://www.tradingview.com/script/OUkUGhJn-Opening-Range-Breakout/

Official market-clock references:
- https://www.nyse.com/trade/trading-information
- https://www.nasdaq.com/market-activity/stock-market-holiday-schedule

## Anti-duplication

Known covered families:
- Donchian / trend breakout;
- geometric trendline interaction;
- VWAP;
- ATR / SuperTrend;
- generic technical-indicator families.

Material novelty here is the exogenous U.S. cash-open auction clock and session-reset range, not a new mathematical price transform.

## Firewall

Allowed now:
- public/free source acquisition;
- source QA;
- 2022–2023 Discovery;
- immutable execution receipt;
- terminal closeout if the frozen gate fails.

Forbidden:
- opening 2024, 2025 or 2026;
- changing the 15-minute range;
- changing the signal window;
- adding EMA/VWAP/volume filters;
- reversal rescue if continuation fails;
- changing holding horizon;
- winner-asset selection;
- cost reduction rescue;
- live trading;
- exchange mutation;
- merge to main.
