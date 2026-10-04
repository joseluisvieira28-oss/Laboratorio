# MEXC GOLD SOURCE ACQUISITION AMENDMENT V0.7.1

Date: 2026-10-04
Status: PRE-OUTCOME TECHNICAL SOURCE CORRECTION

## Incident

Source-gate run 37194455766 failed before any historical outcome access.

GitHub-hosted runner received HTTP 451 from:

`https://fapi.binance.com/fapi/v1/ticker/bookTicker?symbol=XAUUSDT`

Reason returned by Binance:
service unavailable from the runner's restricted location.

This is an acquisition-route blocker, not a scientific result.

## Source correction

Binance publishes an official public-data archive at:

`https://data.binance.vision`

Its USD-M Futures kline files are documented as data from the Binance `/fapi/v1/klines` endpoint.

For Binance source availability V0.7.1 will use an official archived XAUUSDT Min1 file from a source-verification day outside the planned discovery window:

`2026-09-30`

This source probe may verify archive accessibility, ZIP integrity, CSV structure and symbol/interval/date identity.

It may NOT score returns or use the source-verification day as a research outcome.

## Scientific invariants

UNCHANGED:
- MEXC target `XAU_USDT`;
- external component identity `XAUUSDT`;
- Binance / Bitget / Bybit source family;
- no historical outcome scoring in the source gate;
- no account/private endpoints;
- no trading/orders/mutation.

The later discovery window, if source gate passes, must begin no earlier than 2026-10-01 so the Binance verification day remains outside the outcome sample.
