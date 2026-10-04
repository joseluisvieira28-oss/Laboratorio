# MEXC GOLD SOURCE ACQUISITION AMENDMENT V0.7.2

Date: 2026-10-04
Status: PRE-OUTCOME TECHNICAL SOURCE CORRECTION

## Incident

Run 37194537259 passed the Binance Vision acquisition step but the GitHub-hosted runner received HTTP 403 from the Bybit V5 API due CloudFront country restrictions.

No historical research outcomes were opened.

## Bybit public archive route

Bybit's public market-data ecosystem exposes downloadable historical market data and public trading-history files through the `public.bybit.com` domain.

For source verification only, V0.7.2 will attempt:

`https://public.bybit.com/trading/XAUUSDT/XAUUSDT2026-09-30.csv.gz`

The date 2026-09-30 is outside the future Gold discovery sample.

The gate may:
- verify HTTP accessibility;
- verify gzip/CSV structure;
- verify symbol/date identity;
- count rows;
- record SHA-256.

It may NOT score returns from the verification day.

## Scientific invariants

UNCHANGED:
- target MEXC `XAU_USDT`;
- external venue family Binance + Bitget + Bybit;
- no source weighting from outcomes;
- no historical research outcome opened in source gate;
- no account/private endpoint;
- no live trading/orders/mutation.

If the Bybit static archive is not available for XAUUSDT, the 3-venue family remains SOURCE_BLOCKED. A later 2-venue family, if pursued, must be a distinct preregistered hypothesis.
