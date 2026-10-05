# MEXC GLOBAL-ASSET — INTRADAY LARGE-SHOCK CATCH-UP
## SOURCE GATE FREEZE V1.0

Date: 2026-10-05
Status: FROZEN BEFORE OUTCOMES

Purpose:
Verify that the already source-bound 35 MEXC global-asset contracts and their Binance + Bitget external leaders have public/free 1-minute historical coverage across the full U.S. regular session, rather than only the pre-open anchor used by V1.1.

Authority inherited:
- candidate identity and symbol transport: `MEXC_PREOPEN_SHOCK_SOURCE_BINDING_V1.1.json`
- 35 candidates only
- no additions/removals based on outcomes

Burned source-only date:
- 2026-09-30
- this date is permanently excluded from later outcome evaluation

Coverage window:
- closed-candle timestamps from 13:30 through 20:00 UTC
- MEXC public contract kline endpoint
- Binance public data archive
- Bitget public futures historical candles
- 1-minute cadence

SOURCE PASS per asset:
- all three venues return usable 1-minute closes
- >= 390 unique closed-candle timestamps in the frozen session window on each venue
- exact closed-candle timestamps 13:30 and 20:00 UTC present on each venue

Family SOURCE PASS:
- all 35 inherited candidates pass

Strict boundaries:
- source only; no signal returns, forward returns or PnL may be computed
- outcomes_opened = 0
- no private endpoints
- no account reads
- no orders
- no wallets
- no exchange mutation
- no live trading
