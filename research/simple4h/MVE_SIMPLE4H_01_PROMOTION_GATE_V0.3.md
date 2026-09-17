# MVE-SIMPLE4H-01 — PROMOTION GATE READY — V0.3

Date: 2026-09-17
Status: PROMOTION_GATE_READY / 2025 STILL LOCKED
Repository: joseluisvieira28-oss/Laboratorio
Branch: simple4h-recovery-v0.2

Research-only. Fail-closed. No live trading, no exchange mutation, no 2026 access, no merge to main.

## 1. Purpose

This V0.3 gate supersedes the earlier V0.2 promotion-gate draft BEFORE any 2025 outcomes were opened.

The historical SIMPLE TRADING LAB V0.1 verdict remains immutable:
- 36/36 primary cells complete
- 27 NEGATIVE_EXPECTANCY
- 9 NO_STATISTICAL_EDGE
- 0 SURVIVES_DISCOVERY

MVE-SIMPLE4H-01 is a NEW replication hypothesis using exactly seven pre-identified 4H positive-diagnostic cells.

## 2. Why V0.3 changes the draft statistical gate

The V0.2 draft inherited N >= 100 per cell from the four-year Discovery lab and also required BH-FDR q < 0.05 plus a positive moving-block-bootstrap lower bound for STRONG_CELL_PASS.

That combination is not appropriate as a universal MVE kill-switch for a one-year OOS block:
- the canonical MVE standard explicitly says p <= 0.05 is not a universal economic kill-switch;
- MVE-2 is defined as independent OOS net-positive evidence under frozen realistic costs with uncertainty reported;
- the protected 2025 sample remains unopened;
- historical annual event counts show that five of seven fixed cells normally generate roughly 56-91 trades/year, while the two EMA cells generate roughly 101-114 trades/year.

Therefore V0.3 prospectively uses N >= 50 as the minimum cell-level OOS evidence floor, while N >= 100 remains a reported high-confidence sample diagnostic. This is a pre-outcome design correction, not a rescue.

No trading rule, asset, timeframe, cost, entry, exit, stop, target, timeout, or protected period is changed.

## 3. Fixed seven-cell family

1. ST-01_DONCHIAN_BREAKOUT — BNBUSDT — 4H
2. ST-01_DONCHIAN_BREAKOUT — DOGEUSDT — 4H
3. ST-01_DONCHIAN_BREAKOUT — SOLUSDT — 4H
4. ST-01_DONCHIAN_BREAKOUT — XRPUSDT — 4H
5. ST-02_EMA_PULLBACK — SOLUSDT — 4H
6. ST-02_EMA_PULLBACK — DOGEUSDT — 4H
7. ST-03_EXTREME_MEAN_REVERSION — DOGEUSDT — 4H

No additions, removals, substitutions or post-outcome cell selection.

## 4. Economic rules

All inherited rules remain exactly as recovered in V0.2:
- Donchian: previous 20 completed bars; next-bar open; 2 x ATR14 stop; 4R target; 20-bar max hold.
- EMA Pullback: EMA20/EMA50 trend relation plus pullback/reclaim conditions; next-bar open; 1.5 x ATR14 stop; 2R target; 10-bar max hold.
- Extreme Mean Reversion: EMA20 +/- 2 x ATR14 extreme; next-bar open; 1.5 x ATR14 stop; frozen signal-bar EMA20 target; 8-bar max hold.
- one active position per cell; overlapping signals while open ignored.
- adverse gap honored; favorable target gap not improved; stop-first if intrabar ordering is unknowable.
- BASE cost = 10 bps round trip.
- STRESS cost = 14 bps round trip.
- no maker rebates.

## 5. Protected 2025 source contract

Eligible signal window:
2025-01-01T00:00:00Z <= signal < 2026-01-01T00:00:00Z

Source:
official Binance public-data USD-M Futures 1m monthly kline ZIPs + adjacent CHECKSUM sidecars.

Required assets:
BNBUSDT, DOGEUSDT, SOLUSDT, XRPUSDT.

Allowed files:
- 2024-12 only as indicator warm-up
- 2025-01 through 2025-12 as confirmation data

4H bars require exactly 240 native 1m rows.
No interpolation.
No forward fill.
Start flat at 2025-01-01.
No position triggered by a 2024 signal may enter 2025.

End-of-year censoring:
a signal is excluded prospectively if its maximum holding horizon plus deterministic time-exit would require any 2026 bar, even if an earlier stop/target might have occurred.

2026 remains forbidden.

## 6. Cell-level 2025 outputs

For each fixed cell report:
- N
- gross mean
- NET10 mean and median
- NET14 mean
- NET10 profit factor
- NET10 win rate
- SD / SE
- Student-t 95% CI
- one-sided t-test H1 mean NET10 > 0
- BH-FDR q across exactly seven cells
- 3000-rep circular moving-block bootstrap lower 95%, block length 5
- maximum drawdown on cumulative NET10 log returns
- mean R multiple
- stop / target / time-exit frequencies
- Q1/Q2/Q3/Q4 NET10 means
- positive-quarter count
- largest winning-trade share of total positive NET10
- largest positive-quarter share of total positive NET10

