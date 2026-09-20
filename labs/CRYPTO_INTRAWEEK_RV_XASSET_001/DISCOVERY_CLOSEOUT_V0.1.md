# CRYPTO-INTRAWEEK-RV-XASSET-001 — SOL/BNB DISCOVERY CLOSEOUT V0.1

Date: 2026-09-20
Canonical run: `35500147634`
MVE: `CIRV-HAR-DOW-SOLBNB-001`

## Source

**CIRV_SOURCE_FULL**

- BNBUSDT: 1,461 / 1,461 valid realized-variance days, 48 / 48 monthly archives.
- SOLUSDT: 1,456 / 1,461 valid realized-variance days (99.66%), 48 / 48 monthly archives.

## Discovery 2023-2024

**DISCOVERY_FAIL_NO_PROMOTION**

BNBUSDT:
- N = 731
- QLIKE reduction = **+1.050%**
- log-MSE reduction = **+17.871%**
- paired NW/DM t = **3.048**

SOLUSDT:
- N = 731
- QLIKE reduction = **+0.574%**
- log-MSE reduction = **+15.074%**
- paired NW/DM t = **1.499**

Pooled QLIKE reduction = **+0.835%**.

Passed:
- sample size on both assets
- positive QLIKE improvement on both
- positive log-MSE improvement on both
- positive DM t on both
- at least one asset DM t >= 1.645

Failed:
- frozen pooled QLIKE reduction >= 1.00%

Because the exact cross-asset Discovery gate failed, the 2025 SOL/BNB holdout remained closed.

## Interpretation

The direction of the weekday-structure effect generalizes weakly to SOL and BNB: both assets improve on both forecast losses, and BNB is statistically stronger. However, the exact pre-frozen cross-asset hurdle was not met.

This does **not** alter the BTC/ETH `SURVIVES_2025_HOLDOUT` result. It limits the claim of broad cross-asset generality.

No parameter rescue, asset dropping, 2025 SOL/BNB holdout, 2026 data, PnL, live trading, exchange mutation, wallet access or merge to main occurred.
