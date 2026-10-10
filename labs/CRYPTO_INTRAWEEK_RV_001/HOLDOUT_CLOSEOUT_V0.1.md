# CRYPTO-INTRAWEEK-RV-001 — BTC/ETH HOLDOUT CLOSEOUT V0.1

Date: 2026-09-20
Canonical run: `35500049139`
MVE: `CIRV-HAR-DOW-BTCETH-001`

## Source

**CIRV_SOURCE_FULL**

5-minute Binance USD-M data were complete for BTCUSDT and ETHUSDT across 2021-2024:
- 48 / 48 monthly archives per asset
- 1,461 / 1,461 valid UTC realized-variance days per asset
- each accepted day had 287-288 valid 5-minute returns

## Discovery 2023-2024

**DISCOVERY_PASS**

BTCUSDT:
- N = 731
- QLIKE reduction vs plain HAR = **+1.681%**
- log-MSE reduction = **+34.645%**
- paired NW/DM t on QLIKE loss differential = **4.233**

ETHUSDT:
- N = 731
- QLIKE reduction = **+1.097%**
- log-MSE reduction = **+24.079%**
- paired NW/DM t = **3.855**

Pooled QLIKE reduction = **+1.396%**.

Every frozen Discovery gate passed, so the locked 2025 holdout was opened.

## Holdout 2025

**SURVIVES_2025_HOLDOUT**

BTCUSDT:
- N = 365
- QLIKE reduction = **+2.150%**
- log-MSE reduction = **+46.262%**
- paired NW/DM t = **5.837**

ETHUSDT:
- N = 365
- QLIKE reduction = **+1.426%**
- log-MSE reduction = **+30.703%**
- paired NW/DM t = **3.608**

Pooled QLIKE reduction = **+1.818%**.

All frozen holdout gates passed for both assets.

## Scientific interpretation

Explicit target-day weekday structure improves one-day-ahead realized-variance forecasts relative to the plain HAR benchmark in both BTC and ETH, and the improvement survives the prospectively locked 2025 holdout.

This is a forecast result, not a trading-PnL result. It supports maturity at **L5 OOS/HOLDOUT** for the volatility-forecast mechanism. It does not by itself authorize options trading, leverage sizing, capital deployment, or a diamond label.

A separately frozen exact-rule cross-asset replication and/or prospective forward observation is the appropriate next step.

No 2026 outcomes, PnL, live trading, exchange mutation, wallet access or merge to main occurred.