Classical significance is evidence strength, not a universal MVE economic kill-switch.

## 7. Prospective cell classifications

### ADEQUATE_CELL_SAMPLE
N >= 50.

### HIGH_CONFIDENCE_SAMPLE
N >= 100.
This is reported but is not required for MVE-2 family routing.

### CELL_OOS_POSITIVE
All must hold:
1. N >= 50
2. NET10 mean > 0
3. NET14 mean > 0
4. NET10 profit factor > 1.0
5. at least 2 of 4 calendar quarters have positive NET10 mean

### Concentration red flags
- largest single winning trade > 25% of total positive NET10 bps
- largest positive quarter > 60% of total positive NET10 bps

A flagged cell may remain an economic diagnostic but is not counted as a clean positive cell for Tier 2/Tier 3 routing.

### CELL_STRONG_EVIDENCE
CELL_OOS_POSITIVE, no concentration red flag, and at least one:
- BH-FDR q < 0.05 across the seven-cell family
- moving-block-bootstrap lower 95% NET10 mean > 0

This is a stronger-evidence label, not the minimum MVE-2 requirement.

## 8. Family routing

All medians below are calculated only across ADEQUATE_CELL_SAMPLE cells.

### TIER_2_PROMOTED_CANDIDATE
All must hold:
- at least 5/7 cells have N >= 50
- at least 4 clean CELL_OOS_POSITIVE cells
- clean positive cells span at least 2 distinct strategy families
- median NET14 across adequate cells > 0

### TIER_3_WATCHLIST
All must hold:
- at least 4/7 cells have N >= 50
- median NET14 across adequate cells > 0
- and either:
  - at least 2 clean CELL_OOS_POSITIVE cells spanning at least 2 strategy families; or
  - at least 3 clean CELL_OOS_POSITIVE cells total
- TIER_2 is not met

### REJECTED_STONE
- at least 5/7 cells have N >= 50
- at least 5 adequate cells have NET14 <= 0
- median NET14 across adequate cells <= 0

### NO_EDGE
- at least 5/7 cells have N >= 50
- TIER_2, TIER_3 and REJECTED_STONE are not met

### INSUFFICIENT_SAMPLE
- fewer than 5/7 cells have N >= 50 and no higher routing criterion is met

## 9. Quase-diamond boundary

QUASE_DIAMANTE is not an automatic machine output.

A human scientific review may consider QUASE_DIAMANTE only if:
- machine routing is TIER_2_PROMOTED_CANDIDATE;
- at least 2 CELL_STRONG_EVIDENCE cells exist;
- those strong cells span at least 2 strategy families;
- provenance is clean;
- 2025 is confirmed as genuinely untouched for this hypothesis;
- no fatal concentration issue exists.

Even QUASE_DIAMANTE does not authorize live trading.

## 10. Authority / implementation preflight

Recovered source package and results authority preflight:
AUTHORITY_PREFLIGHT_PASS.

Verified without protected data:
- package ZIP hash PASS
- results ZIP hash PASS
- internal authority hashes PASS
- historical closeout identity PASS
- 36/36 historical summary metrics recomputed against the ledger PASS
- 32,243 historical events verified
- 7/7 fixed cells verified
- protected 2025 opened: NO
- protected 2026 opened: NO

Runner V0.2 is protected-data-free self-test capable and fail-closed unless an explicit authorization JSON is supplied.

## 11. Required chain before one-shot outcome opening

1. PROMOTION_GATE_READY V0.3 committed.
2. Runner V0.2 and decision schema V0.2 committed.
3. Inert compile/self-test PASS.
4. Exact gate commit SHA frozen.
5. 2025 source files materialized and checksum-verified without using outcomes to change the hypothesis.
6. Source manifest SHA256 generated.
7. Explicit 2025-only authorization JSON binds:
   - MVE ID
   - exact gate commit SHA
   - exact source-manifest SHA256
   - one-shot arm token
   - 2026_authorized = false
   - live_trading_authorized = false
8. One-shot run exactly once.
9. Machine closeout.
10. Human scientific review.

Any missing link = FAIL CLOSED.

## 12. Forbidden

- no parameter sweep
- no alternate lookbacks
- no new assets
- no 1H cells
- no cell dropping
- no costs below 10 bps
- no alternate stops/targets/timeouts
- no regime filter
- no indicator stacking
- no post-outcome gate changes
- no 2026 access
- no live orders
- no exchange mutation
- no merge to main

## 13. State

PROMOTION_GATE_READY.

2025 outcomes remain unopened by this gate.
2026 remains locked.
Live trading remains unauthorized.
