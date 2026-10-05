# BINANCE-LISTING-INFORMATION-CASCADE-001 — V0.9 SHORT-HORIZON DELAYED-ENTRY POOLED OOS FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE ANY MARKET OUTCOME ACCESS FOR THE 15 VALIDATION OBSERVATIONS

## Development rationale
The V0.8 retrospective 2025 delayed-entry audit failed the frozen H15 mechanism gate, but showed median H5 = +1.641% after entry at the next minute boundary. This observation is DEVELOPMENT evidence only.
V0.9 tests the new short-horizon hypothesis on observations whose delayed-entry outcomes remain unopened.

## Validation set
Pool ALL source-valid observations from the already-completed source-only gates for calendar 2023 and the 2026 interval through 2026-10-04.
No event is selected by outcome.
Total frozen n = 15.

### 2023
1. FLOKI — BITGET — FLOKIUSDT — T0 2023-05-05T11:20:04.106Z
2. PEPE — BITGET — PEPEUSDT — same T0
3. PENDLE — BITGET — PENDLEUSDT — 2023-07-03T06:22:15.567Z
4. ORDI — BITGET — ORDIUSDT — 2023-11-07T06:44:13.500Z
5. BLUR — KUCOIN — BLUR-USDT — 2023-11-24T06:09:47.186Z
6. 1000SATS — KUCOIN — SATS-USDT — 2023-12-12T06:09:30.579Z
7. BONK — BITGET — BONKUSDT — 2023-12-15T03:58:33.180Z

### 2026
8. ZKP — KUCOIN — ZKP-USDT — 2026-01-07T10:39:06.580Z
9. ROBO — BITGET — ROBOUSDT — 2026-03-04T13:13:14.452Z
10. CFG — KUCOIN — CFG-USDT — 2026-03-16T10:22:39.260Z
11. XAUT — BITGET — XAUTUSDT — 2026-03-26T10:45:28.143Z
12. GENIUS — BITGET — GENIUSUSDT — 2026-05-22T07:18:35.961Z
13. AERO — BITGET — AEROUSDT — 2026-07-17T07:30:01.964Z
14. 牛来 — MEXC — 牛来USDT — 2026-09-09T11:30:19.513Z
15. HYPE — BITGET — HYPEUSDT — 2026-09-24T07:30:38.608Z

## Frozen trade definition
M = floor T0 to containing UTC minute.
LONG entry = OPEN of candle M+1m.
Primary exit = CLOSE of candle M+5m.
This is exactly 5 one-minute candles from M+1 through M+5 inclusive.
Primary return H5 = exit / entry - 1.
H15 and H60 may be recorded descriptively but are not promotion gates.
MFE5/MAE5 use M+1..M+5.
5m volume shock = M..M+4 volume / median non-overlapping 5m wall-clock baseline from T-24h through T-1h.

## Frozen V0.9 survival gate
ALL required:
- n >= 12 valid observations;
- median H5 > +0.50%;
- H5 positive hit rate >= 65%;
- median 5m volume shock >= 2x;
- leave-one-out median H5 remains >0;
- no single observation contributes >35% of summed positive H5.

If n<12 => SOURCE_BLOCKED_SHORT_HORIZON_OOS.
If n>=12 but any performance gate fails => NO_EDGE_SHORT_HORIZON_OOS.
All pass => SURVIVES_SHORT_HORIZON_OOS.

## Anti-tuning
No observation, venue, symbol, T0, entry time, exit horizon, threshold, direction or gate can be changed after this commit.
No additional years/events can be added to V0.9 after outcomes.
No fees/slippage/fill claim. Survival requires a separate cost/latency freeze before any execution claim.
No live trading, private endpoints, accounts, orders, wallets, exchange mutation or main merge.
