# BTC-CONVEX V5 — MATRIZ 15m / 30m / 1h / 4h — VEREDITO HISTÓRICO
**Data:** 2026-10-13
**Branch:** `research/btc-convex-5m-canonical-matrix-v02-2026-10-13`
**Autoridade:** RESEARCH_ONLY / NO_EXECUTION_GO / NO_OOS_CREDIT
**Protocolo PRÉ-OUTCOME:** `research/btc_convex_timeframe_matrix_20261013/NEW_SOURCE_FAMILY_V02_PREOUTCOME_FREEZE.md`, commit `b17cef1889f07518c9ced86341206793251ab437`.
**Run validado:** https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38426153613 — SUCCESS, 9/9 synthetic checks and market replay.
**Artefacto auditável:** https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38426153613/artifacts/11828479302 — `MATRIX_RESULTS.json`, publisher SHA-256 source-manifest, 8 complete trade ledgers.

## Mesma estratégia e custos, timeframes diferentes
BTCUSDT Binance USD-M historical model 2021-01-01 through 2025-12-31, 2020-11/12 warmup; all market prices from single source official 5m historical tape, resampled to UTC 15m,30m,1h,4h. SHA-256 independently matched publisher .CHECKSUM for complete months. Original V5 LONG confirmed-bar signal (RSI14 Wilder, BB20, z-score -2, vol>SMA20 and SMA200 trend, score >=3). Original stop initial -4% price, conditional nonlatched trailing 12% when profit on completed TF close >=5%, one-slot. Entry 5m opening strictly after witness of confirmed bar (TF close+5m); stop-first for ambiguous 5m candle touches and adverse-gap prices.
Each timeframe separate paper account 10,000 USDT, 20% current paper equity notional, no leverage. Fees assumed 8bps taker per side, BASE adverse slippage 2bps/side, STRESS 5bps/side, archived actual funding-rate events and 5m BTC market-price **proxy** (not actual settlement mark), no genuine Binance/MEXC executable quotes or account charges.
All percentages below use **terminal marked equity**, including one outstanding position at 2025-12-31 for 15m,30m,1h. 4h fully closed.

| TF | BASE return | STRESS return | BASE closed | BASE wins | BASE PF | BASE low-MTM DD |
|---|---:|---:|---:|---:|---:|---:|
| 15m | +4.146595% | +2.403494% | 114 | 22 (19.30%) | 1.046664 | -26.127112% |
| 30m | -0.270943% | -1.013594% | 102 | 18 (17.65%) | 0.995585 | -22.961735% |
| **1h** | **+15.074361%** | **+13.607362%** | **77** | **17 (22.08%)** | **1.265218** | **-14.852988%** |
| 4h | -5.608852% | -5.959490% | 49 | 11 (22.45%) | 0.813419 | -17.642167% |

**1h wins descriptively** on net result, drawdown and PF among the 4 fixed candidates. But 1h 5-year paper return +15.07% is only ~2.848% geometric annualized. Three biggest 1h winners account for 42.489% of gross positive closed PnL; subtraction of those winners from completed historical ledger changes closed PnL to **-1,568.28 USDT** (arithmetic not a re-run with changed exposure). Thus historical dependence on rare winning tails remains.
The 1h BASE fee drag was **-278.22 USDT**, funding `-1,154.26 USDT` (market-price-based modeled funding). The enormous funding drag is a source/model-sensitive cost, NOT evidence the source's actual mark cashflows match execution.
15m gains modest with nearly twice 1h drawdown (26.13% vs 14.85%), top3 omission `-2,786.23 USDT` closed ledger.
30m loses after expenses; 4h loses and relies on top3 winners = **69.81% of gross winner PnL**.

## Annual closed-trade NET PnL, BASE, USDT (not marked terminal annual account returns)
| TF | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| 15m | +223.51 | -1,764.65 | +526.36 | +1,973.25 | -582.72 |
| 30m | -85.57 | -1,447.29 | +337.77 | +1,506.19 | -342.11 |
| 1h | +1,083.81 | -996.77 | +349.56 | +1,889.69 | -799.14 |
| 4h | -771.40 | -607.64 | -215.66 | +865.27 | +168.53 |
No arm wins all five years. 1h and 15m each show 3/5 positive PnL exit years, 30m and 4h 2/5. Positive total driven significantly by 2024.

## Source integrity: no false parity
Verified 543,456 five-minute bars, 45,288 independent official one-hour bars (includes warmup) and 5,478 historical funding events.
The publisher CHECKSUM-matched independent official one-hour archive does **NOT** exactly equal aggregation of official five-minute bars:
- **7 of 45,288 hourly bars differ**, 6 volume fields, 2 open, 2 high, 2 low, 1 close. Some mismatches occur in multiple fields of the same bar.
- First source blocker (PR #211): 2022-06-23 19:00 UTC 5m aggregate volume 51,536.155 vs independent official 1h 51,615.158.
- Another: 2023-11-10 19:00 UTC 5m high 37,120.0 vs independent published 1h high 37,189.8.
- Exact recovered Parent 1h binary entry signal divergence over 2021–2025 was **zero**, but trailing peaks, intrabar stop events and historical fills could differ. Hence this is an **official 5m canonical reconstructed study**, NOT reproduction of official 1h history or original TradingView broker emulator.
- Original strict one-hour ALL-FIELDS parity experiment **remains SOURCE_BLOCKED**; V02 is a newly frozen source-descriptive family after two upstream source-only failures, not a retroactive pass of that original hypothesis.

## Decisions
- 15m: WEAK HISTORICAL POSITIVE BUT FRAGILE (PF 1.047, DD -26.13%, missing top3 => negative); low research priority, no GO.
- 30m: HISTORICAL FAIL under both BASE and STRESS; archive from active execution shortlist for this exact V5 specification.
- **1h: BEST RELATIVE HISTORICAL TIMEFRAME, NOT AN ECONOMIC DIAMOND.** Can preserve as Parent reference for separately frozen improved execution/source/forward; 5-year annualized ~2.85%, high sensitivity to big winners, funding model/venue execution unverified.
- 4h: HISTORICAL FAIL both scenarios and right-tail concentration 69.81%; de-prioritize.
- Historical 2021–2025 was previously investigated and is contaminated for independent OOS validation. Historical rank is **descriptive only**. No 2026 holdout opened.
- No trading, orders, accounts, private endpoints, wallets, spend, Render, main merge or parameters modified because of economic outcomes.
**Final:** 1h > 15m > 30m > 4h on this single matched reconstructed five-year test; ZERO execution authority.
