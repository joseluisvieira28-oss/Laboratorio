# MEXC NVIDIA CROSS-VENUE — SOURCE GATE V0.6

Date: 2026-10-04
Status: SOURCE-ONLY / OUTCOMES CLOSED / RESEARCH-ONLY

## Trigger

MEXC public `contract/detail` for `NVIDIA_USDT` reports external index origins including:

- `BINANCE_FUTURE`
- `BITGET_FUTURE`
- `BINANCETICKER`
- `PYTH`
- `KAIKO`

Binance and Bitget both publicly list `NVDAUSDT` perpetual futures tracking NVIDIA Corporation common stock.

## Mission

Establish whether MEXC `NVIDIA_USDT`, Binance Futures `NVDAUSDT`, and Bitget Futures `NVDAUSDT` provide defensible, public, timestamped, same-scale market data suitable for a later cross-venue lead/lag study.

## Allowed

Public/no-auth market data only:
- MEXC contract detail, ticker/index, and public klines;
- Binance USDⓈ-M Futures public exchange info/ticker/klines;
- Bitget USDT-FUTURES public instrument/ticker/candles.

## Prohibited

- historical directional outcome scoring;
- lead/lag performance testing;
- accounts;
- API keys;
- private endpoints;
- wallets;
- orders;
- mutation;
- live trading.

## PASS requirements

`NVDA_CROSSVENUE_SOURCE_PASS` requires:
1. exact NVDA instrument identity on all three venues;
2. live price scale within 500 bps across venues at probe time;
3. public/no-auth 1m candles available on all three;
4. usable timestamps;
5. no private/authenticated endpoint.

A PASS does not authorize outcome access. A separate pre-outcome freeze is mandatory.
