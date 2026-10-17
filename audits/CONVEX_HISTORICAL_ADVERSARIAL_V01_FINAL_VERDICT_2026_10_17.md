# CRYPTO LAB — CONVEX HISTORICAL ADVERSARIAL V0.1 — FROZEN FINAL VERDICT

Date: 17 October 2026 UTC. Original artifacts only. Run [39019452293](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39019452293) = **SUCCESS** on original GitHub Actions artifacts (source runs 38432883246 and 38435206427). Synthetic integrity tests PASS; original per-trade ledger accounting, original source-publisher hash count metadata (112 original source files for each asset), original trade count and annual PnL reconciliation PASS. New machine: `research/convex_historical_adversarial_v01/ledger_attack.py`.

## Exact scientific classification

- **HISTORICAL_CANDIDACY_SURVIVES** for all three **in already observed 2023-25 Binance-model original BASE/STRESS runs**. No independent OOS, no MEXC/Kraken/OKX executable venue fill, no sealed 2026 holdout, no positive live performance evidence.
- **RISK/PORTFOLIO CLAIMS NOT VALIDATED**: +5% activation + 12% trail may weaken stop again (original V5), 4% initial stop cannot guarantee max realized loss, no exchange stop ACK. V07/V11/V12 Telegram observers do not place stops.
- **COST SENSITIVITY STATIC PASS (not rerun)** for additional +6/+12/+20/+40bps on the **same original closed trades**; no leverage, compounding or stop reinterpretation. These do NOT prove that a costlier venue yields the same trades.
- **TRUE INDEPENDENT ECONOMIC EDGE NOT YET CERTIFIED / NO LIVE GO**. Absolutely no auto-trading authorization, no merging main, no protected 2026 history opening, no parameter fitting after results.

## Six original immutable ledgers — PnL in USDT per independent 10k paper portfolio

| Candidate | cost | closed trades | closed original net USDT | terminal marked return % (model) | closed top3 removed USDT (static) | worst nonwinning streak |
|---|---|---:|---:|---:|---:|---:|
| SOL 1h | BASE | 84 | +5,930.210 | +59.3883% | +1,395.797 | 11 |
| SOL 1h | STRESS | 84 | +5,821.940 | +58.2955% | +1,305.210 | 11 |
| BNB 4h | BASE | 28 | +2,737.793 | +27.3779% | +483.163 | 6 |
| BNB 4h | STRESS | 28 | +2,705.531 | +27.0553% | +458.773 | 6 |
| SOL 5m | BASE | 182 | +5,961.905 | +59.9872% | +780.831 | 13 |
| SOL 5m | STRESS | 182 | +5,741.913 | +57.7727% | +598.727 | 13 |

**BASE closed-year PnL breakdown:**

| candidate | 2023 (trades, net USDT) | 2024 (trades, net USDT) | 2025 (trades, net USDT) |
|---|---|---|---|
| SOL 1h | 39, +5,203.056 | 23, +1,304.873 | 22, **-577.718** |
| BNB 4h | 5, **-28.885** | 17, +1,761.364 | 6, +1,005.314 |
| SOL 5m | 66, +5,617.574 | 64, **-130.919** | 52, +475.250 |

**IMPORTANT:** SOL1h derives ~87.7% of its three-year closed profit from 2023 (same reported static cash); SOL5m derives ~94.2%. These are **in-sample regime-concentration warnings**, not future-return forecasts. BNB4h has only 5 historical closes in 2023 and 28 altogether; its strong original model PF is statistically sample limited.

**Profit concentration**: top three original BASE winners account for approximately 76.5% (SOL1h), 82.4% (BNB4h) and 86.9% (SOL5m) of the entire **net closed gains** (ratio top3 wins / net closed PnL, NOT share of gross winners). Static removed-top3 balance still positive in each original ledger; this does NOT mean a real portfolio would preserve that residual after those trades were absent.

## Adversarial static extra round-trip costs — BASE ORIGINAL CLOSED OPERATIONS (USD)

| candidate | +0 bps | +6bps | +12bps | +20bps | +40bps |
|---|---:|---:|---:|---:|---:|
| SOL 1h | +5,930.210 | +5,788.980 | +5,647.749 | +5,459.441 | +4,988.672 |
| BNB 4h | +2,737.793 | +2,699.602 | +2,661.410 | +2,610.489 | +2,483.184 |
| SOL 5m | +5,961.905 | +5,643.984 | +5,326.063 | +4,902.169 | +3,842.433 |

This is an EXACT static financial subtraction from original per-trade entry notionals, not a price rerun; the comparison does not account for variable funding, slippage, stop amendments, spread changes, maker queue, account reinvestment or position re-entry effects. It demonstrates the **existing trade cashflows aren't mathematically erased merely by modest extra static fees**; it does not validate actual cross-venue economics.

