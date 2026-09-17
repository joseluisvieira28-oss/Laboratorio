# MVE-SIMPLE4H-01 — 2025 ONE-SHOT COHORT AUTHORITY — V0.1

Date: 2026-09-17
Status: PROSPECTIVE_FROZEN / DATA_ACCESS_AUTHORIZED / 2026_FORBIDDEN
Branch: simple4h-recovery-v0.2

## Identity
This is a NEW MVE replication. It does not change the historical SIMPLE TRADING LAB V0.1 verdict (27 NEGATIVE_EXPECTANCY, 9 NO_STATISTICAL_EDGE, 0 survivors).

## Protected cohort authorized
Exactly 2025-01-01T00:00:00Z inclusive through 2026-01-01T00:00:00Z exclusive.
Market type must match the recovered parent authority: Binance USD-M Futures native 1m klines.
Universe is fixed to the six parent assets only: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, but outcomes are computed only for the seven frozen cells below.
2026 market data is forbidden.

## Seven frozen cells
1. ST-01 Donchian Breakout — BNBUSDT — 4H
2. ST-01 Donchian Breakout — DOGEUSDT — 4H
3. ST-01 Donchian Breakout — SOLUSDT — 4H
4. ST-01 Donchian Breakout — XRPUSDT — 4H
5. ST-02 EMA Pullback — SOLUSDT — 4H
6. ST-02 EMA Pullback — DOGEUSDT — 4H
7. ST-03 Extreme Mean Reversion — DOGEUSDT — 4H

No cell may be added, removed, replaced, promoted alone, or retuned after 2025 outcomes are opened.

## Inherited execution rules
Exact recovered SIMPLE TRADING LAB V0.1 rules apply without modification: completed-bar signals; next-bar OPEN entry; one active position per cell; signals during a position ignored; conservative intrabar stop-before-target convention; Donchian 20 / ATR14 / 2 ATR stop / 4R target / 20-bar maximum hold; EMA20/EMA50 pullback / ATR14 / 1.5 ATR stop / 2R target / 10-bar maximum hold; Extreme MR EMA20 +/- 2 ATR14 / 1.5 ATR stop / frozen signal-bar EMA20 target / 8-bar maximum hold. 4H bars require exactly 240 native 1m observations. No interpolation or forward fill.

## Costs
BASE = 10 bps round trip per completed trade.
STRESS = 14 bps round trip per completed trade.
No rebates and no cost reduction are allowed.

## Frozen family decision rule
All seven cells are evaluated together. Individual cell results are diagnostics only.
Family PASS requires ALL of:
- equal-cell-weighted mean NET10 > 0;
- equal-cell-weighted mean NET14 > 0;
- pooled trade-level NET10 profit factor > 1;
- every leave-one-cell-out equal-cell-weighted NET10 mean > 0;
- no single winning trade contributes 50% or more of total positive NET10 PnL.

Uncertainty and cell-level N, expectancy, PF, drawdown and win rate must be reported. Classical p<=0.05 is not a universal kill switch under MVE V0.1 and is not used to select cells. Negative economics are never waived.

PASS -> MVE-2 OOS_POSITIVE only; no live trading. Next stage may only be shadow/paper readiness.
FAIL -> MVE_CLOSED_NO_EDGE under this hypothesis ID. Do not retune, isolate a winning cell, lower costs, or open 2026 to rescue it.
DATA/TECHNICAL FAILURE -> preserve as such; repair only source/technical defects without changing economics.

## Authorization
User explicitly authorized proceeding on 2026-09-17 after the prospective seven-cell recovery freeze. This authority is limited to the 2025 cohort above and research-only one-shot evaluation. It does not authorize 2026 access, exchange mutation, orders, leverage, capital allocation, alerts/webhooks, live trading, or merge to main.