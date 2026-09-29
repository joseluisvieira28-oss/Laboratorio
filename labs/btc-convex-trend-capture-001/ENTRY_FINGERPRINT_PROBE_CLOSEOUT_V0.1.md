# BTC-CONVEX-TREND-CAPTURE-001 — ENTRY FINGERPRINT PROBE CLOSEOUT V0.1

**Date:** 2026-09-23  
**Run:** 35898821781  
**Artifact:** 10768516834  
**Artifact SHA-256:** e512eada5ffc1ccdde4a996bc57de7b1fb2d829d4750c018bf55e8c99e5d075e  
**Status:** FORENSIC SOURCE PROBE PASS / BREAKOUT-LIKE STANDARD FAMILIES NOT SUPPORTED

## Coverage

Official Binance USD-M BTCUSDT monthly futures klines were acquired for the available historical range.

Matched entries:
- 5m: 172 / 188
- 15m: 149 / 160
- 4h: 60 / 62
- total: 381 / 410

The 29 unmatched entries are all in 2019 months where the requested Binance USD-M monthly archive paths returned 404. They are preserved as source-unavailable, not silently removed.

Flat-state controls:
- 5m: 47,923 bars
- 15m: 39,583 bars
- 4h: 9,670 bars

## Fill fingerprint

For every matched 5m and 15m entry, reported entry price is within 1 bp of the Binance entry-bar OPEN.

For 4h:
- all matched entries except same-bar reentries are within 1 bp of the Binance bar OPEN;
- the same-bar reentry cluster has intrabar prices and is treated separately.

This strongly supports the default TradingView pattern where a signal calculated on the prior closed bar creates a market order filled at the next bar open for ordinary entries.

## Standard-family fingerprint

The probe predeclared a limited set of standard families only:
- EMA states/crosses;
- MACD;
- RSI;
- momentum;
- Donchian breakouts;
- standard Supertrend(10,3);
- close-vs-previous-high.

### Long-horizon trend context

At the prior bar:

- EMA20 > EMA50:
  - 5m: 95.3%
  - 15m: 94.6%
  - 4h: 88.3%

- EMA50 > EMA200:
  - 5m: 77.9%
  - 15m: 83.2%
  - 4h: 93.3%

This is materially more prevalent at entries than across flat control bars.

### Short-horizon momentum at entry

At the prior bar:

- MACD line > signal:
  - 5m: 0%
  - 15m: 0%
  - 4h: 0%

- RSI14 > 50:
  - 5m: 1.2%
  - 15m: 1.3%
  - 4h: 3.3%

- 20-bar momentum positive:
  - 5m: 3.5%
  - 15m: 4.0%
  - 4h: 11.7%

- Donchian 20/55 breakout:
  - essentially absent from the entry fingerprint.

## Forensic interpretation

The observed pattern is inconsistent with a simple classic breakout / bullish-momentum entry.

The strongest descriptive fingerprint is instead:

**longer-horizon bullish structure + short-horizon pullback/weakness.**

A post-hoc conjunction using information discovered in this V0.1 probe would capture many entries, but it is contaminated and receives zero scientific credit. It may be used only to reverse-engineer the missing source.

## Important non-edge boundary

This probe does NOT establish that EMA20/50, EMA50/200, MACD, RSI or momentum are the actual Pine rule.

They may merely correlate with a different hidden condition.

No indicator parameter may be optimized on these observed BTC entries and then counted as validation.

## Next forensic action

A V0.2 source-reconstruction diagnostic may inspect:
- the complements of the already-tested momentum states;
- standard pullback relationships to moving averages;
- simple conjunctions explicitly labeled POST-HOC FORENSIC ONLY;
- 4h same-bar reentry price mapping to historical OHLC ticks.

These diagnostics may narrow the code architecture but create zero promotion credit.

## Verdict

**ENTRY ARCHETYPE NARROWED TO TREND-CONTEXT / PULLBACK-LIKE.**

**EXACT ENTRY RULE REMAINS SOURCE-BLOCKED.**

No live trading, exchange mutation, promotion or main merge is authorized.
