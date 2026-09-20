# CRYPTO-INTRAWEEK-RV-SPOT-001 — BTC/ETH SPOT HOLDOUT CLOSEOUT V0.1

Date: 2026-09-20
Canonical run: `35500300894`
MVE: `CIRV-HAR-DOW-BTCETH-SPOT-001`

## Source

**CIRV_SOURCE_FULL**

Binance Spot 5-minute BTCUSDT and ETHUSDT data passed the frozen source gate across 2021-2024:
- 48 / 48 monthly archives per asset
- 1,456 / 1,461 valid UTC RV days per asset (99.66%)
- accepted days had at least 271 valid 5-minute returns

## Discovery 2023-2024

**DISCOVERY_PASS**

BTCUSDT Spot:
- N = 731
- QLIKE reduction vs plain HAR = **+1.691%**
- log-MSE reduction = **+35.861%**
- paired NW/DM t = **4.410**

ETHUSDT Spot:
- N = 731
- QLIKE reduction = **+1.061%**
- log-MSE reduction = **+25.771%**
- paired NW/DM t = **4.294**

Pooled QLIKE reduction = **+1.381%**.

All frozen Discovery gates passed, so the locked 2025 Spot holdout was opened.

## Holdout 2025

**SURVIVES_2025_HOLDOUT**

BTCUSDT Spot:
- N = 365
- QLIKE reduction = **+2.160%**
- log-MSE reduction = **+46.602%**
- paired NW/DM t = **5.915**

ETHUSDT Spot:
- N = 365
- QLIKE reduction = **+1.407%**
- log-MSE reduction = **+31.102%**
- paired NW/DM t = **3.688**

Pooled QLIKE reduction = **+1.814%**.

All frozen 2025 holdout gates passed on both spot assets.

## Interpretation

The same exact HAR + target-day weekday structure that survived on Binance USD-M Futures also survives on Binance Spot for BTC and ETH with nearly identical effect sizes.

This materially strengthens the claim that the effect is a **volatility-forecast structure**, not a futures-specific microstructure artifact.

It remains a forecasting result, not a PnL or options-profit result.

No 2026 data, trading PnL, live trading, exchange mutation, wallet access or merge to main occurred.
