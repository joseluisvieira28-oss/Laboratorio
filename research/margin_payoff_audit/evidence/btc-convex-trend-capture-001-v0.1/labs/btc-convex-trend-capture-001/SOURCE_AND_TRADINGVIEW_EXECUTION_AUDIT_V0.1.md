# BTC-CONVEX-TREND-CAPTURE-001 — SOURCE + TRADINGVIEW EXECUTION AUDIT V0.1

**Date:** 2026-09-23  
**Status:** SOURCE_CODE_NOT_FOUND / EXECUTION-SEMANTICS RISK IDENTIFIED  
**Role:** forensic support only

## 1. Exact-source search

Searched:
- current repository default branch for "Quant Trailing", "Payoff Invertido" and BTC trailing variants;
- repository branch names for quant/trailing/payoff variants;
- public GitHub code search for the exact strategy name and close variants;
- public web/TradingView search for the exact strategy name and close variants;
- connected Google Drive for "Quant Trailing v5", "Payoff Invertido", "Quant Trailing" and "BTCUSDT.P";
- prior available project/conversation context for the exact name.

No exact Pine/source/configuration for **Quant Trailing v5 (Payoff Invertido)** was found.

Classification:

**SOURCE_CODE_MISSING**

This is an evidence state, not proof that the code never existed.

## 2. TradingView trailing-stop semantics relevant to this lab

Official Pine strategy documentation states that a built-in trailing stop created with `strategy.exit()` requires:
- an activation level via `trail_price` or `trail_points`;
- a trail offset via `trail_offset`.

After activation, the built-in stop trails favorable intrabar extremes. The parameters are expressed as prices/ticks according to the Pine API, not inherently as percentages.

Official references:
- https://www.tradingview.com/pine-script-docs/concepts/strategies/
- https://www.tradingview.com/pine-script-docs/faq/strategies

## 3. Historical-emulation risk

TradingView explicitly warns that built-in trailing stops can differ between realtime and historical calculations because historical bars do not contain the full intrabar path. The broker emulator must make assumptions unless lower-timeframe information is available.

TradingView also documents Bar Magnifier as a way to use lower-timeframe data for more realistic historical order fills.

Relevant references:
- https://www.tradingview.com/pine-script-docs/faq/strategies
- https://www.tradingview.com/support/solutions/43000774016-common-reasons-for-mismatches-between-strategy-alert-triggers-and-strategy-orders-on-the-chart/
- https://www.tradingview.com/pine-script-docs/release-notes/

## 4. New reproduction blockers

Exact reproduction therefore requires more than the entry formula. We must also recover or prove:

1. Pine language version;
2. exact `strategy()` properties;
3. `use_bar_magnifier` state;
4. `calc_on_every_tick` state;
5. `calc_on_order_fills` state;
6. `process_orders_on_close` state;
7. commission type/value;
8. slippage setting;
9. pyramiding setting;
10. margin / default quantity mode;
11. exact trailing implementation:
    - built-in `trail_price` / `trail_points` / `trail_offset`, or
    - custom stop logic;
12. symbol/feed and standard-vs-nonstandard chart type.

Without these, matching headline PnL is not sufficient evidence of reproduction.

## 5. Implication for the seed finding

The approximately 12% peak giveback in profitable trades remains a strong descriptive fingerprint.

However, it must not yet be interpreted as proof that the Pine code literally contained a `12%` trailing parameter. A tick-based offset, a custom formula, or TradingView historical broker-emulator behavior can produce a similar observed footprint.

Likewise, the activation-boundary probe already falsified a simple universal fixed close-return trigger on 5m.

## Verdict

**EXIT FOOTPRINT STRONG / EXACT IMPLEMENTATION UNPROVEN.**

The lab remains scientifically useful, but the next decisive artifact is the exact Pine source/settings or an independently reproducible implementation that matches entry and exit timestamps under frozen tolerances.

No promotion, live trading, exchange mutation, or main merge is authorized.
