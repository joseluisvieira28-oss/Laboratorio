# Crypto Lab — CONVEX V5 MULTI-ALT 2021–2025 × 15m/30m/1h/4h — CLOSEOUT
**2026-10-13. SCIENCE ONLY. NO LIVE TRADING GO.**
Pre-outcome frozen protocol: `research/convex_multialt_4tf_20261013/PRE_OUTCOME_PROTOCOL.md`, commit `83730eed7b8521f42d4568159a39cac6a4988dea`.
Eight assets predeclared, no omissions: ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT, DOGEUSDT, ADAUSDT, LINKUSDT, AVAXUSDT.
Eight-arm cost and timeframe model per asset: 15m/30m/1h/4h × BASE/STRESS, fixed 2021-01–2025-12. Original recovered Quant Trailing V5 long Parent exactly as BTC V02: SMA200 trend, BB20 extreme correction, Wilder RSI14 or volume, 4% initial stop, 12% nonlatched trail activated at 5% completed timeframe close; next 5m after signal open, independent 10k USDT paper account, 20% paper notional at entry and no leverage. Fee model BASE 8bps taker/side + 2bps adverse slip/side, STRESS 8bps taker/side + 5bps slip/side. Historical public Binance USDM 5m market tapes (single canonical feed), public funding rate with **market 5m-price proxy** not verified exact mark; no bid/ask executable evidence.

## Audits & exact evidentiary status
- Original run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38430847396 — **overall workflow failure because SOL/XRP fail SOURCE gate**, not because strategies lost. All 5 frozen synthetic invariants PASS, six symbol sub-jobs SUCCESS.
- Consolidation from immutable source artifacts only: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38432232740 — **SUCCESS**; reconciled all **64 predeclared cells**, **48 economic results** for six symbols and **16 SOURCE_BLOCKED** cells for SOL/XRP, never relabel as FAIL. Master artifact: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38432232740/artifacts/11831506602.
- Six completed symbols: original publisher checksum-verified all 62 monthly 5m/1h market archives and all 60 funding months each; **543,456 5m**, **45,288 independently official 1h** including warmup and **5,478 funding observations** per symbol. Differences between archival official 1h and 5m reconstruction (6–8 historic hourly bars per alt) all counted; **no 1h binary entry-signal disagreements** in the completed six.
- SOL/XRP: original 5m history **542,016 vs required 543,456** 5m bars each. Dedicated checksum-verified source-only forensic https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38431909963 found identical missing 5m intervals 2022-02-26T00:00 through 2022-03-01T00:00 (864 5m bars) and 2022-04-01T00:00 through 2022-04-03T00:00 (576 bars). Second independent public Binance 1m source-only forensic https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38432492282 confirmed **zero 1m observations** in both corresponding windows, for both symbols. Therefore original 2021–25 SOL/XRP outcomes remain **SOURCE_BLOCKED**, not numerically comparable; do not invent missing prices or optimize a partial five-year sample.

## After modeled fees, slippage and funding: 2021–2025 net terminal marked % — BASE / STRESS
| Coin | 15m | 30m | 1h | 4h |
|---|---:|---:|---:|---:|
| ETH | +8.72 / +7.27 | -3.52 / -5.33 | **+28.61 / +27.63** | -4.95 / -5.41 |
| BNB | +6.79 / +4.71 | **+47.23 / +43.27** | **+52.23 / +51.01** | **+40.96 / +40.27** |
| SOL | SOURCE_BLOCKED | SOURCE_BLOCKED | SOURCE_BLOCKED | SOURCE_BLOCKED |
| XRP | SOURCE_BLOCKED | SOURCE_BLOCKED | SOURCE_BLOCKED | SOURCE_BLOCKED |
| DOGE | +3.47 / -1.46 | **+42.93 / +40.47** | -23.67 / -24.66 | +5.69 / +5.02 |
| ADA | -23.71 / -26.98 | +12.43 / +8.83 | -12.55 / -13.52 | -5.72 / -6.53 |
| LINK | -46.54 / -49.13 | -19.53 / -22.63 | -24.13 / -25.03 | -14.23 / -14.62 |
| AVAX | -0.81 / +3.21* | -2.63 / -4.85 | -7.78 / -12.37 | -10.93 / -11.37 |
*AVAX 15m STRESS positive despite BASE negative due to different path/slot outcomes. NOT a reliable improvement with higher costs; flag as model fragility.

## Most informative BASE historical arm diagnostics (all 2021–25)
| Coin/TF | Closed trades | Profit factor | Model DD (5m low MTM) | Closed-positive calendar years/5 | End mark return | Static sum of closed PnL if 3 largest winners removed |
|---|---:|---:|---:|---:|---:|---:|
| **BNB 4h** | 58 | **2.1265** | **-8.75%** | 3/5 | +40.96% | **+1601.14 USDT** |
| **BNB 1h** | 100 | 1.6131 | -17.74% | 3/5 | +52.23% | +153.97 USDT |
| **BNB 30m** | 125 | 1.4797 | -15.49% | 3/5 | +47.23% | +988.21 USDT |
| DOGE 30m | 223 | 1.2301 | -18.73% | 3/5 | +42.93% | -494.11 USDT |
| ETH 1h | 98 | 1.3909 | -13.74% | 4/5 | +28.61% | -529.51 USDT |
| ADA 30m | 202 | 1.0735 | -27.00% | 3/5 | +12.43% | -3223.68 USDT |
Static top3 omissions are **NOT** causal reruns/reallocation, only concentration gauges. Any positive 5y CAGR remains well under genuine annual 10% gain target for most cases, and all depend on a model lacking executable real-world venue proof.

## Research verdict
- **PRIORITY #1 descriptive: BNB 4h**, lower drawdown, PF above 2.1 and static remaining closed PnL positive after removing top3; requires new untouched prospective data and actual funding settlement/venue feasibility before any economic promotion.
- **Priority #2 BNB 30m and BNB 1h**, higher returns but worse risk profile than 4h. Same coin/regime correlation; they are not independent economic advantages.
- **DOGE 30m**, strong historical sample but subtracting top3 profits makes closed PnL negative. More fragile.
- **ETH 1h**, positive 4/5 exit years and lower DD but dependent on top3 winners, remain research only.
- ADA 30m too weak relative to drawdown; other ADA TF, all LINK, original AVAX BASE TF, ETH 30m/4h, DOGE 1h and BNB 15m weak (not efficient priority) — archive/deprioritize exact fixed setups.
- SOL XRP: NOT DEAD, **SOURCE_BLOCKED** 2021–25. Distinct preregistered *common 2023–25* eight-asset follow-up in separate branch `research/convex-8alt-common-2023-25-2026-10-13`; does not retroactively rescue five-year test.
- All these years and families have prior observation/selection exposure, **no independent OOS**, no forward collector, no MEXC min/orderbook/mark/fill, no real-executable edge. No live trading, orders, account, wallets, external spend, merge main, Render or protected 2026 holdout.

**Final 5y study: SIX ECONOMIC SYMBOLS COMPLETE / TWO SOURCE_BLOCKED / ALL 64 CASES ACCOUNTED / BNB 4H BEST RISK/TAIL DESCRIPTIVE / NO LIVE GO.**
