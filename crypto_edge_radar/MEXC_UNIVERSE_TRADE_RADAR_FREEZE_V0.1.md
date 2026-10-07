# MEXC UNIVERSE TRADE RADAR — OPERATOR FILTER FREEZE V0.1
Date: 2026-10-07
Mode: PUBLIC / READ-ONLY / NO ORDERS

Objective: scan the liquid MEXC USDT perpetual universe without choosing an asset first and return only current operator setups that pass execution and signal filters.

## Universe
- MEXC linear USDT perpetuals only.
- state=0, futureType=1, apiAllowed=true.
- minimum 24h quote amount: 20,000,000 USDT.
- examine at most top 60 contracts by 24h quote amount.

## Execution filters
- current public ticker/depth/funding only.
- top-of-book spread <= 5 bps.
- validation target about 75 USDT notional, quantized to contractSize/volUnit/minVol.
- current entry visible-book impact <= 2 bps.
- MEXC API taker fee authority: 8 bps per fill, therefore 16 bps round-trip fee drag.
- current absolute funding <= 5 bps per settlement unless funding is favorable to the proposed direction.
- no funding settlement inside the next 30 minutes for a new operator setup.

## Closed-candle signal families
Only CLOSED 15m and 1h MEXC contract candles are used.

### A. BREAKOUT
LONG:
- 1h close > EMA20 > EMA50;
- 15m close > EMA20 > EMA50;
- 15m close > prior-20-candle high;
- last 15m volume >= 1.5x median prior-20 volume;
- RSI14 55..72;
- close no more than 1.5 ATR14 above EMA20.

SHORT is symmetric:
- 1h close < EMA20 < EMA50;
- 15m close < EMA20 < EMA50;
- 15m close < prior-20-candle low;
- volume >= 1.5x median prior-20;
- RSI14 28..45;
- close no more than 1.5 ATR14 below EMA20.

### B. TREND_RETEST
LONG:
- 1h close > EMA20 > EMA50;
- 15m EMA20 > EMA50;
- last 15m close is within 0.35 ATR14 of EMA20;
- last 15m candle closes green;
- RSI14 48..62;
- last 15m volume >= median prior-20 volume.

SHORT is symmetric:
- 1h close < EMA20 < EMA50;
- 15m EMA20 < EMA50;
- last close within 0.35 ATR14 of EMA20;
- last candle closes red;
- RSI14 38..52;
- volume >= median prior-20.

No other setup family can rescue a failed scan.

## Risk construction
- entry = current executable ask for LONG / bid for SHORT using visible-book VWAP for quantized validation size.
- LONG stop = min(last-5 closed 15m lows, entry - 1.2*ATR14).
- SHORT stop = max(last-5 highs, entry + 1.2*ATR14).
- reject if gross stop distance <0.6% or >3.5%.
- TP1 = 1.6R gross.
- TP2 = 2.5R gross.
- conservative observable friction budget = 16 bps fees + current spread + 2x current entry impact.
- require net TP1 reward / (gross stop risk + friction) >=1.25.
- require net TP2 reward / (gross stop risk + friction) >=2.0.

## Verdict
TRADEABLE_CANDIDATE only if every source, signal, execution, funding and risk gate passes.
At most 3 candidates are reported, ranked by:
1. signal family (BREAKOUT before TREND_RETEST only when both pass equally);
2. net TP2 R:R;
3. 24h quote volume;
4. lower friction.

If none pass: NO_TRADE / RADAR_EMPTY.

No live trading, authentication, private endpoints, account reads, wallets, exchange mutation, or main merge.
