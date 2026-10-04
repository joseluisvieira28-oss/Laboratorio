# MEXC GOLD MULTI-VENUE CONSENSUS — SOURCE GATE V0.7

Date: 2026-10-04
Status: SOURCE-ONLY / OUTCOMES CLOSED / RESEARCH-ONLY

## Mission

Prove a public/free source chain for MEXC Gold Futures before opening any cross-venue outcomes.

Target:
- MEXC: `XAU_USDT`
- external component symbol: `XAUUSDT`
- expected MEXC index-origin venues: Binance, Bitget, Bybit.

## Public source candidates

MEXC:
- `GET /api/v1/contract/detail?symbol=XAU_USDT`
- `GET /api/v1/contract/index_price/XAU_USDT`

Binance USDⓈ-M Futures:
- `GET https://fapi.binance.com/fapi/v1/ticker/bookTicker?symbol=XAUUSDT`

Bybit V5:
- `GET https://api.bybit.com/v5/market/tickers?category=linear&symbol=XAUUSDT`

Bitget Futures:
- `GET https://api.bitget.com/api/v2/mix/market/ticker?symbol=XAUUSDT&productType=USDT-FUTURES`

All are public/no-auth market-data endpoints.

## PASS requirements

`MEXC_GOLD_MULTIVENUE_SOURCE_PASS` requires all:

1. MEXC `XAU_USDT` exists and its public metadata declares the expected external index-origin set;
2. Binance `XAUUSDT` public BBO is available;
3. Bybit `XAUUSDT` public BBO is available;
4. Bitget `XAUUSDT` public BBO is available;
5. each external mid is on the same economic price scale as the MEXC index;
6. no account/private/authenticated endpoint is used.

Because commodity markets may have session closures, this source gate does not require weekend freshness. It records timestamps and scale only.

## Prohibited

- historical outcome scoring;
- lead/lag testing;
- source weighting from outcomes;
- account reads;
- API keys;
- wallets;
- orders;
- exchange mutation;
- live trading.

Even after SOURCE PASS, historical outcomes remain CLOSED until a separate pre-outcome freeze is committed.
