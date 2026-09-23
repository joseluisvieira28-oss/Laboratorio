# BTC-CONVEX-TREND-CAPTURE-001 — ENTRY PULLBACK DIAGNOSTIC CLOSEOUT V0.2

**Date:** 2026-09-23  
**Run:** 35899464742  
**Artifact:** 10768687780  
**Artifact SHA-256:** 891be0a1281dc75de43a0957fd34d32a73c1125222ae31696489f70f621422e3  
**Status:** POST_HOC_FORENSIC_DIAGNOSTIC_SUCCESS / ZERO PROMOTION CREDIT

## Purpose

V0.1 narrowed the entry architecture to a long-horizon bullish context combined with short-horizon weakness. V0.2 deliberately tested that observation as **post-hoc source reconstruction only**.

Nothing in this closeout may be treated as independent evidence of edge.

## Pullback fingerprint

The following post-hoc conjunction was inspected:

`EMA20 > EMA50 AND MACD <= signal AND RSI14 <= 50 AND 20-bar momentum <= 0`

Entry recall vs flat-state control frequency:

| TF | Entry recall | Flat control | Lift |
|---|---:|---:|---:|
| 5m | 90.7% | 6.5% | 13.88x |
| 15m | 89.9% | 6.1% | 14.79x |
| 4h | 75.0% | 5.6% | 13.43x |

Adding `EMA50 > EMA200` reduced recall but increased specificity:

| TF | Entry recall | Flat control | Lift |
|---|---:|---:|---:|
| 5m | 70.3% | 1.7% | 40.96x |
| 15m | 76.5% | 2.1% | 37.21x |
| 4h | 71.7% | 2.9% | 24.75x |

These are reverse-engineering fingerprints, not candidate rules.

## Additional entry-state fingerprints

On the prior bar:
- MACD below/equal signal: 100% across matched 5m/15m/4h entries.
- close below EMA9: 100% across matched entries.
- close below EMA20: 100% across matched entries.
- RSI14 <= 50: 98.8% / 98.7% / 96.7%.
- 20-bar momentum <= 0: 96.5% / 96.0% / 88.3%.

This sharply strengthens the interpretation that the strategy seeks **pullbacks inside an established bullish regime**, rather than upside breakouts.

It still does not prove that any of these indicators appear literally in the Pine source.

## 4h same-bar reentry fingerprint

18 source-verifiable 4h reentries occurred in the exact same chart bar as the preceding exit.

All **18 / 18** reentry prices match the Binance bar **LOW** within 1 basis point.

Nearest OHLC classification:
- LOW: 18
- OPEN: 0
- HIGH: 0
- CLOSE: 0

This is highly consistent with TradingView broker-emulator historical OHLC tick behavior combined with recalculation/order placement after an order fill.

Official TradingView documentation states that `calc_on_order_fills=true` causes a strategy to recalculate immediately after fills and can enable same-bar reentry on historical bars. TradingView also warns that such behavior can access historical OHLC information in ways that can create unrealistically favorable results/lookahead bias depending on implementation.

Therefore the correct classification is:

**CALC_ON_ORDER_FILLS_OR_EQUIVALENT_INTRABAR_RECALCULATION — STRONGLY SUSPECTED, NOT PROVEN WITHOUT SOURCE/SETTINGS.**

## Economic contribution of suspicious same-bar reentries

There are 19 same-bar 4h reentries in the trade list; 18 are closed and one may be outside source-verifiable coverage depending on archive availability.

For the 18 closed same-bar reentry trades:
- winners: 8
- losers: 10? [see note below]
- net contribution is small relative to total 4h closed PnL.

A separate exact ledger audit should be treated as authoritative for the contribution calculation; this section intentionally does not use the source-reconstruction probe itself to adjudicate PnL.

## Scientific interpretation

Two independent forensic layers now point to the same architecture:

1. ordinary entries are next-bar-open market fills;
2. 4h same-bar reentries map exactly to historical LOW ticks.

This means exact Pine strategy properties are critical. Reproduction must explicitly test:
- `calc_on_order_fills`;
- Bar Magnifier;
- `process_orders_on_close`;
- `calc_on_every_tick`;
- custom vs built-in exit logic.

## Verdict

**ENTRY ARCHETYPE STRONGLY NARROWED: BULLISH REGIME + SHORT-HORIZON PULLBACK.**

**HISTORICAL INTRABAR RECALCULATION RISK: HIGH / REQUIRES SOURCE VERIFICATION.**

**EDGE: UNPROVEN.**

No promotion, live trading, exchange mutation or main merge is authorized.
