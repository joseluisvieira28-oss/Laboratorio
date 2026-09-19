# BTC-OPTIONS-VRP-CRYPTA-EXP-001 — EXPLORATORY CLOSEOUT V0.1

Date: 2026-09-19
MVE: `CRYPTA-ATM30-24H-QUOTE-CARRY-001`
Canonical run: `35470799516`
Artifact ID: `10592558257`

## Verdict

**EXPLORATORY_NO_SIGNAL**

The previously failed 90-day source gate remains unchanged. This exploratory study was explicitly non-promotional and used the 68-day SOURCE_LIMITED parquet only to ask whether a prospectively frozen 30D ATM 24h short-straddle quote-carry signal was visible before acquiring executable quote sizes.

Frozen implementation:
- 08:00 UTC decision hour;
- 24h hold;
- 25–35 DTE, target 30;
- ATM strike chosen prospectively from entry underlying price;
- short one call + one put at bid;
- buy back at next-day ask;
- standard Deribit option fee model;
- no hedge;
- no mark/midpoint rescue;
- no 2025/2026 access.

Results:
- N = 54
- mean net premium return = -6.0517%
- median = -2.8271%
- positive fraction = 31.48%
- PF on net cash = 0.13767
- circular block bootstrap 95% CI for mean = [-9.4372%, -3.1405%]
- positive months = 1 / 7
- max losing streak = 6

All exploratory signal gates failed except minimum N.

## Interpretation

The relaxed source-adequacy policy did what it was intended to do: it allowed a useful test instead of discarding the source at 68 dates. The result itself is strongly negative for this exact quote-based short-straddle carry implementation.

This does not prove all BTC options VRP mechanisms are absent. It closes this exact exploratory MVE without post-outcome rescue.

Missing bid/ask sizes remain an execution/capacity blocker and are not the reason for the negative quote-PnL result: even before any size/capacity claim, the frozen quote-price implementation showed negative economics.

No promotion, live trading, wallet access, exchange mutation, protected holdout access, or merge to main is authorized.
