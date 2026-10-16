# LICP-001 — FEATURE CALIBRATION RUN 001 RESULT

Date: 2026-09-26
Workflow run: 36231152537
Status: CALIBRATION_SPARSE

## Window
300 seconds.

## Liquidation streams
Binance:
- subscription acknowledged
- 29 websocket messages
- 0 BTC/ETH/SOL liquidation events retained
- malformed: 0

Bybit:
- subscription acknowledged
- 1 websocket message (subscription acknowledgement)
- 0 BTC/ETH/SOL liquidation events
- malformed: 0

Total eligible liquidation events: 0.

Therefore no burst notional or side-concentration quantile exists for any required trigger component.

## Open interest
The Binance USD-M public OI REST polling path failed for all attempted calls from this GitHub runner:
- poll rounds: 59
- errors: 177
- valid BTC/ETH/SOL OI snapshots: 0

This is treated as a source/infrastructure blocker only.

## Outcome isolation
- MEXC post-trigger price outcomes opened: NO
- trigger config frozen: NO
- trigger config remains UNFROZEN

## Decision
CALIBRATION_SPARSE.

Per the frozen policy, missing quantiles must not be substituted or lowered.
Continue feature-only calibration on new forward data.

A pre-outcome technical amendment switches OI context to public Hyperliquid metaAndAssetCtxs and extends the next bounded calibration run to 600 seconds.
