# MEXC ↔ BINANCE NVIDIA EQUITY-PERP — SOURCE GATE V0.8

Date: 2026-10-04
Status: SOURCE-ONLY / OUTCOMES CLOSED / RESEARCH-ONLY

## Mission

Determine whether MEXC `NVIDIA_USDT` and Binance `NVDAUSDT` form a defensible public/no-auth cross-venue pair for a later equity-perpetual lead/lag or dislocation study.

## Public product identity

MEXC publicly lists `NVIDIA_USDT` as an NVDA-linked perpetual.

Binance publicly announced `NVDAUSDT` Equity Perpetual on 2026-03-26 and states that it tracks NVIDIA Corporation common stock (Nasdaq: NVDA), trades 24/7, settles in USDT and supports up to 10x leverage.

## Allowed

Public/no-auth market data only:
- MEXC Futures contract metadata, index/market ticker and klines;
- Binance USD-M Futures exchangeInfo, book ticker, premium/mark data and klines.

## Prohibited

- historical return scoring;
- lead/lag outcome testing;
- accounts/private endpoints;
- API keys;
- orders;
- wallets;
- exchange mutation;
- live-trading authorization.

## PASS requirements

`MEXC_BINANCE_NVDA_SOURCE_PASS` requires:

1. exact MEXC `NVIDIA_USDT` contract exists and is publicly readable;
2. exact Binance `NVDAUSDT` contract exists and identifies NVDA as the underlying/base asset;
3. both expose live public/no-auth price data;
4. live price scales are consistent within 500 bps;
5. at least one venue exposes one-minute public klines for the pair and the other exposes compatible timestamped one-minute klines;
6. no account/private/authenticated request is used.

A PASS authorizes only a new pre-outcome freeze. It does not authorize historical scoring by this gate.
