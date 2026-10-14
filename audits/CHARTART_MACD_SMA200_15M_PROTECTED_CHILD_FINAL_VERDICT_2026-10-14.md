# ChartArt MACD/SMA200 15M V0.1 — FROZEN HISTORICAL FINAL ECONOMIC VERDICT
14 October 2026 UTC. Canonical experiment SUCCESS. **NO_HISTORICAL_CANDIDACY / NO MICRO-LIVE GO / NO INDEPENDENT OOS**.
Location: draft PR #225, branch research/chartart-macd-sma200-15m-prospective-v01-2026-10-14. main unchanged. Original scientific freeze commit **dcb81df170e5343fefc8739d00632bb66f984738**, recorded before any new historical 2022-2025 outcomes.

## Immutable primary receipts
- [Canonical single GitHub Actions study #38598789132](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38598789132): 11/11 synthetic tests PASS, public Binance USD-M 15m full publisher-checksum ZIP acquisition PASS, economic engine SUCCESS. [Authoritative compressed artifact #11912551562](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38598789132/artifacts/11912551562) contains full source SHA256 list, economics JSON and individual per-trade ledger. **No 2026 was requested/downloaded**.
- [Source/economic artifact-only receipt #38599122973](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38599122973) SUCCESS; download-only, no market replay. Publisher source verified **108 archives**: 60 fifteen-minute market-price ZIPs (2021 warmup through 2025) and 48 funding-rate ZIPs (2022–2025). **175,296** continuous BTCUSDT USD-M 15m bars; **4,383** funding events; 1,791 strictly-positive subsecond funding timestamps normalized (max31ms) for same-boundary proxy accounting, without editing rates. Publisher source has **zero verified exact funding markPrice fields**; use 15m opening market-price proxy. All market and funding archive SHA256 values included in canonical artifact.
- A second workflow run #38599122967 was inadvertently triggered by a PR synchronize event. It is **NONCANONICAL**, never used as additional evidence or tuning input. Auto historical replay subsequently disabled at governance commit d35ffbea126b1f8a655cfa75f1b1dc830a3af846; no further results should be given OOS/replication weight.
- The pasted Pine v2 was not imported as byte-identical source and NOT compiled on TradingView during this study. We implemented a **frozen Python interpretation** of identical source signal rules using marketable next-15m-OPEN entries and two account models, excluding Pine v2 exact stop-entry queue/risk-max-intraday broker-emulator behavior. Historical outputs should NOT be passed off as exact 2015-v2 TradingView reproduced PnL.

## Fixed simulation protocol
BTCUSDT 15m UTC from 2022-01 through 2025-12, 2021 warmup, 10,000 USDT virtual equity **per account**, entry notional 10% of equity, 1x, both LONG and SHORT; confirmed completed candle signal with SMA12/26 MACD, signal SMA9, SMA200, historical close[26] vs current SMA200. Signals filled at NEXT 15m candle opening with adverse slip. No market-data peek; all missing source/checksum would fail closed. Both arms use BASE 8bps taker +2bps slip per side or STRESS 8+5bps/side, plus timestamped public long/short funding with OPEN proxy. Protection child E1 only: hard initial 4% adverse stop price, active in entry candle and conservatively worse gap execution, 7 calendar day cap; same signal/reversal logic as E0. E0 original-signal reference has no per-position stop/cap.

## Canonical results — four years cumulative, **not annual**
| Arm | BASE closed | BASE terminal return | BASE PF | BASE max 15m MTM drawdown | STRESS closed | STRESS terminal return | STRESS PF | STRESS max DD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| E0 unprotected signals | 354 | **+7.0961%** | 1.1219 | -6.5598% | 354 | +4.8360% | 1.0825 | -6.8069% |
| E1 protected 4% stop +7d max | 407 | **-2.1639%** | 0.9701 | -9.5854% | 408 | **-4.6549%** | 0.9352 | -10.8224% |
Terminal virtual equity: E0 BASE 10,709.609 USDT vs E1 BASE 9,783.610; E0 STRESS 10,483.604 vs E1 STRESS 9,534.512. E1 has more closed positions (407/408 vs 354), thus increased repeated cost drag. STRESS changes some stop-trigger timing and trade count dynamically because slipped entry changes stop price, NOT a static ledger-only sensitivity. All values contain simulation commissions/slippage and modeled funding; none implies actual executable futures edge.

## Base account reconciliation and costs
| Field | E0 BASE | E1 BASE |
|---|---:|---:|
| Closed net PnL USDT | +719.3268 | -207.5123 |
| Still-open position net mark USDT | -9.7178 | -8.8775 |
| Terminal paper net USDT | +709.6091 | **-216.3899** |
| Individual transaction fee total USDT | 590.1050 | 654.1577 |
| Funding accounting total USDT | -82.8924 | -65.4089 |
| Winners / losers closed | 130 / 224 | 138 / 269 |
| Top 3 NET winner sum USDT | +845.5223 | +774.6616 |
| Closed net after removing top3 winners STATIC | **-126.1955** | **-982.1740** |
| LONG closed net USDT | +850.9414 | +76.1581 |
| SHORT closed net USDT | -131.6146 | -283.6705 |
Removing winners is a *non-causal descriptive sensitivity*: do not re-simulate portfolio or advertise this as an independent OOS. Long/short asymmetry is now observed; do NOT create a LONG-only 'rescue' on these years.

## Closed NET profitability by exit year (including assigned funding and fees)
| Year | E0 BASE USDT | E1 BASE USDT | E1 closed trades |
|---|---:|---:|---:|
| 2022 | -170.55 | -312.04 | 106 |
| 2023 | +626.15 | +708.95 | 93 |
| 2024 | +422.85 | -224.47 | 107 |
| 2025 | -159.12 | -379.96 | 101 |
Only **1/4 years** (2023) is profitable for E1 BASE. For STRESS only 2023 is positive (+651.46), 2022 -362.26, 2024 -278.73 and 2025 -467.02. E0 two positive years out of four (2023–24).

## Predeclared frozen gates — NO alteration after PnL
| Criterion | E1 result |
|---|---|
| At least 100 closed trades over window | PASS (407 BASE) |
| At least 15 closed trades per year | PASS (93–107) |
| BASE + STRESS terminal positive | **FAIL** (-2.16%, -4.65%) |
| PF BASE >1.15 and STRESS >1.05 | **FAIL** (0.970, 0.935) |
| At least 3 of 4 years positive BASE+STRESS | **FAIL** (1/4) |
| MTM drawdown <=20% BASE | PASS (-9.59%) |
| After removal top3 winners still BASE closed positive | **FAIL** (-982.17 USDT) |
| Incremental over source-signal reference E0 | **FAIL** (worse return, PF, DD, net expectancy) |
**Frozen verdict NO_HISTORICAL_CANDIDACY**. E0 historically positive but not resilient to top3 exclusion, weak PF and lacking stop protection. No 2026 forward clean data and no real broker venue executable bid/ask, funding mark, contract lot, stop-order acknowledgement, margin/kill-switch or run restart receipts. Nothing is remotely MICRO-LIVE GO.

## Final allocation action
Stop spending time trying to rescue these exact original ChartArt 15m signals with optimized 4% stop, time window, SMA200 lookback, LONG-only, fee reduction, chart timeframe or price source based on already opened 2022–25 outcomes. Scientific negative child is complete and archived. The already-viewed 2026 TradingView CSV is not independent forward for this child. A different economic mechanism needs independent source and separate preregistered future outcomes; no main merge or trading.
