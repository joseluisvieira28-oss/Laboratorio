# V0.13.1 LIVE ATTACK STATUS — 2026-10-03

Branch: `mexc-event-futures-v013-source-completion-2026-10-03`
Parent: `mexc-event-futures-event-conditioned-v0.13-prereg-2026-10-03`
Main untouched.

## Liquidation family

Prior one-hour evidence:
- run 37075262340
- BTC valid real liquidations: 3
- ETH valid real liquidations: 0
- verdict PARTIAL_SOURCE
- no transport exceptions
- artifact 11257963990
- digest sha256:1521ef40603b46a3e76fc148c1e6df9d830faae7c00030ed720e23c45c3e1a5f

Independent-topic audit:
- run 37100075588
- BTC allLiquidation topic ack PASS
- ETH allLiquidation topic ack PASS
- errors 0
- 90-second window had 0 real liquidation events
- verdict PARTIAL_SOURCE
- artifact 11265289330
- digest sha256:590fd5d3ab57aec6603ed67840ea1d99c67e648aba50fa39462d6592c55969fd

ETH market-liveness diagnostic:
- run 37100470880
- 25 tickers.ETHUSDT messages
- 1 publicTrade.ETHUSDT message
- errors 0
- verdict ETH_MARKET_LIVE
- gives zero liquidation-source-gate credit
- artifact 11265744056
- digest sha256:e5f2c243a0ad62f4934b1fcc2c79dfa9ce9e34568089c817af71f38603d00e0a

Interpretation:
ETH symbol/feed and liquidation-topic subscription are both operationally live.
The missing evidence is specifically a real ETH liquidation payload.

Active source-completion run:
- workflow run 37100077597
- max 10800 seconds
- independent BTC/ETH public connections
- early stop only after valid ETH liquidation + both topic acks + no invalidating errors
- prior BTC payload evidence anchored
- no MEXC/outcome/trading access

Do not activate LIQUIDATION-FLOW-FWD-001 until this reaches SOURCE_GATE_PASS.

Calibration tooling:
- health semantics frozen in LIQUIDATION_FLOW_CALIBRATION_HEALTH_ADDENDUM_V013_V01.md
- collector prepared in liquidation_flow_calibration_chunk_v0131.py
- synthetic mechanics self-test run 37100308809 PASS
- REAL_CALIBRATION_STARTED=0
- source-gate events are excluded from calibration
- real calibration may begin only strictly after a SOURCE_GATE_PASS receipt

## Options family

Frozen rule unchanged:
- family OPTIONS-VOL-FWD-001 V0.1
- rule hash edd02c530398465cb35e481f96e336ebd0dcccc73235aaffe6c1d984c3986517
- FOLLOW_INSURANCE_SKEW
- absolute skew threshold 5.0 pp
- horizon 10m
- N min 100 per symbol
- 30-day evaluation boundary
- exact observed Event Futures payout per shadow event

Initial smoke:
- run 37074644170
- preflight PASS
- resolved N=0
- outcomes opened=0
- status INSUFFICIENT_N
- artifact 11255948065
- digest sha256:c4e5379eeebfc99a4109872d8e50005137e3b9377986791259a9a9dbb69b4ebe

First continuation attempt:
- run 37100149611
- FROZEN_RUNTIME_BLOCKED
- INDEX_TICK_TIMEOUT
- source rounds 0
- outcomes opened 0
- resolved N 0
- public index stream itself was active
- blocker was lack of a BTC change-driven push inside one arbitrary 5s preflight join

Technical correction:
- OPTIONS_VOL_RUNTIME_PREFLIGHT_RETRY_FREEZE_V0131.md
- real event five-second payout/index join remains unchanged
- preflight may retry up to 12 NEW payout/index join attempts per symbol
- no blocked attempt is rescued

Current corrected bounded forward batch:
- run 37100393588
- 10800-second acceptance window when preflight passes
- same frozen rule and original forward boundary
- zero trading/private/account actions

## Scientific state

No hypothesis has been declared dead by these source/runtime results.
No edge has been demonstrated.
No significance test is authorized early.
No main merge.
No live trading.
No orders.
No private Event Futures endpoints.
