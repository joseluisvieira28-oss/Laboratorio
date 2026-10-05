# LICP-001 — CALIBRATION FREEZE AUDIT — 2026-10-05

Status: **CALIBRATION PASS / TRIGGER FREEZE AUTHORIZED**
Branch: `liquidation-cascade-propagation-v0.1`

## Outcome-isolation statement

This freeze was produced from outcome-blind liquidation/source-health artifacts only. No MEXC post-trigger return, PnL, MFE, MAE, hit-rate or Sharpe was inspected or used to select any threshold.

## Frozen eligibility gates

- span_days = **9.092194641204** >= 7
- Bybit events = **647** >= 250
- Bybit BTCUSDT events = **164** >= 50
- minimum source uptime = **99.998617833405%** >= 95%
- clock regressions = **0**
- canonical raw-event hash = `ed4e8096b75625193558af72956fc7ef5cdec16b6280d1ef7cce474282be1a4d`
- scheduled calibration seconds = **62400**
- shard count = **4**

Decision: **eligible_for_freeze = true**.

## Mechanical threshold mapping

- Bybit BTCUSDT 5s burst p95 = **69395.44230000001 USDT**
- Bybit BTCUSDT 5s side-concentration p75 = **1.0**
- Binance BTCUSDT 5s published-snapshot p75 = **8807.811999999998 USDT**
- Bybit ETHUSDT 5s burst p95 = **49585.26119999999 USDT**
- Bybit SOLUSDT 5s burst p95 = **41424.18 USDT**

These values are copied mechanically from the predeclared quantiles. No value was rounded or selected using future price outcomes.

## Binance source-semantics caveat

The Binance `forceOrder` stream is treated as a lossy **largest-liquidation snapshot** confirmation sensor under the 2026-10-05 source amendment. It is not treated as complete forced-liquidation volume or event count.

## Source artifact chain

- run 36234941600 / artifact 10909113556 / `sha256:80d8fdada9a207523169a13f3a95dc09e5d710d90a1c281880fd025898075ff3`
- run 36261304688 / artifact 10918394152 / `sha256:6c842c1968e195f8b3f07f14f9657df5267433763ff43ba382c8aa3d8f04f070`
- run 36280706720 / artifact 10925794842 / `sha256:7c59a410d3c75a5abc3c7e96f8c3f455eaf3ec1c7373ee72ab65d74d6e04bd66`
- run 37308484735 / artifact 11344428835 / `sha256:a9ee6042f7cfafa3ca00811e8c41abf846c34a8d770ebef09ea31ab754764398`

## Receipt integrity

Freeze receipt SHA256: `2411f39ad3e2228b723814c54030a1fa44744c871426cd28eebaf9201b4d54a0`

## Scientific state after this freeze

- SOURCE/CALIBRATION: **PASS**
- numeric trigger config: **FROZEN**
- forward outcome epoch: **NOT OPENED BY THIS AUDIT**
- economic verdict: **NOT YET SURVIVES / NOT YET NO_EDGE**
- live trading: **NOT AUTHORIZED**
