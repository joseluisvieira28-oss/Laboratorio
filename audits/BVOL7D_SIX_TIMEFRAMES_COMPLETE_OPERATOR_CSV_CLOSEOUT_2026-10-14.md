# BVOL7D × BTCUSDT — complete six-timeframe operator CSV forensic closeout
Date: 2026-10-14 UTC. PR #221. SCIENCE ONLY. No orders, spending, authenticated exchange calls, main merge, protected internal 2026 holdout opening or parameter rescue.
STATE: 4H/1D POSITIVE HISTORICAL STATIC BASE+STRESS; 5M/15M/30M/1H BASE FAIL; NO CERTIFIED OOS / NO REAL VENUE EDGE / NO LIVE GO.

## Scientific chronology
- Pre-outcome *intake-grid freeze*: research/tradingview_diamond_hunter_v01/BVOL7D_MULTI_TF_EXPLORATORY_INTAKE_FREEZE_2026-10-14.md, Git commit d14e81d23f34b606d85b6638297501fd83e5740a, created before the five new CSVs arrived. Predeclared requested 5m, 15m, 30m, 4h; 1h was already seen. Operator additionally supplied a 1D file: report it transparently as UNPLANNED / EXPLORATORY, not cherry-picked independent confirmatory evidence.
- Source: original exlux Pine v5 and screenshots sent earlier by operator. Five new raw TradingView trade-ledger CSVs supplied by operator. Raw author code, exchange source bars and operator market CSVs NOT copied to public repository. Exact raw Pine .pine bytes and compile receipt absent.
- Screenshots previously showed 1 BTC fixed quantity, 1,000,000 USDT starting virtual capital, zero commission, zero slippage, infinite margin settings, Binance BTCUSDT chart, Coinbase BTCUSD and BitMEX BVOL7D point-in-time external signal sources.
- Read CSV as utf-8-sig, group entry/exit rows by Número da negociação, exclude any Saída where Date == Abertura (open position). Every closed trade is LONG, entry/exit qty=1 BTC, price delta times quantity exactly reconciles published PnL within 0.01 USDT per trade. Infer timeframes from mode of elapsed timestamp minutes / duration bars. 4h has 322/325 exact 240m ratios and three anomalous durations; all other TFs exact. This is a source-integrity qualifier to investigate, not grounds to invent missing candles.

## EVERY source file; SHA256 (raw CSV bytes)
| Inferred TF | suffix | sha256 | closed | coverage first entry → last closed exit |
|---|---|---|---:|---|
| 5m | 837cf | f8738e4fc16a1b1d7c050e88c254d859dcd1400b27c2d2797adfd5b04bbb94e1 | 64 | 2026-08-03 14:25 → 2026-09-18 11:45 |
| 15m | 169b6 | ff5081ff7c899a696010a10afdc7d4beceab8b63e3bc953c7500b9940e101596 | 196 | 2026-03-01 16:15 → 2026-09-19 19:15 |
| 30m | 678f6 | 0197a46b812c5f63990e45cc303201859958d64a015ac9aaf8d3f0b81ff2078e | 382 | 2025-01-02 05:00 → 2026-09-20 02:30 |
| 1h benchmark | 76e19 | 0ad68c94c28e4068a77f7043fc7a23d358ee8eb39ce65abe84bcec9f28f9dea6 | 335 | 2024-01-03 08:00 → 2026-09-20 09:00 |
| 4h | 231d1 | 10ce1ee37cb1b080793215c742f8537594584351ab483ca32086c4f5551e7357 | 325 | 2017-08-29 16:00 → 2026-09-15 04:00 |
| 1D extra exploratory | 48951 | 12ad50496e9f4a452564d1a805bffbe4dca4b3921ae82492236f7107fc192d3d | **49 CLOSED + 1 OPEN** | 2017-11-22 → last CLOSED exit 2026-05-23; open LONG since 2026-08-20 |

## Frozen-ledger net cost scenario
All rows fixed; **NO dynamic rerun**, no additional simulated fills, no matched date windows, no exchange maker-tier or funding proof. Compute each closed entry/exit leg notional = |quantity × price|; charges BOTH legs. BASE = 8bps taker fee + 2bps assumed adverse slip **per leg**; STRESS = 8bps +5bps **per leg**. Illus. low = 2bps +2bps **per leg**, not authenticated fee tier. Fees in supplied TradingView reports were zero.
| TF | N closed | original gross USD | PF gross | BASE static USD | STRESS static USD | lower-cost illustrative USD | BE fee+slip bps/leg |
|---|---:|---:|---:|---:|---:|---:|---:|
| 5m | 64 | +7,350.47 | 1.709 | **−2,186.07** | −5,047.03 | +3,535.86 | 7.708 |
| 15m | 196 | **−859.03** | 0.984 | **−28,104.71** | −36,278.41 | −11,757.30 | −0.315 |
| 30m | 382 | +15,117.46 | 1.104 | **−53,321.42** | −73,853.08 | −12,258.09 | 2.209 |
| 1h known | 335 | +44,760.06 | 1.259 | **−8,689.35** | −24,724.17 | +23,380.30 | 8.374 |
| **4h** | 325 | **+71,451.69** | **1.379** | **+44,884.36** | **+36,914.17** | +60,824.76 | 26.895 |
| **1D EXTRA** | **49 closed** | **+96,903.38** | **2.422** | **+92,344.01** | **+90,976.19** | +95,079.63 | 212.537 |
Initial portfolio is 1m USDT in ALL cases. Thus static full-series BASE 4h return is +4.488% over approximately nine years, 1D +9.234% over approx 8.5 years, not annual profits; cannot compare these percentages to 5m's 46-day sample or multiply by leverage.
1D open trade #50 **is NOT a realized exit**. Entry 2026-08-20, export marks open PnL +14,079.22 and marked cumulative +110,982.60; the 49 CLOSED cumulative is +96,903.38. Only closed two-leg notional included in static cost sensitivity; unrealized carry/funding/protection untested.

