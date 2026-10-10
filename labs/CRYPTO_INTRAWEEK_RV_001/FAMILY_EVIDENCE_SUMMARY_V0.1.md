# CRYPTO-INTRAWEEK-RV — FAMILY EVIDENCE SUMMARY V0.1

Date: 2026-09-20

## Current family status

**PROMOTED TO L5 — REPLICATED OOS/HOLDOUT FORECAST MECHANISM**

This maturity applies to the **volatility-forecast mechanism only**. It is not a trading-strategy, options-PnL, or diamond promotion.

## Canonical evidence

### Binance USD-M Futures — BTC / ETH
Run: `35500049139`
Verdict: **SURVIVES_2025_HOLDOUT**

2025 QLIKE reduction versus plain HAR:
- BTC: +2.150%
- ETH: +1.426%

2025 log-MSE reduction:
- BTC: +46.262%
- ETH: +30.703%

Paired NW/DM t:
- BTC: 5.837
- ETH: 3.608

### Binance Spot — BTC / ETH
Run: `35500300894`
Verdict: **SURVIVES_2025_HOLDOUT**

2025 QLIKE reduction:
- BTC: +2.160%
- ETH: +1.407%

2025 log-MSE reduction:
- BTC: +46.602%
- ETH: +31.102%

Paired NW/DM t:
- BTC: 5.915
- ETH: 3.688

The near-identical effect size across USD-M Futures and Spot is strong corroboration that the weekday structure is not merely a futures-specific artifact.

### Exact-rule SOL / BNB cross-asset replication
Run: `35500147634`
Verdict: **DISCOVERY_FAIL_NO_PROMOTION**

Both assets improved on both QLIKE and log-MSE, and BNB had DM t = 3.048. However pooled QLIKE reduction was +0.835%, below the prospectively frozen +1.00% Discovery gate. The 2025 SOL/BNB holdout therefore remained closed.

This limits broad cross-asset generality but does not alter BTC/ETH evidence.

## Forward status

Forward ID: `CIRV-BTCETH-FORWARD-001`

Preflight run: `35500251132`
Status: **READY**

- BTC and ETH source history available through 2026-09-19
- 902 valid daily RV observations per asset in the forward preflight window
- no pre-boundary target outcome opened
- first eligible clean target date: **2026-09-21**

## Scientific boundary

What is supported:
- target-day weekday structure improves one-day-ahead BTC and ETH realized-variance forecasts;
- the result survives a locked 2025 holdout;
- the effect replicates on both Binance Futures and Binance Spot.

What is not yet supported:
- profitable option trading;
- profitable directional trading;
- leverage/sizing alpha;
- implied-vs-realized variance edge after costs;
- production deployment.

Next maturity gate:
**L6 prospective forward observation**, followed only then by a separately frozen application layer for options, sizing, or regime selection.

No 2026 resolved forward outcomes, live trading, exchange mutation, wallet access, or merge to main have been opened.
