# CONVEX V5 NATIVE 5m — ALL EIGHT ALTS / COMMON 2023–2025 — FINAL SCIENTIFIC CLOSEOUT
**Date: 2026-10-13 UTC**
Authority: RESEARCH ONLY; no trading, no 2026 holdout, no exchange/account/wallet/private API, main unchanged.
Parent-freeze source: `research/convex_8alt_5m_common_20261013/PRE_OUTCOME_FREEZE.md` committed **252bf24d143775fd66ebf85faf082b83fe2dd45d** BEFORE 5m economic results.
Source historical run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38435206427 — **SUCCESS**, four offline synthetic causal tests PASS, eight independent symbol modeling jobs SUCCESS.
Independent read-only ledger consolidation run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38435478036 — **SUCCESS (attempt 2)**. The initial attempt started while DOGE producer was still writing its artifact and failed closed with EIGHT_SOURCES_REQUIRED:DOGE; retry after all eight original jobs completed passed using exact *same* immutable run, no rerun of market economics.
Master JSON/CSV: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38435478036/artifacts/11833106063. Full per-asset 8 original producer artifacts under 38435206427 with checksummed source manifests and BASE/STRESS trade CSV.

## Scope, execution assumptions, provenance
- Frozen assets: **ETH BNB SOL XRP DOGE ADA LINK AVAX**, one complete homogeneous economic window **2023-01-01..2025-12-31**, warmup **2022-11/12**. Official Binance USD-M futures 5m historical source from publisher ZIP with exact .CHECKSUM SHA256 for all 38 market months and 36 funding months per asset; each symbol has 333,216 5m candles, 27,768 independent published 1h candles (audited only), and 3,288 archived funding observations. Four or five independent source price/volume 1h bars differ per symbol, all source discrepancies included; **0 independent 1h entry-signal boolean disagreements** across all 8. Historical source gaps from SOL/XRP Feb/Apr 2022 are OUTSIDE this common-window 2023–25 study; original 2021–25 comparison remains blocked for those symbols.
- Same recovered Quant Trailing V5 LONG Parent score (RSI14 Wilder, 20-bar Z<-2, BB20 below 2 sigma, volume above 20-bar mean; >=3/4 + price>SMA200); **200 × 5m = 16h40 SMA trend, NOT the 1h/4h regime horizon**. No retuned indicator parameters or cherry-picked assets.
- Confirmed 5m signal after close, 1 second witness, next strictly later 5m opening hypothetical entry at **second next** 5m bar open, not impossible same closing price fill. Only one active trade. Original initial -4% price stop, nonlatched conditional 12%-from-peak trailing when completed 5m close >=+5% entry, otherwise initial stop. No TP, no imposed maximum hold; 5m OHLC conservative stop-first and adverse gap.
- Each separate paper account 10,000 USDT, 20% current equity nominal exposure, 1x no leverage. BASE taker fee **8bps per side** + assumed adverse slippage **2bps per side**; STRESS same taker fee + **5bps** adverse slippage per side. Public archived historical funding rate cashflow uses contemporaneous **5m market open PROXY for settlement mark**, not real funding mark or authenticated MEXC fills/fees/order book/contract minimums. Modelled returns are not actual realized exchange returns.

## Matched native 5m after-cost historical economics
Every percentage below is cumulative **TERMINAL MARKED ACCOUNT EQUITY RETURN** across 2023-2025, one 10,000 USDT hypothetical account per symbol; may include an open position at end. DD is model worst observed 5m-low MTM, not exchange liquidation or gap-worst bound.

| Symbol | BASE net % | STRESS net % | Closed trades BASE | PF BASE | DD BASE % | BASE positive exit years /3 | BASE closed PnL after STATIC top3 winner subtraction USDT |
|---|---:|---:|---:|---:|---:|---:|---:|
| **SOL** | **+59.9872** | **+57.7727** | **182** | **1.3423** | **-15.6424** | 2 | **+780.83** |
| **BNB** | **+17.5568** | **+15.9200** | 72 | 1.3449 | -15.1724 | **3** | -317.82 |
| XRP | +12.0952 | +10.8976 | 147 | 1.1109 | -26.9059 | 2 | -3427.94 |
| ETH | +6.9999 | +6.2759 | 91 | 1.1077 | -27.7371 | 2 | -2366.01 |
| DOGE | +4.0808 | +1.8134 | 183 | 1.0320 | -17.5173 | 1 | -2793.12 |
| LINK | -7.0169 | -8.2253 | 177 | 0.9422 | -20.9785 | 1 | -3026.66 |
| AVAX | -22.6502 | -24.5320 | 223 | 0.8414 | -33.8928 | 1 | -4627.63 |
| ADA | -24.1564 | -25.8365 | 193 | 0.8201 | -34.7232 | 1 | -5628.04 |

