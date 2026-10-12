# BTC-CONVEX-TREND-CAPTURE-001 — EXECUTION INTEGRITY GATE V0.1

**Date:** 2026-09-23  
**Status:** FAIL-CLOSED PENDING SOURCE/SETTINGS  
**Scientific role:** execution-authenticity gate only

## Evidence

Ordinary matched entries:
- 5m: entry fills match next-bar OPEN within 1 bp.
- 15m: entry fills match next-bar OPEN within 1 bp.
- 4h ordinary entries: entry fills match next-bar OPEN within 1 bp.

However, the supplied 4h ledger contains 19 reentries on the same chart bar as the prior exit.

For the 18 cases for which official Binance USD-M monthly 4h archives are available:
- 18/18 reentry prices match the historical bar LOW within 1 bp;
- 0/18 match OPEN as their nearest OHLC tick;
- 0/18 match HIGH;
- 0/18 match CLOSE.

This exact-low pattern is not treated as normal market-fill evidence.

## TradingView mechanism risk

TradingView documents that historical strategies normally calculate once per bar and market orders fill at the next available bar open.

TradingView also documents that enabling `calc_on_order_fills` causes additional executions after order fills. On historical bars, the broker emulator exposes a small set of historical ticks from OHLC data by default, and Pine calculations during those historical intrabar executions can have access to the bar's confirmed OHLC values.

TradingView explicitly warns this can produce misleading or lookahead-biased results depending on implementation.

Therefore:

**4H_EXECUTION_INTEGRITY = BLOCKED_PENDING_EXACT_SOURCE_AND_PROPERTIES**

This is not a declaration that every same-bar fill is invalid. The exact Pine code/settings are required to determine whether the behavior is legitimate, emulator-specific, or contaminated by lookahead.

## Economic sensitivity

Same-bar 4h reentry ledger accounting:
- 19 trades;
- 8 winners / 11 losers;
- +5,028.04 USDT gross winning PnL contribution;
- -4,891.24 USDT losing contribution;
- net +136.80 USDT.

Full 4h closed PnL = +1,417.20 USDT.

Simple removal of these trade PnLs leaves +1,280.40 USDT. This is descriptive only because deleting trades would change later equity sizing and possibly strategy state.

Therefore the suspicious 4h behavior is **not sufficient by itself to explain the full positive ledger**.

## Required PASS evidence

The execution-integrity gate cannot pass until exact source/settings establish:
- `calc_on_order_fills`;
- `calc_on_every_tick` / historical tick settings where applicable;
- `process_orders_on_close`;
- Bar Magnifier / historical bar detail state;
- exact entry-order placement logic after an exit;
- whether historical current-bar OHLC variables are used in a way unavailable at the decision timestamp.

If any historical reentry depends on impossible foreknowledge, the affected evidence must be excluded from promotion/adjudication and the exact original configuration must be classified accordingly.

## Verdict

**5m/15m: REPRODUCTION STILL SOURCE-BLOCKED.**  
**4h: REPRODUCTION + EXECUTION INTEGRITY SOURCE-BLOCKED.**  
**EDGE: UNPROVEN.**

No live trading, promotion, exchange mutation or main merge is authorized.
