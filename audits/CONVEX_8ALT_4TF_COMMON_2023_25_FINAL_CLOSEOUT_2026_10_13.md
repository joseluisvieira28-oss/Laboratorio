# CRYPTO LAB — CONVEX V5 — ALL 8 ALTCOINS × 4 TIMEFRAMES — COMMON 2023–2025 CLOSEOUT
**Dated:** 2026-10-13 UTC. **STATUS: DESCRIPTIVE HISTORICAL SCIENCE ONLY / NO INDEPENDENT OOS / NO TRADING AUTHORITY.**
Frozen BEFORE new 3-year outcomes: `research/convex_8alt_common_2023_25/PRE_OUTCOME_3YEAR_FREEZE.md`, commit `7dec5e0f46d34744366ec28edf1712aca95f0aa9`.
Reasons for new common period rather than mixing incomparable windows: 2021–25 8-alt study 38430847396 had SOL/XRP SOURCE_BLOCKED due two verified 2022 full-days gaps; 1m corroboration also missing. Common period is first complete calendar year AFTER source gaps 2023-01-01 through 2025-12-31, with complete Nov/Dec 2022 warmup for all eight. 2021–25 original source blocks remain unmodified.

## Evidence
- Independent GitHub Actions run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38432883246 — **SUCCESS**, 3 window/invariant tests PASS, all **8 symbol CI jobs SUCCESS**.
- Independent complete consolidation of **64/64 fixed cells**, source manifest and per-trade CSV exact coverage: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38433418250 — **SUCCESS**.
- Consolidation artifact JSON + CSV: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38433418250/artifacts/11831602875.
- Every symbol: official Binance USDM market 5m and independently published 1h archived market 2022-11..2025-12: **333,216 5m bars**, **27,768 independently official 1h bars**, **3,288 public archived historical funding observations**; every ZIP passed official publisher checksum. All 8 1h binary entry signal disagreement counts 0, although 4 or 5 official 1h price/volume archive bars per symbol differ from 5m reconstructed source, disclosed. All strategies consistently use 5m canonical source.
- Each symbol 15m/30m/1h/4h signals from original recovered BTC V5 indicator code: confirmed bar trend + extreme pullback + RSI or volume score (identical SMA200 candle count, not equal physical timeframe). Original initial -4% stop, NONLATCHED 12%-from-running-peak trail triggered on completed TF close >=+5%; one slot, next 5m bar open **strictly after** the TF signal witness. All positions 20% of current independently simulated equity notional, 1x, initial 10,000 USDT, no leverage; no exchange marketable order/fill reconstruction. BASE 8bps taker fee each side+2bps adverse slip each side; STRESS 8bps+5bps. Archived per-settlement funding rates multiplied by 5m market price **proxy**, NOT exact Binance futures mark, MEXC funding, actual user fees or verified fill.

## All 64 historical combinations 2023–2025
**Each cell below: BASE % / STRESS % terminal marked 3y net return**, fees, assumed slippage and funding model included, initial 10,000 USDT. A positive value in a single 3y historical backtest is NOT demonstrated independent OOS edge.

| Coin | 15 min | 30 min | 1 hour | 4 hours |
|---|---:|---:|---:|---:|
| **ETH** | -0.01 / -0.58 | -2.81 / -4.10 | **+18.77 / +18.34** | -1.46 / -1.70 |
| **BNB** | +11.04 / +10.49 | +19.67 / +18.17 | +10.88 / +10.51 | **+27.38 / +27.06** |
| **SOL** | +21.48 / +19.04 | +24.67 / +22.50 | **+59.39 / +58.30** | +35.90 / +35.42 |
| **XRP** | +18.43 / +14.95 | +6.97 / +6.13 | +4.48 / +3.93 | -16.15 / -16.35 |
| **DOGE** | +8.45 / +7.20 | +3.08 / +2.20 | -12.82 / -13.45 | **+15.66 / +15.26** |
| **ADA** | -13.30 / -14.17 | +2.07 / +1.28 | +2.04 / +1.41 | -2.63 / -2.97 |
| **LINK** | -26.64 / -28.63 | -0.93 / -2.52 | -13.97 / -14.50 | -10.29 / -10.55 |
| **AVAX** | -6.50 / -7.56 | -9.96 / -10.71 | -4.98 / -9.17 | +1.93 / +1.67 |

