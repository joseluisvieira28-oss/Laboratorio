# BTC-OPTIONS-VRP-001 — optionsDX Public Sample Source Closeout V0.2

Date: 2026-09-19  
Branch: `btc-options-vrp-exec-bbo-v0.2`  
Probe: `OVRP-EXEC-SOURCE-OPTIONSDX-PROBE-002`  
Canonical run: `35456986140`  
Artifact ID: `10588098978`  
Artifact digest: `sha256:e95ec8bc6a9c9fd7920b8c4a681897e6a80e991bd2944edc18846ede113e037a`

## Final classification

**OPTIONSDX_SAMPLE_SCHEMA_FEASIBLE**

This is source-only. No option price value was emitted into the receipt and no execution return, PnL or performance outcome was calculated.

## Public-sample evidence

The frozen public sample returned:
- HTTP 200
- 21,385,261 bytes
- 94,066 rows
- 28 columns
- 458 unique option instruments
- sample timestamps spanning 2021-06-01 04:00:46 UTC through 21:55:48 UTC

Required fields were all present after documented provider-specific header normalization:
`QUOTE_UNIXTIME, INSTRUMENT_NAME, EXPIRY_UNIX, DTE, OPTION_RIGHT, STRIKE, BID_SIZE, BID_PRICE, ASK_PRICE, ASK_SIZE, UNDERLYING_PRICE, DELTA, MARK_IV`.

## Coverage fit

The provider publicly lists BTC Deribit monthly data from 2021-06 through 2024-09 and frequencies including minutely snapshots.

The already-frozen BBO MVE calendar remains 192 Thursday anchors from 2021-04-01 through 2024-11-28. The provider's published date span intersects **174 of those 192 anchors**. The calendar is not changed to fit the provider; outside-coverage anchors remain source-missing/non-executable.

The frozen minimum executable-N remains 120. Therefore the provider's published date span is **calendar-feasible in principle**, but actual contract/BBO executability still requires a paid-data source gate before any performance run.

## Provider comparison state

- Tardis: source structure proven; full historical access commercial.
- CoinAPI: frozen route exists, but zero-network readiness V0.2 found `COINAPI_CREDENTIAL_ABSENT`; no network probe was attempted.
- optionsDX: public sample schema proven and published historical span is large enough in principle for the frozen N gate.
- No purchase has been authorized.

## Next valid action

Run a source-fit probe on the free sample only:
- 25-35 DTE same-strike call/put pairing;
- point-in-time timestamp density;
- nonzero bid/ask and size availability;
- no returns or PnL.

Only after that may procurement be considered, and procurement still requires separate user authorization.

## Safety

No purchase, key use, 2025/2026 access, live trading, exchange mutation, wallet access, main merge or post-outcome tuning.