## Critical falsification beyond headline returns
- Different available histories: 5m ~46 days; 15m ~202 days; 30m ~626 days; 1h ~991 days; 4h ~9 years; 1D ~8.5 years. **Never rank raw overall PnL or trade frequencies as matched comparable performance.** Monthly/archive limits/source freshness require validation.
- Observed trade arrival rates over interval first→last CLOSED: 5m ~9.76 trades/week; 15m ~6.79; 30m ~4.27; 1h ~2.37; **4h ~0.69**; **1D ~0.11**. Rates conditional on export coverage and no proof full-market bars. The two positive after-cost histories are the SLOWER variants, not a fast income machine.
- Top3 winners by frozen closed ledger: 5m +11,993.82 vs total +7,350.47; 15m +19,730.73 vs total −859.03; 30m +24,022.33 vs +15,117.46; 1h +46,203.07 vs +44,760.06; **4h +51,535.20 vs +71,451.69**; **1D +95,371.45 vs +96,903.38**. After removing three profits AND associated BASE fees for those three transactions from unchanged rest of ledger, 4h **−6,338.35 USDT**, 1D **−2,698.12 USDT**; static omission is NOT causal portfolio rerun.
- 4H year 2024 +34,637 gross / +29,535 BASE; 2025 −17,456 gross / **−25,470 BASE**; 2026 through September +2,351.96 gross / **−1,459.55 BASE**. Entire 2025–2026 4H static BASE **−26,929.07**. 4H 2024–2026 combined BASE only **+2,605.76**, compared to full-series +44,884.36; strongest performance heavily depends on older historical regimes, including 2021.
- 1D BASE 2024 +54,837; 2025 **−6,981**; 2026 closed **−7,311**, despite one open marked profit. 1D 2025–2026 BASE **−14,292.13**. Max adverse excursion 4h −14.13% of position and 1D −23.50%; there is NO standing protective stop in pasted original Pine. Hypothetical leveraged execution would be dangerous.
- 4H CSV has three elapsed-time/bar-count mismatches: trade 2 (20h/4 bars=5h), 28 (~244.14m/bar), 62 (~245.52m/bar). This could reflect gaps or historical bar differences; do not label exact source parity PASS.
- All intraday exports' last recorded entries cluster around **September 18, 2026**, while operator exported October 14. Could simply be no qualifying signals, limited chart coverage, or stale BitMEX volatility index series. CSV alone cannot determine which. Investigate BVOL7D freshest actual update versus chart Oct13/14; `request.security()` defaults `gaps_off` and can forward-fill stale external data. Source freshness and point-in-time availability remain UNVERIFIED.

## Economic/scientific judgment
- 5m, 15m, 30m, 1h: ORIGINAL SIMULATOR variants FAIL BASE and STRESS on supplied export, 15m loses with zero friction.
- 4h: **DESCRIPTIVE historical cost-survivor**, not disposable 'palha'; note entire 2017–2026 history, 2025+ loss, top-3 reliance after fees, 4h source time anomalies, no stops/mark funding and very low frequency. No certified net edge, no real executable PnL, no independent OOS.
- 1D extra: DESCRIPTIVE slow historical cost-survivor; unrequested extra/timeframe search is not independent science; 49 closed, ~0.11/week, +1 open only marked, 2025/26 weak and extreme winner concentration. No live eligibility.
- No different parameter/timeframe choice derived here may be represented as pre-registered successful confirmatory selection; this is still exploratory, and all 2026 candidate results have been viewed.

## Next concrete source-first gates (without user passwords or costs)
1. Ask operator to show one chart screenshot each of 4H and 1D with symbol/timeframe visible, inputs and latest BVOL7D observations on Oct 14. Chart end timestamp, chart visible date coverage and whether the BVOL7D security series has updated since 2026-09-18.
2. Seek BitMEX legally accessible, timestamp-verifiable BVOL7D hourly/daily history, plus Coinbase BTCUSD and Binance BTCUSDT point-in-time source. Check last-valid updates, gaps_on vs gaps_off without trading performance retuning, exact same-bar signal availability, and independent archive parity. If unavailable: SOURCE_BLOCKED, not OOS PASS.
3. Reconcile original author Pine bytes/commit, original chart TradingView broker settings and export timestamps; verify 4h three bar anomalies and overnight costs (funding, actual mark/venue BBO), max DD/stop feasibility.
4. Distinct prospective protocol after source availability proved, lock 4h and 1D as two separate **descriptive** tracks and test true post-freeze future, with fixed cross-market latency and consistent risk. No 'free' fast 5m family rescue and no opening internal protected 2026 holdout or making live trades.
