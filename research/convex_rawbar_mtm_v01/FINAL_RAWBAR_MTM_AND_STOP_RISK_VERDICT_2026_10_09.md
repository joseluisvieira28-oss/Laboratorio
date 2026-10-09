# BTC CONVEX — HISTORICAL RAW CANDLE MTM + STOP OVERSHOOT — SCIENTIFIC CLOSEOUT
Date 2026-10-09
**Status:** `RAW_1H_PROVENANCE_PASS__MARKED_RISK_ESTIMATE_ONLY`.
**Economic finding:** previously identified ETH/SOL/BNB basket remains locally historically profitable under the SAME fixed low-risk simulated strategy, but actual stop losses exceed planned account-risk budget on many trades and complete all-cost executable profitability remains unproven.

## 1. What was ACTUALLY tested now
- Read original frozen 2021–2025 Parent V5 historical 1h trade ledgers from GitHub Actions original canonical source artifacts 10775714534 (ETH/SOL/BNB), 10778258822 (XRP/DOGE/ADA/LINK/AVAX), 10791006099 (original Parent as third-basket benchmark). New replay reuses exactly the predeclared 0.25% and 0.50% per-position planned risk from the previous `convex-risk-v01` model, max 3 positions, total planned risk <=1%, deterministic concurrency and 10,000 USDT initial shared simulation.
- Independently downloaded **185 official USD-M Futures 1h Binance OHLCV source archives** including 60 monthly archives per coin and five daily SOL gap-fill archives. Every archive's **SHA256 matched the canonical original 2021–2025 trade-ledger provenance manifest**. All three symbols complete **43,824 contiguous 1h bars** (2021–2025), no missing hour or conflict. 6,388,796 bytes compressed source matched.
- Replayed EXACT archival trade outcomes and frozen source/simulation commission, slippage, funding totals. Marked any still-open position hourly against actual original historical bar CLOSE, minus entry commission and a modeled exit taker commission/slippage. **Interim funding path was NOT recovered**; recorded total net funding is still included in trade PnL on exit. This marked equity series is an *indicative* exposure-risk path, NOT a fully modeled account MTM.
- Reported a pessimistic same-hour LOW envelope across currently still-open assets. Within each 1h, price lows need not be simultaneous and stop exits may precede low; this is a conservative sensitivity proxy, NOT executable worst-case account DD.
- Independent 1h candle execution-consistency re-audit: original simulated entries = original 1h OPEN*(1+frozen adverse slip) to numerical precision; recorded stop exit, reversing frozen slip, lies within original same exit-bar HIGH/LOW; forced end equals final CLOSE. **All 365 BASE trade records and 366 STRESS records match with 0 candle/entry discrepancy**, not proof of exchange order fill.

## 2. Exact local historical shared-basket economics 2021–2025
Portfolio: ETHUSDT + SOLUSDT + BNBUSDT Parent V5, original 1h signals/stops, **not a newly selected independent OOS**. Source prices from original Binance; NOT a replication at MEXC.

| Audit number | Planned risk 0.25%, BASE | 0.25%, original STRESS | Planned risk 0.50%, BASE | 0.50%, original STRESS |
|---|---:|---:|---:|---:|
| Cumulative net simulated return over 5 years | +34.596090% | +33.684714% | +20.080257% | +16.949956% |
| Number of filled historical simulated positions | 365 | 366 | 221 | 223 |
| Missed historical positions due to 1% aggregate risk budget | 0 | 0 | 144 | 143 |
| Previous realised-only drawdown | -6.903543% | -7.023568% | -13.499644% | -13.825749% |
| NEW indicative hourly CLOSE MTM drawdown | **-8.828838%** | **-8.963408%** | **-16.193746%** | **-16.515670%** |
| NEW pessimistic same-hour LOW envelope | -8.893458% | -9.027920% | -16.331725% | -16.653097% |

All 43,824 1h observations processed; for 0.25% BASE, 29,548 hourly slots had at least one open position, max three simultaneously.
Run **37901455199** first rawbar SHA + MTM PASS. Technical prefreeze additional source execution-coherence checks, followed by final SUCCESS run **37901690536**, artifact **11602782725**, code/source unchanged scientifically and original risk-cash outcomes reproduced. Latest job compared every original entry price with SHA-checked Binance OHLCV and every exit against the 1h bar bound, with zero discrepancy.
Prior 13-asset risk-normalized run 37896908699 remains binding: second five-symbol basket -25.60% at 0.25% risk BASE; all13 -4.11% at 0.25% BASE, i.e. global generalization FAIL.

