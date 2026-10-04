# MEXC GLOBAL-ASSET EXECUTION ROUTE CLOSEOUT V0.1

Date: 2026-10-04
Status: FROZEN OPERATIONAL VERDICT

Scientific family authority:
- V0.5 run: 37235872887
- 35 assets
- 31 scientific survivors after Holm
- 0 fee-floor survivors after 12 bps
- 0 robust-fee survivors after 16 bps
- family artifact SHA256: 1fd39b9a6224d3210e74ba8ee12f9486d35ff8dd1a5f9ece7fc986353a47c5f3

## Standard MEXC Futures API

Official MEXC API Futures fee update effective 2026-06-01:
- maker 0.06% per side
- taker 0.08% per side
- API tariff overrides website/app promotions and zero-fee rates
- applicable to Futures API pairs outside Innovation Zone.

Frozen standard round trips:
- maker-maker: 12 bps
- maker-taker: 14 bps
- taker-taker: 16 bps

V0.5 empirical maximum mean gross:
- VRTSTOCK_USDT: +5.724073 bps

Therefore:
`STANDARD_MEXC_API_EXECUTION_ECONOMICALLY_BLOCKED`

## TradingView

MEXC's direct TradingView broker connection advertises standard MEXC broker rates for orders placed through the broker integration.

However MEXC's own automation description routes TradingView strategy alerts through webhook to the MEXC execution layer after launch of Futures API trading.

No official evidence was identified that an automated TradingView webhook route preserves website/app broker fees instead of API Futures fees.

Therefore:
`TRADINGVIEW_MANUAL_BROKER_ROUTE_NOT_EQUIVALENT_TO_PROVEN_AUTOMATED_NON_API_ROUTE`

## MEXC AI Strategy

Official MEXC AI Strategy documentation states:
- fees follow the main account rate;
- supported triggers are time, price, candlestick patterns, technical indicators, and social-media monitoring;
- at most two strategy types may be combined.

This makes AI Strategy potentially attractive on fees.

But no documented trigger can reproduce the frozen Crypto Lab signal:
- read Binance 1m return;
- read Bitget 1m return;
- average them;
- compare against MEXC 1m return;
- require same-sign lag gap >=3 bps after external shock >=5 bps.

Therefore:
`AI_STRATEGY_FEE_ROUTE_POTENTIALLY_COMPATIBLE__SIGNAL_COMPATIBILITY_NOT_PROVEN`

## Overall operational verdict

`NO_PROVEN_OFFICIAL_AUTOMATED_MEXC_ROUTE_PRESERVES_THE_REPLICATED_EDGE_AFTER_COSTS`

This is an execution blocker, not a scientific failure.

Do not continue mining additional MEXC stock symbols with the same 5/3/1m rule solely to rescue API profitability. V0.5 already tested 35 pre-frozen source-pass assets and found zero 12-bps survivors.

Next legitimate research direction:
- test the economic mechanism on a different execution venue with a materially lower automated fee schedule, under a new pre-outcome venue-specific freeze; or
- wait for a documented MEXC fee/automation route change and re-open execution feasibility only, without retuning science.

No live trading, orders, account reads, private endpoints, wallets or exchange mutation were used.
