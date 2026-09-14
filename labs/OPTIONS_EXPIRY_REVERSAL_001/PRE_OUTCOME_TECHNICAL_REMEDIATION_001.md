# OPTIONS-EXPIRY-REVERSAL-001 — PRE-OUTCOME TECHNICAL REMEDIATION 001

Status: FROZEN BEFORE ANY OUTCOME METRIC WAS COMPUTED

## Trigger

Official one-shot Discovery run 34900018454 failed during raw BTC price acquisition before r_pre, r_post, OLS, bootstrap, trade returns, PnL, or promotion gates were computed.

Failure: Binance monthly BTCUSDT Spot 1m archive lacked all four required exact minute points for 2021-09-29 (07:30, 08:00, 08:01, 08:31 UTC).

This is classified as TECHNICAL_FAILURE_PREOUTCOME, not a scientific result.

## Frozen remediation

Keep the scientific hypothesis, signal, dates, timestamps, direction, regression, bootstrap, costs, and promotion gates unchanged.

For every protected Discovery date, acquire exact 1-minute BTCUSDT Spot open prices from the official Binance Vision MONTHLY archive first, verified against its official CHECKSUM.

If and only if one or more of the four exact required minute points are missing for a date, attempt the official Binance Vision DAILY BTCUSDT Spot 1m archive for that same calendar date, also verified against its official CHECKSUM.

The daily archive is a same-source/same-market/same-symbol/same-interval redundancy path, not a new data family.

Rules:
- no interpolation;
- no nearest-minute substitution;
- no alternative exchange;
- no futures/perpetual data;
- no dropping the date to make the sample pass;
- no 2025 or 2026 access;
- if the daily archive does not contain all missing exact minute points, fail closed again before outcomes;
- the fallback applies generically to any protected date with missing exact monthly points, not only to 2021-09-29;
- no return, regression, bootstrap, PnL, or gate may be computed until every protected date has all four exact prices.

## Governance

This remediation exists only because run 34900018454 terminated before outcome construction. It must not be changed after any outcome metric is observed.

No live trading. No exchange mutation. No post-outcome tuning. 2025 locked. 2026 locked.
