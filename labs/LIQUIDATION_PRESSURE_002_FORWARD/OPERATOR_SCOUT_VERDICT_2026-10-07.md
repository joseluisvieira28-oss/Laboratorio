# LIQUIDATION REVERSAL OPERATOR SCOUT — VERDICT 2026-10-07

Observed through UTC: 2026-10-07T19:33:49.634191+00:00
Observation duration: 180 seconds
Mode: PUBLIC BYBIT WEBSOCKET / READ-ONLY / NO ORDERS

Frozen q95 burst thresholds:
- BTCUSDT: 297490.255 USDT / 5s
- ETHUSDT: 334400.8419 USDT / 5s
- SOLUSDT: 46364.0 USDT / 5s
- XRPUSDT: 79025.7258 USDT / 5s
- DOGEUSDT: 174472.60349 USDT / 5s

Live scout:
- q95 triggers observed: 0
- current operator verdict: NO_TRADE_NOW_NO_Q95_TRIGGER

Existing authoritative economic evidence:
- completed independent forward events: 1
- symbol: SOLUSDT
- direction: LONG reversal after long-liquidation / forced-sell burst
- gross 30s move: +3.4405642525 bps
- BASE net after 5.5 bps taker per side: -7.5613280578 bps
- STRESS net after 10 bps per side: -16.5628763117 bps
- scientific verdict: INSUFFICIENT_FORWARD_SAMPLE

## Interpretation
There is no current liquidation-reversal entry signal.
The only completed forward event moved in the predicted reversal direction gross, but not enough to pay taker fees.
One event is not enough to declare NO_EDGE or TRADEABLE.

No trading authority.
