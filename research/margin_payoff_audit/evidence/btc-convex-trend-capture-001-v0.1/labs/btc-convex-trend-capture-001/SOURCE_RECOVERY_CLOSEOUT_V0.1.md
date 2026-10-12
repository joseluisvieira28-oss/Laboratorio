# BTC-CONVEX-TREND-CAPTURE-001 — SOURCE RECOVERY CLOSEOUT V0.1

**Date:** 2026-09-23  
**Status:** EXACT USER-SUPPLIED PINE SOURCE RECOVERED / R0 OPEN

## Recovered source

The operator supplied the Pine Script used by the TradingView strategy:
**Quant Trailing v5 (Payoff Invertido) - BTC**

Pine version: **6**.

The source is now preserved in this lab as:
`SOURCE_RECOVERED_V0.1.pine`.

The source code supersedes previous reverse-engineering guesses whenever there is a conflict.

## Exact entry architecture

The source defines:

- 20-bar SMA and standard deviation;
- Z-score entry threshold: -2.0;
- RSI14 < 30;
- close below 20-bar lower 2-sigma band;
- volume > SMA20(volume);
- regime filter: close > SMA200;
- score >= 3;
- long-only when flat.

### Important algebraic simplification

With the supplied defaults:

`zScore < -2`

and

`close < SMA20 - 2 × STDEV20`

are the same condition (for positive standard deviation).

Therefore `sinalZ` and `sinalBB` are not independent evidence. They double-count the same 20-bar price-extreme condition.

Under the default parameters, `score >= 3` simplifies to approximately:

**close > SMA200  
AND close < SMA20 - 2σ20  
AND (RSI14 < 30 OR volume > SMA20(volume))**

This directly explains the earlier forensic fingerprint of:
- bullish long-horizon regime;
- short-horizon pullback/oversold state;
- non-breakout entries.

## Exact exit architecture

- initial stop: 4% below average entry;
- running peak: maximum chart-bar high seen while in position;
- trail level: 12% below running peak;
- the code chooses the trail only when current close profit is >= 5%.

### Critical implementation detail

The 5% activation is **not latched**.

The code is:

`stopFinal = lucroAtual >= ativaTrail ? max(precoTrail, precoStopIni) : precoStopIni`

There is no persistent boolean such as `trailAtivo`.

Therefore the implementation is not:
> once profit reaches +5%, trail remains active forever.

It is:
> on each script execution, use the trailing stop only while current close-based profit is >= +5%; otherwise revert to the initial 4% stop.

This explains why some eventual -4.19% losers previously reached large positive MFE. A trade can enter the trailing regime, later fall below the +5% close threshold, and revert to the original hard stop.

This also explains why the earlier fixed one-way activation reconstruction failed.

## Strategy properties recovered from source and operator screenshot

Source:
- initial capital = 10,000 USDT;
- percent-of-equity sizing = 95%;
- commission = 0.10% per side;
- margin_long = 0;
- slippage not declared in source.

Operator Properties screenshot additionally shows:
- initial capital 10,000 USDT;
- order size 95% of equity;
- pyramiding = 1;
- historical bar detail = default 4 ticks per bar;
- commission = 0.1% percentage;
- long leverage displayed as Infinity;
- short leverage 1x;
- slippage = 0 ticks;
- limit execution at requested price;
- order execution delay = one tick.

The screenshot's Script execution selection appears to include bar-close execution plus order-fill recalculation. Because the visible label is truncated in the screenshot, this field must be verified by behavior/source reproduction rather than text inference alone.

## New R0 question

The source itself does NOT declare:
- calc_on_order_fills;
- calc_on_every_tick;
- calc_on_every_history_tick;
- process_orders_on_close;
- use_bar_magnifier.

TradingView allows users to override relevant execution defaults in Properties.

The already-observed same-bar historical reentries therefore become a direct execution-integrity test.

## Scientific status

**SOURCE_CODE_MISSING** is closed.

New classification:

**SOURCE_RECOVERED / R0_REPRODUCTION_OPEN / EXECUTION_SETTINGS_STILL_REQUIRE_VALIDATION**

No edge claim or promotion is created by source recovery.
