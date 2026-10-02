# ETF-CME EVENT FUTURES TRANSFER — V1.0 SOURCE CLOSEOUT / V1.0.1 REMEDIATION FREEZE

Date: 2026-10-02

## V1.0 result classification

V1.0 successfully retrieved:
- 261 CFTC observations;
- 260 independently derived ETF-CME signals;
- 156 discovery-period signals;
- 53 OOS-period signals;
- 209 MEXC public index-price query responses with zero HTTP/source exceptions.

However, **zero exact entry/expiry proxy timestamps were usable in every horizon**.

Therefore:

**V1.0 = SOURCE_BLOCKED, NOT NO_EDGE.**

No directional outcome was scored.
No OOS horizon was opened.
No 2026 data was scored or fetched.

## V1.0.1 mission

SOURCE-ONLY diagnosis of historical price coverage.

Probe the frozen MEXC public BTC_USDT standard-futures index-price routes at representative dates in:
- 2022
- 2023
- 2024
- 2025
- 2026 control

Intervals:
- Min5
- Min15
- Min30
- Min60
- Hour4
- Day1

Routes:
- index_price
- regular contract K-line
- fair_price

For every probe record:
- HTTP/status;
- success flag;
- returned row count;
- first/last returned timestamp;
- whether any timestamp lies inside the requested window.

No signal direction, future return, win/loss, accuracy, EV, or strategy result may be calculated in V1.0.1.

## Contingent source-transfer rule frozen now

If official MEXC historical data is unavailable for 2022–2025 at the event horizons, a later branch MAY test the already-frozen ETF-CME signal against an external public BTC spot/index proxy **only after a separate explicit transfer freeze is committed before outcome access**.

Such a result must be labeled:
`EXTERNAL_PRICE_PROXY_ONLY`

It may never be promoted directly to an exact MEXC Event Futures candidate.

## Boundaries

- No authenticated requests.
- No order submission.
- No exchange mutation.
- No strategy outcomes.
- No 2026 scoring.
- No main merge.
