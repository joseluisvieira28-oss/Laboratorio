# NVIDIA CROSS-VENUE — SOURCE ROUTE AMENDMENT V0.8.1

Date: 2026-10-04
Status: SOURCE-ONLY / OUTCOMES CLOSED

## V0.8 incident

The MEXC ↔ Binance public source probe passed its local preflight but the GitHub Actions runner received HTTP 451 from Binance USD-M Futures:

`Service unavailable from a restricted location...`

This is a runner/network eligibility blocker, not a scientific NO_EDGE result.

No historical returns, lead/lag outcomes or directional performance were opened.

## V0.8.1 source route

Replace the external public market-data leg with Bitget public Futures market endpoints.

Target:
- MEXC: `NVIDIA_USDT`
- Bitget: exact `NVDAUSDT` if publicly listed; otherwise fail closed unless a unique NVDA/NVIDIA contract identity is proven from Bitget contract metadata.

## Public endpoints

Bitget:
- `GET /api/v2/mix/market/contracts`
- `GET /api/v2/mix/market/ticker`
- `GET /api/v2/mix/market/candles`

MEXC:
- `GET /api/v1/contract/detail`
- `GET /api/v1/contract/index_price/NVIDIA_USDT`
- `GET /api/v1/contract/ticker`
- `GET /api/v1/contract/kline/NVIDIA_USDT`

## PASS requirements

`MEXC_BITGET_NVDA_SOURCE_PASS` requires:
1. exact MEXC NVIDIA contract;
2. unique Bitget NVDA/NVIDIA futures identity;
3. public/no-auth live prices on both legs;
4. price scale within 500 bps;
5. public/no-auth 1m candles on both legs;
6. timestamped source payloads;
7. no accounts, credentials, wallets, orders or mutation.

A PASS is source authority only. Historical outcomes remain CLOSED until a separate freeze.

## Governance

No main merge.
No live trading.
No authenticated account data.
No orders.
No exchange mutation.
No outcome scoring.
