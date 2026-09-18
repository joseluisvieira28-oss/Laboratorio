# CROSS-VENUE-DIAMOND-REPLICATION-002 — OKX JAN-2025 RAW PAYLOAD ACQUISITION FREEZE — 2026-09-18

Status: FROZEN_BEFORE_ANY_HISTORICAL_FILE_URL_IS_FOLLOWED
Candidate: CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1
Venue: OKX
Instrument family: AVAX-USDT
Instrument type: SWAP

## Prior source evidence

Outcome-blind schema probing of /api/v5/public/market-data-history established that the accepted response contains:
- details[].groupDetails[].filename
- details[].groupDetails[].url
- details[].groupDetails[].sizeMB
- details[].groupDetails[].dateTs

No historical payload URL has yet been followed under this experiment.

## Frozen acquisition pilot

Window:
- begin inclusive: 2025-01-01T00:00:00Z
- end exclusive: 2025-02-01T00:00:00Z

Modules:
- 2 — 1-minute candlestick
- 3 — funding rate

Request:
- instType=SWAP
- dateAggrType=monthly
- instFamilyList=AVAX-USDT

Allowed action:
1. Query the exact public historical endpoint.
2. Extract only provider-returned groupDetails URL/filename/size/date metadata.
3. Follow only HTTPS URLs returned by that exact response.
4. Download original bytes without modification.
5. Persist original filename, byte length and SHA256.
6. Detect container/media type from magic bytes and filename extension only.
7. Do NOT decompress or parse market rows in this gate.

Hard failures:
- provider code != 0;
- no groupDetails URL;
- non-HTTPS URL;
- redirect/download failure;
- zero-byte payload;
- duplicate filename with conflicting hash;
- any request outside the frozen Jan-2025 window;
- any attempt to access 2026+.

## Outcome lock

Forbidden in this gate:
- opening candle OHLC values;
- opening funding-rate values;
- signal calculation;
- returns/PnL/expectancy/PF;
- direction-performance analysis;
- candidate tuning or venue selection;
- live trading, orders, exchange mutation, authenticated exchange APIs, wallets, alerts/webhooks, main merge.

If both module-2 and module-3 raw payloads are acquired with reproducible hashes, classify RAW_PAYLOAD_ACQUISITION_PASS and freeze a separate parser/source-validation contract before decompression.
