# BINANCE-MARGIN-BORROW-ACCESS-001 — EXECUTION COST PROVENANCE CLOSEOUT V0.1

Date: 2026-09-17  
Status: **CREDENTIAL_BOUND / SOURCE-ONLY**  
Branch: `binance-margin-borrow-access-v0.1`

## Finding

The legitimate Binance historical margin-interest route is:

`GET /sapi/v1/margin/interestRateHistory`

Official Binance Developer documentation classifies this endpoint as **USER_DATA** and signed. It requires an API key through `X-MBX-APIKEY` plus request signing. Binance's official API changelog records the historical-interest endpoint as added on 2021-03-05.

Official references:
- https://developers.binance.com/docs/margin_trading/borrow-and-repay/Margin-Account-Borrow-Repay
- Binance Developer API change log entry for 2021-03-05.

## Canonical classification

**CREDENTIAL_BOUND**

This is not `UNAVAILABLE`: a legitimate historical route exists. It is not `PUBLIC_HISTORICAL_SOURCE_AVAILABLE`: the legitimate route requires authenticated USER_DATA credentials.

## Safety

No Binance API key, signature, account, wallet or authenticated exchange access was used. No historical borrow-rate values or historical borrow-inventory values were opened. Current rates/current inventory were not substituted for historical event-time conditions.

## Scientific consequence

Per the frozen EVENT SOURCE ADJUDICATION AUTHORITY V0.1, `CREDENTIAL_BOUND` may permit a separately frozen **non-executable research Discovery**. It does **not** permit an after-cost strategy claim, executable-strategy approval, live promotion, or trading deployment. Any such step requires a separate cost-resolution gate with legitimate point-in-time historical cost/availability evidence.