**New learning:** The lower-risk 0.25% model's originally reported DD of -6.90% understated hourly marked-to-close DD; hourly reconstructed estimate -8.83%, even before exact intraposition funding, real execution/latency, small lot constraints and stop-gap tails. DD remains materially reduced vs original original independent high-notional first basket 54–59% *original* mark-to-market DD, but those are different position sizing regimes and cannot be treated as equivalent experiments.
**Low envelope caveat:** -8.89% is a simplified same-hour low sensitivity among positions still open after event processing, NOT a strict lower-bound guarantee for actual realized drawdown; excludes intrabar already closed positions. High-frequency order-price events remain unknown.

## 3. Stop-risk assumption falsified by raw economic trade ledger
Original strategy hard price stop was 4%; planned counterfactual per-position budget uses 4.24% notional equivalent (4% stop plus baseline modeled 10bps taker per side and 2bps adverse slip per side). Actual source trade returns and funding frequently exceed that fixed drawdown threshold, including stop gaps.

| Parent BASE symbol | Total closed trades | Net loss worse than 4.24% notional | Worst NET trade loss (% notional) | Worst planned-R multiplier |
|---|---:|---:|---:|---:|
| ETHUSDT | 100 | 43 | -6.536018% | 1.541514 R |
| SOLUSDT | 163 | 46 | -5.285875% | 1.246669 R |
| BNBUSDT | 102 | 18 | -6.349854% | 1.497607 R |
| TOTAL | 365 | **107** | n/a | n/a |

107/365 (29.3%) exceed the planned 4.24% net loss threshold. In the stronger slippage STRESS, ETH 70/100, SOL 117/163, BNB 46/103 exceed that same **BASE planning** denominator; this is a fixed baseline benchmark, not a dynamically updated stop.
At planned 0.25% equity risk, an actual -6.536% notional loss represents about **0.3854% of equity** under that same fixed position size, before capital changes/gaps beyond sample. At planned 0.50%, about 0.7708%. **Risk budget is not a maximum-loss guarantee.**

## 4. Integrity and limits
- Original historic source files and OHLCV entry/stop range rechecked **PASS**. Original signal entry = next-bar OHLCV OPEN with assumed slip, not a contemporaneous tradable bid/ask. This is an internal **bar simulator coherence proof**, NOT live exchange quote feasibility.
- The original first-basket local PASS and second-basket FAIL persist; results are ALREADY KNOWN 2021–2025, not untouched new OOS, and 2026 first three closed shadow trades remain losses.
- Hourly CLOSE MTM uses unaccrued interim funding until final trade close and estimated exit fees/slippage; downside tails within each hour and path of collateral/margin not fully simulated. Thus **hourly MTM drawdown is indicative, not exact economic liquidation risk**.
- No leverage, orders, real money, private endpoints, wallets, account reads, exchange mutation, main merge or protected outcome reopening was used.
- **Net profitable after modeled historical transaction costs in that first basket: YES (scope-limited)**.
- **Profitable across 13 assets with same rules: NO (prior basket generalization FAIL)**.
- **Reliable recurring live profit or new independent 2026 edge: NOT PROVEN**.
- **Hard per-trade maximum loss of planned 0.25% / 0.50%: FALSE**.

## 5. Practical scientific engineering priority
1. Further reduce **true** loss budget failure: redesign the position-sizing denominator to explicitly include observed adverse stop overruns; any newly proposed higher planning haircut is an **ex-post engineering sensitivity** on this already opened data; cannot be called scientifically optimized from these trades. Do not promise 'stop always respected'.
2. Build full historical mark/funding path and orderbook/liquidity reconstruction or publicly available 1-minute/tick source for deterministic stops; record missing inputs as SOURCE_BLOCKED rather than assume a fill at an hourly OPEN.
3. Until actual economic venue fees, minimum lot/market depth and per-symbol portfolio margin are bounded, do not give a live capital GO. A five-year +34.6% total (~6.1% CAGR) is positive but not a 'money printing machine'.
4. Do not lose the macro result: universal 13-asset rule failed. Continued ETH/SOL/BNB-only investigation is justified as a historically observed *scoped phenomenon*, with selection-bias caveat; no blind expansion or 2026 re-optimization.

## Repro links
- Latest original archive/candle/exit coherence job, **SUCCESS**: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37901690536 (artifact 11602782725)
- Original archive MTM raw-bar receipt **SUCCESS**: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37901455199
- Risk-normalized all-13 portfolio historical replay **SUCCESS**: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37896908699
- Source and execution invariant freezes: `RAWBAR_MTM_PREPROBE_FREEZE_2026_10_09.md`, `TECHNICAL_FILL_CANDLE_INTEGRITY_PREFREEZE.md`.
