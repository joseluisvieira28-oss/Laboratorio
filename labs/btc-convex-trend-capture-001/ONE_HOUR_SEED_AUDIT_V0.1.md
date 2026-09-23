# BTC-CONVEX-TREND-CAPTURE-001 — 1H SEED AUDIT V0.1

**Date:** 2026-09-23  
**Source:** operator TradingView CSV export  
**CSV SHA-256:** 38fb5267fdc085d252448a888c71d3b08fadd0807d975779fd401d37d9ed5986  
**Normalized ledger SHA-256:** ca6903faf7d4f42a40d0b76d4e7d106edec36007075d2da4600c4800b08583fa  
**Role:** retrospective seed characterization only

## Identification

The export is exactly a **1-hour** BTCUSDT perpetual strategy ledger:
- 100 closed trades;
- 1 current open trade;
- first entry: 2019-10-10 13:00;
- last closed exit: 2026-06-24 13:00;
- bar duration reconstruction = exactly 60 minutes.

## Closed-trade result

- closed net PnL: **+37,942.76 USDT**
- closed return on 10,000 initial capital: **+379.43%**
- CAGR over the closed sample: approximately **26.3%**
- wins: **26 / 100**
- win rate: **26.0%**
- average winning trade return: **+21.56%**
- average losing trade return: **-4.19%**
- average-win / average-loss payoff ratio: **5.15x**
- PnL profit factor: **1.340**
- maximum closed-equity drawdown: approximately **-40.7%**
- maximum losing streak: **10**
- closed commissions: **6,861.66 USDT**
- median trade return: **-4.19%**
- mean trade return: **+2.51%**

This is materially stronger descriptively than the previously supplied 5m, 15m and 4h seed exports, but remains retrospective and highly right-skewed.

## Tail dependence

Largest historical closed winner:
- +23,609.13 USDT.

Removing only the largest winner leaves:
- **+14,333.63 USDT** closed net.

Removing the top three historical winners leaves:
- **-20,360.33 USDT**.

Top five winners contribute approximately **52.9%** of gross winning PnL.

Therefore the 1h version is less fragile than the lower-timeframe seeds to removal of a single winner, but remains strongly dependent on a small set of major trends.

## Current open position

The export includes an open trade entered:
- 2026-07-06 13:00.

Reported current state in the export:
- open PnL: **+16,189.69 USDT**
- return: **+35.55%**
- MFE: **+41.41%**
- MAE: **-0.81%**
- cumulative PnL including open mark: **+54,086.97 USDT**
- cumulative return including open mark: **+540.87%**

The current open trade accounts for approximately **29.9%** of the cumulative profit shown including the open mark. It is not treated as a closed scientific outcome.

## Year-by-year closed PnL

| Exit year | Trades | Net PnL USDT |
|---|---:|---:|
| 2019 | 5 | -1,839.02 |
| 2020 | 14 | +6,102.03 |
| 2021 | 20 | +26,209.20 |
| 2022 | 18 | -14,447.48 |
| 2023 | 9 | +4,713.25 |
| 2024 | 16 | +36,375.64 |
| 2025 | 13 | -15,242.63 |
| 2026 closed | 5 | -3,928.23 |

The result remains regime-sensitive, with severe negative years in 2022 and 2025.

## MFE leakage among eventual losers

Among 74 closed losers:
- MFE >= +2%: 41 / 74
- MFE >= +4%: 24 / 74
- MFE >= +5%: 18 / 74
- MFE >= +10%: 6 / 74
- MFE >= +15%: 1 / 74

Median loser MFE: **+2.21%**.
Maximum loser MFE: **+15.69%**.

The recovered source explains this behavior: the 5% trail activation is not persistent and can deactivate when close-based profit falls below +5%.

## Trailing fingerprint

Of 26 closed winners:
- 24 / 26 exit in the normal approximately 11.8%-12.1% peak-giveback band;
- median reconstructed giveback ≈ **11.9325%**.

This strongly matches the recovered source parameter:
- trailing stop = 12%.

## Same-bar reentries

The 1h ledger contains **8** entries at the exact same timestamp as the previous exit.

Those eight closed trades contribute:
- winners: 4
- losses: 4
- net: **+6,111.10 USDT**

Simple ledger subtraction leaves +31,831.66 USDT, but this is not a valid counterfactual because removing trades would alter later equity sizing and potentially strategy state.

Given the recovered Pine source and the Properties screenshot, these same-bar entries are now a priority execution-integrity test.

## Important correction to source comment

The source contains a comment referring to a prior “68% win rate”.

The supplied actual ledgers do not support a current 68% win rate:
- 1h closed win rate = 26.0%;
- previous supplied timeframes were also far below 68%.

That comment is historical/stale documentation and must not be used as evidence.

## Verdict

**1H = STRONGEST RETROSPECTIVE SEED SO FAR.**

But:

**EDGE REMAINS UNPROVEN.**

The next adjudicating step is exact source reproduction and execution-integrity testing, not parameter optimization.