## Fixed 3y completed BASE variant diagnostic table, select economically relevant ones
| Symbol/TF | Trades closed | PF BASE | 5m-low model drawdown | Positive exit years /3 | Gross net marked % | Closed net PnL after STATIC removal of top 3 winners |
|---|---:|---:|---:|---:|---:|---:|
| **SOL 1h** | **84** | **1.8240** | **-12.27%** | 2/3 | **+59.39%** | **+1,395.80 USDT** |
| **BNB 4h** | **28** | **2.8942** | **-7.96%** | 2/3 | **+27.38%** | **+483.16 USDT** |
| SOL 4h | 44 | 2.0253 | -10.45% | 3/3 | +35.90% | -526.02 USDT |
| ETH 1h | 47 | 1.5396 | -11.06% | 3/3 | +18.77% | -975.14 USDT |
| BNB 30m | 51 | 1.6009 | -10.40% | 2/3 | +19.67% | +61.77 USDT |
| DOGE 4h | 44 | 1.5405 | -10.61% | 3/3 | +15.66% | -757.13 USDT |
| XRP 15m | 124 | 1.1924 | -22.76% | 2/3 | +18.43% | -2,867.81 USDT |
Top-3 subtraction is **just arithmetic on frozen closed trade ledger, not a causal portfolio rerun**. Marked terminal equity may include an open position and does not equal the sum of closed trade PnL; do not conflate. 3y annualized implied model CAGR SOL 1h ~16.8% and BNB 4h ~8.4%, entirely retrospective and not a forecast. A 10% annual income claim is unsupported without live venue fees/capital/drawdown/robust confidence.

## Science verdict
1. **SOL 1h research priority #1** within common 2023–25: best matched historical net result after BASE and STRESS friction, PF 1.824, 84 trades and +1395.80 USDT static top3-removed closed PnL. However only 2/3 positive exit years, sample already seen in related family and fills/mark unknown. Not a micro-live authorization.
2. **BNB 4h research priority #2 / BEST modeled risk-efficiency:** highest PF 2.894 of highlighted cases, lowest modeled drawdown -7.96%, and static top3-removed ledger positive +483.16 USDT. 28 closed events over three years (small sample), non-OOS. Could be a distinct source of study, NOT an independently proven profitable mechanism.
3. SOL 4h / ETH 1h viable descriptive controls but top3-removed closed PnL negative, suggesting right-tail dependence. DOGE 4h too concentrated; BNB 30m relatively moderate with +61.77 static residual.
4. XRP 15m and ADA 30m etc: headline gains too fragile relative to DD and top3 concentration; all LINK timeframes negative, AVAX mostly negative/weak; these exact historical specifications low priority.
5. 2021–25 BNB 1h +52.23% vs 4h +40.96%; 2023–25 BNB 1h +10.88% vs 4h +27.38%; rankings CHANGED with sample. Similarly DOGE 30m +42.93% over five years, just +3.08% on 2023–25 common period. This is **regime sensitivity**, not broad, steady cash generation. Unchanged Source Parent and five-year frozen results retained. Do not select a timeframe by the higher observed sample alone.

## Next legitimate work
First-order economic source/venue validation for SOL 1h and BNB 4h **as hypotheses, not trades**: exact dated historical funding settlements with true mark price (not 5m market open), public bid/ask depth and venue contract min/lot at T0, actual per-account taker schedule only with user's separate permission, independent out-of-sample prospective point-in-time continuous collector with preregistered matched capital and constraints. Avoid reoptimizing original 4%/12%/+5%, after-the-fact tweaked timeframe rules or opening locked 2026 holdout. No scheduled bot collector or true forward introduced by these retrospective Actions. No main merge, orders, exchange mutation, wallet, Render or spend.

**Final: 8/8 SYMBOL SOURCE_PASS FOR COMMON 2023–25 / 64/64 HISTORICAL CASES / SOL 1H HIGHEST 3Y MODEL RETURN / BNB 4H MOST DEFENSIVE MODEL PF/DD / OOS AND EXECUTION NOT PROVEN / TRADING_AUTHORITY NONE.**
