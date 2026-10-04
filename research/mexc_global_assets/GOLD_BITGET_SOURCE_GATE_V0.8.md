# MEXC GOLD ↔ BITGET — SOURCE GATE V0.8

Date: 2026-10-04
Status: SOURCE-ONLY / OUTCOMES CLOSED / RESEARCH-ONLY

## Trigger

MEXC public `contract/detail` for `XAU_USDT` identifies external index origins including:

- `BINANCE_FUTURE`
- `BITGET_FUTURE`
- `BYBIT_FUTURE`
- `BINANCETICKER`

This gate narrows the next research family to the explicitly declared Bitget Futures source.

## Mission

Prove that MEXC `XAU_USDT` and Bitget USDT-FUTURES `XAUUSDT` expose defensible public/no-auth, same-scale, timestamped 1-minute market data suitable for a later cross-venue lead/lag study.

## Allowed

Public/no-auth market data only:
- MEXC contract detail, ticker and public klines;
- Bitget public instruments, ticker and public candles.

## Prohibited

- historical directional outcome scoring;
- lead/lag performance testing;
- account/API key/private endpoint reads;
- wallets;
- orders;
- exchange mutation;
- live trading.

## PASS requirements

`GOLD_BITGET_MEXC_SOURCE_PASS` requires all:

1. MEXC exact symbol `XAU_USDT`;
2. MEXC `indexOrigin` includes `BITGET_FUTURE`;
3. Bitget exact symbol `XAUUSDT` under USDT-FUTURES;
4. contemporaneous live prices are on the same scale and differ by < 500 bps;
5. both venues expose at least 10 public 1-minute candles in a 30-minute probe;
6. no authenticated/private source is used.

A PASS is source feasibility only. Historical outcomes remain CLOSED until a separate pre-outcome freeze is committed.
