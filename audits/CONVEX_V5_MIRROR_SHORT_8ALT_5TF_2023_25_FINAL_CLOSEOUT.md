# CRYPTO LAB — CONVEX V5 EXACT SHORT MIRROR: EIGHT ALTS × FIVE TIMEFRAMES — FINAL 2023–2025 CLOSEOUT
**Date:** 2026-10-13 UTC.
**Status:** SOURCE_AND_SYNTHETIC_GATES_PASS; ALL 80/80 HISTORICAL SHORT ARMS; RESEARCH ONLY; INDEPENDENT_OOS=NONE; LIVE_TRADING_AUTHORITY=NONE.
**Pre-outcome frozen protocol:** `research/convex_short_mirror_8alt_5tf_20261013/PRE_OUTCOME_FREEZE.md`, commit `71b8711247ab9cbe43e38e5af8ff65cf8f9670c0`, before reading any mirrored SHORT economic history.
**Original producer:** https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38437548175 — **SUCCESS**, 7 synthetic short invariants PASS, 8/8 symbol source+model jobs SUCCESS.
**Audit 80 cases:** https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38437814725 — **SUCCESS**, independently reconciles exact original eight receipts, all 80 full-period arms, source provenance, 80 cases including losers and underlying exit trade CSVs.
**Master JSON + CSV artifact:** https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38437814725/artifacts/11832579860.

## Hypothesis and economics
The Parent BTC-CONVEX V5 originally tests LONG ONLY. This research creates an exact-symmetric **hypothetical SHORT-only** inverse: below SMA200, upper 20-bar Bollinger/Z>+2 price extreme, RSI14 Wilder >70 OR high volume (same 3/4 total score and original BB+Z redundancy). An upside correction inside a bearish regime is a SHORT opportunity. Each TF uses 200 period bars, so physical SMA200 horizon differs (5m 16h40, 4h 800h).
The mirrored initial SHORT stop is +4% over slip-adjusted entry; trailing buys-to-cover at <= min(initial stop, running price LOW×1.12), active on closed candle SHORT profit >=5%, NONLATCHED otherwise. No take-profit/time expiry and one slot. Stop-first if 5m HIGH reaches stop, at actual observed 5m OPEN on adverse upward gap. Sell short at strictly next 5m bar OPEN after 1-second completed-TF-signal witness (for 5m: signal 5m close -> entry second-next 5m opening). Adverse simulated SHORT slippage lowers entry and raises cover. All source/target calculations are causal in the OHLC proxy model, but 5m cannot certify intra-bar fill chronology.
Every independent simulated arm starts at 10k USDT with 20% current equity SHORT notional, 1x. BASE 8bps taker fee each side +2bps adverse slip each side; STRESS same fee +5bps adverse slip each side. Public actual Binance USD-M historical funding rates applied to SHORT as **PLUS qty × contemporaneous 5m market OPEN × rate** (opposite LONG sign); this is NOT exact Binance settlement mark, true user effective MEXC costs or real traded fills/borrowing/margin proof.
Public Binance USD-M official checksum-verified monthly archives 2022-11–2025-12: for EACH asset 333,216 5m bars, 27,768 independently archived official 1h bars (audit only), 3,288 archived funding events. Price/volume revisions between 5m aggregation and official independent 1h archive not silently assumed identical; 5m canonical chosen prior to outcomes. Original SOL/XRP historical 2022 Feb+Apr missing-source problems are outside this frozen common economic window; 2026 protected holdout never opened.

## FULL 8×5 BASE SHORT comparison
Terminal marked equity after modeled fees/slippage/funding over THREE years; % cumulative, not yearly. Every corresponding STRESS case was also computed and archived (80 total).

| Coin | SHORT 5m | SHORT 15m | SHORT 30m | SHORT 1h | SHORT 4h |
|---|---:|---:|---:|---:|---:|
| ETH | -17.78 | -17.42 | -17.22 | -18.13 | **+7.43** |
| BNB | **-27.64** | -19.61 | -17.42 | -8.25 | +0.35* |
| SOL | **-22.95** | -16.17 | -4.10 | -6.09 | -15.36 |
| XRP | **+8.92** | +2.94* | -11.58 | -4.45 | -5.14 |
| DOGE | +4.55 | -20.94 | -3.49 | **+22.20** | **+20.81** |
| ADA | **+16.68** | +5.84 | +7.23 | +1.73* | +9.48 |
| LINK | -11.37 | -9.55 | -2.17 | -3.61 | **+12.17** |
| AVAX | **+18.03** | +7.13 | +10.40 | +12.46 | **+21.15** |
*BNB4h, XRP15m, ADA1h have positive marked result but closed-trade PF<1; outstanding open/unrealized paper mark can explain discrepancy, so never classify solely by a positive headline return.

