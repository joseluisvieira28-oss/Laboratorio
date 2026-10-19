# CRYPTO LAB — CONVEX V07 FINAL: ORIGINAL 3-YEAR ECONOMIC-RISK CALIBRATION CLOSEOUT

Date: 2026-10-19 UTC, branch research/convex-v07-economic-risk-calibration-2026-10-19.

## Actual completed proofs, not indicators / cherry-picked outcomes

Source protocol PRE_ARTIFACT_RECALIBRATION_FREEZE_2026_10_19.md committed BEFORE re-opening 2023–25 original trade CSVs in this run.

- [GitHub Actions #39214547899](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39214547899): **SUCCESS** on Ubuntu, Windows, and original source financial census. Hermetic synthetic tests 12 per OS; 2 assets x 2 original BASE/STRESS ledgers fully audited.
- Canonical original GitHub Actions run **38432883246**; SOLUSDT 1h 84 original BASE / 84 original STRESS closes and BNBUSDT 4h 28 BASE / 28 STRESS; original SHA256/source-count/manifest receipts saved under V07 research-only artifact.
- All per-trade decompositions verify original net = price PnL - original entry fee - exit fee + original funding; dates/declared original annual PnL/streaks/PF reconcile. No after-outcome indicator or stop parameter edits, no price replay and no market/exchange HTTP. Source original Binance 5m+funding with 8 bps model taker fees/side and 2 bps BASE/5 bps STRESS slip per side.
- Historical OOS: **NONE**. The full 2023–25 aggregate outcomes were known *before* this V07, so V07 financial gates are retrospective discipline, not new independent test.

## Baseline by asset, only CLOSED trade cashflows in USDT

| Measure | SOL 1h BASE | BNB 4h BASE |
|---|---:|---:|
| Original closed trades | 84 | 28 |
| Original net closed | **+5,930.2102** | **+2,737.7928** |
| 2023 original closed | +5,203.0555 | **-28.8851** |
| 2024 original closed | +1,304.8725 | +1,761.3637 |
| 2025 original closed | **-577.7179** | +1,005.3142 |
| Top 3 winners / total NET closed | **76.4629%** | **82.3521%** |
| Original 5m low-mark max modeled DD | **-12.26737%** | **-7.95943%** |
| Original closed net after additional 40bp roundtrip per entry notional | **+4,988.6725** | **+2,483.1844** |
| STRESS original closed net after additional 40bp roundtrip | **+4,883.9303** | **+2,451.2441** |
| Original extra adverse roundtrip cost to statically wipe original CLOSED net cashflow | 251.94 bps | 430.12 bps |

**Critical nuance:** break-even cost 251.94/430.12 bps is aggregate static original-entry-notional weighted, not an actual quoted exchange spread, not prediction, not price walk at a stop. We do not infer any future potential from high implied historical fee cushion. Because original trade cashflows are held fixed, the scenarios ignore changed exits, reentries, account equity and market liquidity.

## Frozen research risk pre-screen = BOTH REJECTED

The preregistered identical V07 screen required:
- >=60 closed trades;
- original BASE **no calendar year of negative closed PnL**;
- BASE and STRESS net closed still positive with +40bps extra costs;
- 3 largest winners <60% of original net closed profits;
- original 5min low-mark DD at least -10% or better.
These thresholds are transparent *research triage preferences*, not laws of statistical significance nor proof of financial safety. All survivors would still lack broker native stop ACK, cross-venue 2023 actual execution, statistically independent 2026 OOS, fees/lot/tick-point-in-time and real fill data, hence no LIVE GO.

**SOLUSDT 1h reasons:** NEGATIVE_CALENDAR_YEAR_2025; TOP_THREE_WINNERS_GE_60PCT_OF_NET_CLOSED_PROFIT; MODELED_LOW_DRAWDOWN_WORSE_THAN_10PCT.

**BNBUSDT 4h reasons:** LESS_THAN_60_CLOSED_TRADES; NEGATIVE_CALENDAR_YEAR_2023; TOP_THREE_WINNERS_GE_60PCT_OF_NET_CLOSED_PROFIT.

**Final V07 = NO_HISTORICAL_RISK_TRIAGE_SURVIVORS.** This is stronger than a generic "fees too high" explanation. Neither candidate qualifies for *new resource-intensive economic promotion* under the frozen screen. Do not loosen science to rescue one. This does **NOT** imply their population expected return is zero or negative; only that the known selected historical sample is fragile.

## Risk ladder, fixed in pre-read freeze

Exactly 0.25x, 0.50x and 1.00x original quantity, corresponding to static 5%,10%,20% modeled-equity notional scenarios. Cashflows/extra charges were scaled linearly while signal and account equity evolution remain frozen. This is a **STATIC RISK SENSITIVITY**, not a new result or actual exchange order. Scaling down a strategy with a negative 2025 does not change the sign of its 2025 expected cashflow. BNB historical min lot/tick and SOL/BNB account concentration risk remain unresolved. No sizing tier was "optimized" based on observed data or promoted to live.

## Abort post-outcome optimization; productive next steps

1. Existing Windows Telegram CONVEX collectors may CONTINUE strictly signal-only / read-only, recording NEW pre-outcome immutable prospective events, timestamped source venue BBO/L2/funding + contract size/tick/lot source/fee source and actual signal, with no orders or purported automatic stop protection. Avoid opening the protected 2026 scientific holdout.
2. A future candidate family/parameterization must explain an **economic mechanism distinct from hindsight pattern matching**, preregistered before opening its own future outcomes; retain all failed candidates. If SOL1h/BNB4h are continued as *unpromoted monitoring only*, their original params stay frozen; do NOT retune original V5 and re-use 2023–25 as OOS.
3. Independently verify actual broker-native stop risk acknowledgment and reconciliation in a separate sandbox/authorized protocol; original nonlatched trailing is NOT live-safe. Raw OKX 2 paired entry/exit L2 archives remain private; no real global trade portfolio can be inferred from 2 cases.
4. If genuinely independent forward sample confirms repeatable positive after-cost outcomes with realistic fills and aggregate exposure constraints, reconvene a NEW promotion decision against a **newly frozen, independently valid** scientific protocol. No such forward evidence obtained in V07.

**Scientific final: research hygiene PASS, original historic positive cashflows remain but regime-dependent; ZERO historically robust promotions; NO MACHINE OF MONEY PROVEN; NO LIVE GO; no merge to main, no Render, no exchange/wallet/account mutating actions and no cost.**
