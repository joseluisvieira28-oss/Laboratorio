# MVE-SIMPLE4H-01 — RECOVERY & REPLICATION FREEZE V0.2

Date: 2026-09-17
Status: SOURCE_RULE_RECOVERY_PASS / REPLICATION_READY / HOLDOUT_CLOSED
Governance: research-only; fail-closed; no live trading; no exchange mutation; no post-outcome tuning.

## Authority recovery
Original SIMPLE_TRADING_LAB_V0.1 package and original result package were recovered intact on 2026-09-16/17. The historical verdict remains immutable: 36 primary cells, 27 NEGATIVE_EXPECTANCY, 9 NO_STATISTICAL_EDGE, 0 formal survivors. 2025 and 2026 were not opened by the original closeout.

The former SOURCE_RULE_RECOVERY_BLOCKED state is resolved because the original scientific freeze, runner, 36-cell summary, event ledger and closeout are now available. No textbook/default reconstruction is authorized.

## Frozen seven-cell family
The prospective replication family is the seven previously documented 4H positive-diagnostic cells, jointly pre-registered as one family:

1. ST-01_DONCHIAN_BREAKOUT — BNBUSDT — 4H
2. ST-01_DONCHIAN_BREAKOUT — DOGEUSDT — 4H
3. ST-01_DONCHIAN_BREAKOUT — SOLUSDT — 4H
4. ST-01_DONCHIAN_BREAKOUT — XRPUSDT — 4H
5. ST-02_EMA_PULLBACK — SOLUSDT — 4H
6. ST-02_EMA_PULLBACK — DOGEUSDT — 4H
7. ST-03_EXTREME_MEAN_REVERSION — DOGEUSDT — 4H

No cell may be dropped, substituted, added, or reweighted after replication outcomes are opened. ETH Donchian 4H is not added merely because it was slightly positive at the historical 10 bps cost; it was not one of the seven frozen historical diagnostics and was negative at 14 bps stress cost.

## Exact recovered strategy rules
Rules are inherited byte-for-byte in meaning from SIMPLE_TRADING_LAB_SCIENTIFIC_FREEZE_V0.1 and simple_trading_lab_v01.py. No parameter tuning is permitted.

- Donchian Breakout: Donchian lookback 20; ATR14; stop distance 2x ATR14; target 4R; maximum hold 20 bars.
- EMA Pullback: EMA20/EMA50; ATR14; stop distance 1.5x ATR14; target 2R; maximum hold 10 bars.
- Extreme Mean Reversion: EMA20 +/- 2x ATR14 trigger geometry; ATR14; stop distance 1.5x ATR14; target is the frozen EMA20 reference; maximum hold 8 bars.
- Entry execution: next-bar open as specified by the original runner/freeze.
- Timeframe: 4H only for this replication family.
- Costs: primary 10 bps round-trip-equivalent model as encoded by the original runner; stress 14 bps. Costs may not be lowered to rescue results.

## Historical evidence / contamination record
Historical Discovery already consumed: 2021-01-01 through 2024-12-31 under SIMPLE_TRADING_LAB_V0.1.
Historical seven-cell ledger contains 2,332 events across the seven frozen cells.
Historical results are hypothesis-generating only and cannot count as independent replication evidence.

2025: UNTOUCHED by original SIMPLE_TRADING_LAB_V0.1 and remains CLOSED at this freeze.
2026: UNTOUCHED by original SIMPLE_TRADING_LAB_V0.1 and remains CLOSED/PROTECTED.

Any other lab using similar Donchian/EMA/mean-reversion geometry is not authority for this MVE and must be treated as possible contamination when selecting an independent replication source/period.

## Replication gate
Before any new outcome is opened, a separate PROMOTION_GATE_READY receipt must identify:
- exact independent source/provider and source receipts;
- exact non-overlapping period;
- proof of data availability and timestamp semantics;
- contamination audit against other Crypto Lab experiments;
- expected sample sufficiency for all seven cells/family;
- exact multiple-testing correction and promotion thresholds;
- cost model and execution semantics identical to this freeze.

No automatic opening of 2025 or 2026 is authorized by this document.

## Family adjudication requirements
Replication must evaluate all seven cells together. At minimum report N, net expectancy at 10 and 14 bps, win rate, PF or equivalent payoff ratio where definable, max drawdown, bootstrap uncertainty, temporal stability, concentration, and family-adjusted significance. A positive single asset/cell cannot rescue a failed family post hoc.

Allowed terminal states: QUASE_DIAMANTE, TIER_3_WATCHLIST, NEEDS_TESTING, BLOCKED, INSUFFICIENT_SAMPLE, NO_EDGE, NEGATIVE_EXPECTANCY, REJECTED.

## Current decision
SOURCE_RULE_RECOVERY_PASS.
MVE-SIMPLE4H-01 is REPLICATION_READY but outcomes remain CLOSED pending PROMOTION_GATE_READY.
