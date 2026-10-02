# MEXC EVENT FUTURES LAB — PAYOUT / SETTLEMENT SOURCE FREEZE V0.6

Date: 2026-10-02
Status: SOURCE-FIRST / PROSPECTIVE / RESEARCH-ONLY / FAIL-CLOSED

## Mission

Attack the missing exact-product layer for MEXC Event Futures without trading:

- current Up payout;
- current Down payout;
- asset;
- event horizon / time unit;
- displayed index price;
- observation timestamp;
- later expiry/settlement index and direction outcome;
- evidence chain sufficient to distinguish exact Event Futures observations from standard-futures proxy data.

## Authoritative product facts frozen before collection

Official MEXC material states that:
- Event Futures offer Up and Down predictions;
- documented expiration choices include 10m, 30m, 1h and 1d;
- profit = principal × payout;
- payout may fluctuate with asset volatility / market risk and is fixed for a submitted trade;
- current Up/Down payout values are visible in the trading area;
- settlement is determined by the underlying price index at expiry;
- Event Futures currently do not support API trading.

## Hard boundaries

This V0.6 source attack MUST NOT:
- place an Event Futures order;
- click Up or Down;
- fill a quantity;
- submit any form;
- use authenticated account mutation;
- call POST/PUT/PATCH/DELETE endpoints;
- use private API credentials;
- merge to main;
- infer historical payout values from today's payout;
- claim exact product edge from standard-futures proxy data.

Browser reconnaissance is read-only:
- GET navigation only;
- DOM observation;
- GET/XHR response observation;
- websocket frame observation;
- no form submission.

## Public trading pages frozen for reconnaissance

Asset routes:
- BTC_USDT
- ETH_USDT
- NVIDIA_USDT
- MUSTOCK_USDT
- SPCXSTOCK_USDT

Canonical public route pattern:
`https://www.mexc.com/futures/event-futures/{symbol}`

## Source gate

PASS_EXACT_CURRENT_PAYOUT requires at least one reproducible public observation containing:
- asset identity;
- Up payout numeric value;
- Down payout numeric value;
- observation time;
- evidence source (DOM, public GET response, or public websocket message).

PARTIAL requires Event Futures-specific public data but one or more required fields are missing.

BLOCKED means no defensible public source for current payout is found.

## V0.6 phases

A. Static bundle reconnaissance.
B. Browser DOM + network + websocket observation.
C. If A/B identifies an exact public current-payout source, build a prospective collector.
D. Collector records exact current payouts and public index observations only.
E. Settlement resolver remains separate and may use only a source proven to match Event Futures settlement semantics.
F. No hypothesis test begins until a minimum prospective sample rule is frozen in a later version.

## Prospective record schema

- observed_at_utc
- asset_display
- source_symbol
- event_horizon
- up_payout
- down_payout
- event_index_price
- source_kind
- source_url_or_channel
- source_payload_sha256
- expiry_target_utc (if exposed)
- settlement_index_price (later)
- settlement_observed_at_utc (later)
- outcome (UP/DOWN/TIE later)
- source_confidence
- notes

No trading decision field belongs in V0.6 source collection.