## Matched high-interest SHORT results, BASE/STRESS cumulative over 2023–25
| Asset / TF | BASE | STRESS | Closed BASE | PF BASE | Worst modeled 5m-high SHORT DD | Positive closed years | Closed PnL AFTER static top3 net winners subtraction |
|---|---:|---:|---:|---:|---:|---:|---:|
| **DOGE 1h SHORT** | **+22.2016%** | **+21.4069%** | **87** | 1.3762 | **-8.9203%** | **3/3** | **+129.79 USDT** |
| **AVAX 4h SHORT** | **+21.1520%** | **+20.7291%** | **46** | **1.7122** | **-8.4123%** | 2/3 | **+108.25 USDT** |
| **DOGE 4h SHORT** | **+20.8128%** | **+20.4174%** | 43 | **1.7350** | -8.7712% | **1/3** | **+225.70 USDT** |
| AVAX 5m SHORT | +18.0308% | +14.8138% | 212 | 1.1339 | -25.2490% | 2/3 | **-917.31 USDT** |
| ADA 5m SHORT | +16.6797% | +13.3519% | 171 | 1.1391 | -18.2296% | 2/3 | **-1140.89 USDT** |
| LINK 4h SHORT | +12.1709% | +11.8785% | 35 | 1.5173 | -8.6905% | 2/3 | -315.10 USDT |
| XRP 5m SHORT | +8.9215% | +4.9433% | 132 | 1.0686 | -12.0476% | 2/3 | -1700.19 USDT |
Top3 deletion = STATIC accounting change on the already-closed ledger, NOT an executable causal rerun, not a valid portfolio with resized/reentered positions, and not a defensible new OOS sample. Some final marked equity also carries an unclosed position.

## 5m SAME-COIN retrospective LONG vs SHORT comparison (same 2023–25, different strategy direction)
| Coin | Parent LONG 5m BASE | Mirrored SHORT 5m BASE | Descriptive conclusion |
|---|---:|---:|---|
| ETH | +7.00% | -17.78% | LONG preferred historically |
| BNB | +17.56% | -27.64% | LONG superior historically |
| SOL | **+59.99%** | **-22.95%** | LONG vastly superior historically |
| XRP | +12.10% | +8.92% | both positive, SHORT weaker |
| DOGE | +4.08% | +4.55% | both weak; neither 5m PF above 1.04 |
| ADA | -24.16% | +16.68% | SHORT positive but top3 sensitive |
| LINK | -7.02% | -11.37% | both fail |
| AVAX | -22.65% | +18.03% | SHORT positive but 5m DD -25.25% and top3 sensitive |
DO NOT combine the independent LONG and SHORT hypothetical equity curves as a portfolio or turn hindsight into a "direction selector"; no pre-entry causal direction rule or shared margin/capital execution exists. Observation cannot guarantee 2026/27 inversion.

## Scientific verdict / priorities
- **Best SHORT historical controls for new independent source+OOS work:** DOGE 1h for 3/3 positive years and 87 trades; AVAX 4h for 46 trades, PF 1.712, DD -8.41%, and positive static top3 winner residual; DOGE 4h PF 1.735 but annual consistency only 1/3.
- **Native SHORT 5m mostly poor economics:** AVAX +18.03 and ADA +16.68 survive BASE/STRESS but PF only ~1.13, severe modeled drawdowns, closed PnL becomes negative after static removal of top3; XRP weak, DOGE very weak. SOL and BNB SHORT 5m strongly lose while LONG 5m previously gained. LINK and ETH SHORT 5m lose.
- This is **not fast 5-minute scalp** despite 5m signals: old initial 4% stop, huge conditional 12% trailing, no short max holding; futures carries funding risk and potentially unlimited loss during adverse exchange outages/gaps.
- Any use of actual shortable venue order book, borrow/collateral, minimum contract size, actual perp settlement mark and fee tier still unproven; positive returns here are only model-based historic observations on already-studied periods. Multiple-timeframe x symbol testing 80 arms increases false-positive risk.
- Next legitimate step: distinct frozen pre-event matched OOS and real funding+bid/ask source evidence; compare against corresponding LONG controls using same capital/venue without after-outcome winner selection. Existing SOL 1h LONG and BNB 4h LONG research priorities should not be abandoned from speculative mirrored SHORT historical wins.
**END VERDICT: 80/80 HISTORICAL ARMS COMPLETE; 15/40 BASE+STRESS HISTORICAL SHORT ARMS POSITIVE PF>1; NO CERTIFIED ECONOMIC EDGE; NO MICRO-LIVE GO; PARENT AND MAIN UNTOUCHED.**
