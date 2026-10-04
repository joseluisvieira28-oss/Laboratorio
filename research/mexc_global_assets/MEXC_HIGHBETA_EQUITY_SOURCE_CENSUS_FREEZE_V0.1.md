# MEXC U.S. HIGH-BETA EQUITY SOURCE CENSUS V0.1 — PRE-OUTCOME FREEZE

Date: 2026-10-04
Status: SOURCE-ONLY / PRE-OUTCOME

Goal:
select the next independent U.S.-equity target for the already-frozen 5/3/1m FOLLOW transfer rule, without using any signal outcome.

Frozen candidate priority:
1. MSTR
2. COIN
3. PLTR
4. META
5. AMZN
6. MSFT

Selection rule:
choose the first candidate in that order which proves all public/free source requirements on 2026-09-30:
- exactly one identifiable MEXC stock-futures contract;
- MEXC 1m regular-session transport over 14:30–19:00 UTC;
- Binance ticker `<TICKER>USDT` 1m archive transport over the same window;
- Bitget `<TICKER>USDT` live identity plus historical 1m transport;
- MEXC index metadata includes the same multi-source stock-futures structure or otherwise records the exact declared origins.

The source-verification date is burned from any later outcome sample.

No return, shock, lag, threshold performance, direction performance, win/loss or PnL may be calculated in the source census.

If no candidate passes, verdict:
`SOURCE_BLOCKED_HIGHBETA_EQUITY_CENSUS`

No private endpoints, account reads, wallets, orders, exchange mutation or live trading are authorized.
