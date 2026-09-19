# BTC-OPTIONS-UWA-001 — MANUAL SOURCE RECOVERY CLOSEOUT V0.1

Date: 2026-09-19

## Classification

**UWA_TRADE_HISTORY_FULL**

The automatic GitHub source probe was previously access-blocked because the public file routes rejected the runner. The canonical UWA files were then downloaded manually through the browser and supplied directly.

The parsed `Deribit_w_IV.csv` contains **761,067 BTC-options trades** over **1,147 distinct trade dates** from **2016-11-29 through 2020-02-11**, with trade direction, amount, option identity, strike, call/put type, index price and implied volatility.

The separate instrument catalogue contains **6,724 instruments** and expiries through **2020-09-25**.

Important boundary: this source is **trade history**, not BBO/order-book history. The parsed CSV contains no bid/ask price or bid/ask size fields. Therefore it does not rescue the closed executable VRP order-book MVE.

It does, however, unlock a distinct options-information / signed-trade-flow research lane at zero cash cost.

No future returns, PnL, strategy outcomes, 2025/2026 data, live trading, wallet access, exchange mutation or merge to main were opened in this source recovery.