## Critical newly documented overlapping exposure (BASE original interval intersections)

- SOL1h versus SOL5m: **79 interval pairs**, 70 unique SOL1h trades overlapping 65 unique SOL5m trades. Thus **70/84 SOL1h original trades overlapped at least one SOL5m original trade** (83.3%). Independent paper accounts may take simultaneous SOL risk; real single-symbol margin/stop is NOT independent. No simple return sum.
- SOL1h versus BNB4h: 39 interval pairs, 39 distinct SOL1h / 18 BNB4h.
- SOL5m versus BNB4h: 73 interval pairs, 72 distinct SOL5m / 26 BNB4h.
- Maximum **3 simultaneous exposures** across the three independent modeled trade ledgers; this does NOT prove that a single real account could hold them or reproduce the original returns. Physical SOL position aggregation and stop conflicts need new future portfolio design and tests.

## Historical venue availability falsifiers — independently published (no market PnL outcomes)

- [Kraken official product contract specs](https://support.kraken.com/ch/articles/4844359082772-linear-multi-collateral-derivatives-contract-specifications) reports **PF_SOLUSD launched 2022-03-22**, **PF_BNBUSD launched 2023-11-22**. Therefore full 2023 Binance BNB4h signals cannot automatically be re-labelled as contemporaneous Kraken PF_BNBUSD executions before its launch; these are missing venue exposures, not zero-return trades.
- Kraken publicly documents [futures market candle history](https://docs.kraken.com/api/docs/futures-api/charts/candles) and [aggregated spreads/funding/market analytics](https://docs.kraken.com/api/docs/futures-api/charts/market-analytics), but this CI intentionally did **not** fetch 2023-25 venue quote history. Kraken recent trade endpoint limited to 7 days does NOT by itself disprove separate historical order event/analytics coverage.
- [OKX historical download portal](https://www.okx.com/en-sg/historical-data) advertises historical high-resolution L2 from March 2023, historical funding from March 2022 and candles from July 2023. Availability, per-symbol archive integrity, license and exact frozen signal-date book alignments NOT yet proven. Its historical data T&Cs restrict intended use; check license before redistribution/commercial research.
- MEXC 12 *October 13, 2026* public book samples on 100 USDT theoretical notional from PR #216 are unrelated to 2023-25 exact entry quotes, and cannot be pasted as old fills.
- Futures/API fees are product/venue/account specific; PR #243 public base rate comparison 16 bps taker/taker MEXC vs 10 Kraken/OKX is only a **hypothesis** before all-in venue quote/funding risk.

## What is eliminated now

1. **Claim that SOL 1h, SOL 5m, BNB 4h are three independent portfolio alpha slots: FALSIFIED** in time-overlap sense. Do not share one SOL physical position with unrelated stop ownership by assigning each lane separate PnL.
2. **Claim that original historical strategy returns are stable in all three years: FALSIFIED**. Each strategy has a negative closed-PnL calendar year.
3. **Claim that the +6bps Kraken fee gap gives proven +6bps actual executed strategy advantage: NOT PROVEN** due to venue history, quotes and funding gaps. Maker improvement particularly needs a separately frozen fill model.
4. **Claim that extra +40bps static friction automatically kills all historical closed trade cashflows: FALSIFIED AS STATIC ACCOUNTING ONLY**. Does not imply live tradability.
5. **Claim that fixing original nonlatched trailing is free: UNSUPPORTED**. Any monotonic stop, time exit or TP is a distinct prospective branch. The already completed PR #224 early-half/monotonic tests beat neither original parent and showed risk/return tradeoff.

## Economic/operator decision

Keep all original V5 monitoring signal-only; **no live capital deployment.** Prioritize SOL1h as research hypothesis (84 closes) and BNB4h as contrasting asset (28 closes), plus SOL5m **secondary monitoring** because much of its information overlaps SOL1h, it churns more and its net closed cashflow is 2023-heavy. Do not make live leverage/profitability promises from a three-year historical paper ledger.

Before any real automatic execution, independently qualify synchronized venue-specific BBO and funding around genuine signals, and a new pre-outcome frozen risk policy with native broker stop ACK/reconciliation. An independent 2026 holdout may be used only under its original protected authority after strategy and venue-policy freeze. This audit is historical **not** independently OOS.

**FINAL V0.1 STATUS: SIX LEDGERS RECONCILED / HISTORICAL-ONLY CANDIDATES SURVIVE / REGIME DEPENDENCE + OVERLAP PROVEN / NO INDEPENDENT EDGE / NO LIVE GO.**
