# LIQUIDATION-FLOW-FWD-003 — BINANCE USD-M PUBLIC SOURCE GATE V0.3

Date: 2026-10-08
Status: SOURCE-ONLY / PRE-OUTCOME / RESEARCH-ONLY

## Version isolation

This is a new source version. It does not rewrite or pool:
- FWD-001 Bybit PARTIAL_SOURCE;
- FWD-002 OKX source work.

No cross-venue event aggregation is authorized.

## Public source

Official Binance USD-M Futures public WebSocket:
`wss://fstream.binance.com/market/stream`

Subscriptions:
- `btcusdt@forceOrder`
- `ethusdt@forceOrder`

No API key, login, account, order or private endpoint.

For each forceOrder message preserve:
- symbol `o.s`;
- side `o.S`;
- original quantity `o.q`;
- order price `o.p`;
- average price `o.ap`;
- order status `o.X`;
- event time `E`;
- trade/order time `o.T`;
- raw message SHA-256 and receipt time.

Source semantics frozen for later calibration only:
- SELL force order = long-liquidation forced selling;
- BUY force order = short-liquidation forced buying.
No directional outcome is opened here.

## Gate duration

600 seconds after successful subscription acknowledgement.

## Valid event

Per target symbol a record is valid only if:
- exact symbol is BTCUSDT or ETHUSDT;
- event type = forceOrder;
- side in {BUY,SELL};
- q finite and > 0;
- at least one of ap or p finite and > 0;
- E and T parse as integer milliseconds;
- receipt age versus max(E,T) <= 5 seconds;
- future-clock tolerance <= 1 second;
- raw SHA-256 preserved.

## Verdict

Both symbols >=1 valid event:
`BINANCE_LIQUIDATION_SOURCE_PASS`

One symbol only:
`PARTIAL_SOURCE`

Neither:
`NO_EVENTS_OBSERVED`

Subscription/transport failure:
`SOURCE_BLOCKED`

## Outcome boundary

Research outcomes opened must remain exactly 0.

This gate MUST NOT access MEXC Event Futures products, payouts, index outcomes, account data,
candles for future-return labels, win/loss, PnL, or any protected holdout.

## Calibration status

NOT ACTIVE.

A source PASS only authorizes a separately frozen source-only calibration design.
No threshold, quantile, direction rescue, cross-venue pooling or Event Futures outcome may be
selected from this run.

No merge to main. No live trading. No orders. No wallets. No spending. No exchange mutation.
