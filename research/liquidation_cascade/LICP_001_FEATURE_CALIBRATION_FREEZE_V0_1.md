# LICP-001 — FORWARD FEATURE CALIBRATION FREEZE V0.1

Date: 2026-09-26
Status: PRE-CALIBRATION / OUTCOME-BLIND

## Purpose
Calibrate only the observable forced-deleveraging feature space before any post-trigger MEXC price outcome is opened.

## Duration
First bounded calibration run: 300 seconds.

## Sources
- Binance USD-M all-market forceOrder snapshots
- Bybit allLiquidation for BTCUSDT / ETHUSDT / SOLUSDT
- Binance public current open-interest REST snapshots for BTCUSDT / ETHUSDT / SOLUSDT

No MEXC post-trigger price is analyzed in this phase.

## Normalized forced-pressure direction

### Binance
forceOrder field S is the liquidation order side:
- SELL => forced sell pressure
- BUY => forced buy pressure

### Bybit
Bybit allLiquidation S is the liquidated POSITION side.
Official documentation states that a Buy update means a long position was liquidated.
Therefore normalize:
- S=Buy => forced SELL pressure
- S=Sell => forced BUY pressure

The original venue field is preserved.

## Event notional

### Bybit
executed_size × bankruptcy_price

### Binance
prefer accumulated_filled_quantity × average_price.
If either is non-positive, fall back to original_quantity × order_price.

Binance volume is NOT treated as complete market liquidation volume because forceOrder is throttled to the latest liquidation order per symbol per 1,000 ms interval.

## Outcome-blind burst features
Per source × symbol:
- event count
- liquidation notional
- forced-sell notional
- forced-buy notional
- side concentration
- event-time burst aggregation in fixed 1s and 5s bins

Descriptive quantiles:
- p50
- p75
- p90
- p95
- p99

These quantiles describe source features only.

## Cross-venue confirmation
For the same symbol, report whether Binance and Bybit liquidation events occur within:
- ±1 second
- ±5 seconds

No price response is inspected.

## Open-interest destruction context
Poll public current Binance USD-M OI approximately every 5 seconds for:
- BTCUSDT
- ETHUSDT
- SOLUSDT

Report:
- first OI
- last OI
- first-to-last % change
- maximum drawdown from a running prior peak during the calibration window

OI is contextual confirmation only in V0.1. It does not define a trade trigger.

## Calibration sufficiency
CALIBRATION_SAMPLE is considered informative only if:
- source subscriptions remain healthy;
- malformed liquidation payloads = 0;
- >= 20 liquidation events total across Binance + Bybit during the bounded run.

If fewer than 20 events occur:
CALIBRATION_SPARSE — no thresholds may be frozen.

## Prohibited
- no MEXC price outcome
- no entry/exit
- no PnL
- no threshold optimization against future returns
- no live trading
