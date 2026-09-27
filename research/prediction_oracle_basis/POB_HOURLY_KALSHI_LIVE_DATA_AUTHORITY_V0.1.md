# POB-HOURLY-KALSHI-LIVE-DATA-001 — SOURCE AUTHORITY V0.1

Date: 2026-09-27
Parent: PREDICTION-ORACLE-BASIS-001
Branch: prediction-oracle-basis-v0.1
Status: FROZEN_PRE_SOURCE_PROBE / OUTCOME_BLIND / RESEARCH_ONLY

## Trigger

POB-HOURLY-SYNC-CAPTURE-001 reached:
- SOURCE_TRANSPORT_READY_BRTI_ROUTE_UNRESOLVED
- canonical run 36341997042
- 10/10 synchronized bundles complete
- max bundle span 616 ms <= 3000 ms
- zero matured outcomes
- zero economic outputs

The remaining source question is whether Kalshi exposes the underlying BTC settlement-reference live data through its documented event live-data endpoint without authenticated trading access.

## First-party documentation basis

Kalshi documents:
GET /trade-api/v2/live_data/events/{event_ticker}

as event-keyed live data capable of serving crypto price charts. The API documentation separately lists authenticated CF Benchmarks REST/WebSocket passthrough routes. This probe tests only the public event live-data route.

## Deterministic target

At probe start:
1. enumerate open KXBTCD markets using public GET /markets;
2. retain events with a future close time;
3. select the earliest future KXBTCD event_ticker lexically among markets sharing the earliest close instant;
4. query exactly:
   GET /live_data/events/{event_ticker}

No quote, strike, probability, volume, outcome or price may influence target selection.

## Allowed output

Persist only:
- request URL;
- HTTP status;
- content type;
- bytes;
- raw SHA256;
- JSON top-level keys;
- recursive key paths;
- array lengths;
- non-price provenance labels from keys whose names contain type, source, symbol, ticker, index, benchmark, provider, unit, name;
- whether strings BRTI / CF Benchmarks / BTC appear in the response text;
- schema classification.

Do NOT persist numerical underlying/reference prices, timeseries values, candlestick OHLC, market odds, or settlement outcomes.

## Classifications

- KALSHI_EVENT_LIVE_DATA_BRTI_PUBLIC_PASS:
  public 2xx machine-readable response and explicit first-party schema/text evidence identifies BRTI or CF Benchmarks as the crypto reference.

- KALSHI_EVENT_LIVE_DATA_PUBLIC_REFERENCE_UNPROVEN:
  public machine-readable response exists but BRTI / CF Benchmarks identity is not explicit.

- KALSHI_EVENT_LIVE_DATA_AUTH_REQUIRED:
  endpoint rejects the anonymous request with 401/403.

- KALSHI_EVENT_LIVE_DATA_TECHNICAL_FAILURE:
  other transport/schema failure.

## Hard firewall

No PnL, spread, package economics, win rate, expected return, arbitrage calculation, comparison against prediction-market quotes, matured outcome access, orders, authenticated trading endpoint, exchange mutation, capital, wallet action, leverage or main merge.

This source probe cannot promote the candidate.
