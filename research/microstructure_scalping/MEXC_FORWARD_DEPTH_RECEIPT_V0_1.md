# MEXC FORWARD DEPTH RECEIPT V0.1

Date: 2026-09-25
Status: PASS_SAMPLE
Workflow run: 36188589951
Scope: public market data only — no authentication, no orders, no exchange mutation.

## 20-second BTC_USDT sample
- subscription acknowledged: yes
- total websocket messages: 6,941
- incremental depth events: 6,939
- REST snapshot version: 42116634740
- first websocket depth version: 42116634751
- last websocket depth version: 42116641689
- non-monotonic versions: 0
- version gaps inside observed websocket sequence: 0
- gate: PASS_SAMPLE

## Interpretation
The public MEXC Futures depth stream is usable for a forward microstructure observer with explicit version-gap detection.

This does NOT prove:
- historical MEXC L2 availability
- predictive edge
- profitable execution
- fill quality
- latency from the intended deployment environment
- live-trading authorization

Any future collector must reinitialize on a version discontinuity as required by the documented MEXC depth-maintenance procedure.