All **16/16** cases have complete sources, modeled results and trade ledgers. Five of eight positive in BASE and STRESS; three lose both. Important: five positive results among eight already-observed candidates do not establish multiplicity-adjusted statistical significance.
BASE funding cashflows vary by asset: SOL **-523.88 USDT**, BNB **+276.15 USDT**, ETH **-616.84 USDT**, XRP **-540.57 USDT**, DOGE **-534.74 USDT**, LINK **-581.74 USDT**, AVAX **-387.77 USDT**, ADA **-501.10 USDT**; variation depends on historical funded positions and an **imperfect settlement-price proxy**. BASE fees e.g. SOL -856.21, BNB -254.20, ETH -310.92 USDT. This is not proof of exchange-realized funding credits or optimal 5m execution.

## Fair cross-timeframe 2023–25 interpretation (all same 10k paper equity, costs and market window, but different SMA200 physical spans)
| Symbol | Native 5m BASE | Best from prior fixed 15m/30m/1h/4h matrix BASE | Relative interpretation |
|---|---:|---:|---|
| SOL | +59.99% | 1h **+59.39%** | 5m slightly higher return but 1h had **higher PF 1.824, lower DD -12.27%**, fewer trades 84 vs 182; **1h remains risk-adjusted research priority** |
| BNB | +17.56% | 4h **+27.38%** | 4h PF **2.894**, DD **-7.96%** vs 5m PF 1.345, DD -15.17%; 5m not better |
| XRP | +12.10% | 15m **+18.43%** | 5m worse after-cost return, weak PF 1.111 |
| ETH | +7.00% | 1h **+18.77%** | 1h PF 1.540 and DD -11.06% vs 5m PF1.108, DD -27.74%; 5m weak |
| DOGE | +4.08% | 4h **+15.66%** | 5m PF only 1.032; fragile / one positive exit year |
| ADA | -24.16% | 30m +2.07% | native 5m strong historical negative |
| LINK | -7.02% | 30m -0.93% | no attractive timeframe demonstrated |
| AVAX | -22.65% | 4h +1.93% | native 5m strong historical negative |
These timeframes have non-identical physical MA/RSI horizons despite matching candle counts, so do NOT claim a rigorously controlled "only speed changed" effect. Post-outcome ranking is descriptive, not out-of-sample model choice.

## Scientific decision
- Preserve **SOL 1h** as priority alpha research family and **BNB 4h** as defensive model profile. SOL 5m is a noteworthy independent timeframe hypothesis but NOT a justified promotion: near-identical retrospective cumulative performance to SOL 1h with **worse modeled drawdown and lower profit factor**, **twice as many closed trades**, substantially larger fee bill, and source/venue/alpha OOS unresolved. If capacity is limited, de-prioritize native 5m live execution engineering.
- BNB 5m positive but weaker than BNB 4h, also static top3-winner-minus closed PnL negative. XRP/ETH/DOGE 5m positive with fragile profitability and top3 sensitivity; low priority; LINK/ADA/AVAX 5m hist FAIL under both costs. This statement is limited to *exact frozen variant*, not asset direction predictions.
- This is **NOT conventional 5m scalping**: original stop 4%, trailing 12% and no max holding mean positions can persist across many 5m bars. It tests signals at 5m frequency using Parent long-trend capture mechanics, not fixed small TP/SL quick exits. Fees/taker spread and one additional 5m bar of causal entry delay remain very material.
- **Verdict: MODEL PASS / 16-CASE COMPLETE / RESEARCH POSITIVE SOME / ECONOMIC EDGE NOT PROVEN / 2026 HOLDOUT SEALED / NO LIVE GO.**
