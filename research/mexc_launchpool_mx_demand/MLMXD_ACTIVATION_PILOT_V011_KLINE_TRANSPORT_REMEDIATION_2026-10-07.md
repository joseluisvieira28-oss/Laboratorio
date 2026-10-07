# MLMXD ACTIVATION PILOT V0.1.1 — HISTORICAL KLINE TRANSPORT REMEDIATION
Date: 2026-10-07
Status: TECHNICAL REMEDIATION AFTER INCOMPLETE V0.1 RUN

Parent run: 37624255115

## Preserved failed run
V0.1 completed with only 2/14 analyzable events because the CCXT OHLCV transport did not recover the frozen 2025 historical windows.
The V0.1 classification PILOT_NO_SIGNAL is preserved as the literal result of that incomplete transport run and is not deleted.

## Technical cause
Official MEXC Spot V3 kline documentation specifies public GET /api/v3/klines with startTime and endTime parameters for bounded historical queries.

## Permitted correction
For every one of the exact same 14 pre-frozen events:
- use public unauthenticated MEXC Spot GET /api/v3/klines;
- symbol MXUSDT and BTCUSDT only;
- interval 15m;
- startTime = exact frozen T0;
- endTime = T0 + 24h + one 15m bar;
- require exact candle-open timestamps;
- use the same entry and 1h/6h/24h evaluation timestamps;
- preserve the exact same classification gates, bootstrap seed and event list.

## Forbidden
- no event addition or deletion;
- no T0 change;
- no horizon change;
- no direction change;
- no alternate venue;
- no interpolation;
- no nearest-neighbor candle;
- no threshold/gate change;
- no result-conditioned filtering.

This remediation changes transport only, not science.
