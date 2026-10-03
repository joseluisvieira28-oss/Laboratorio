# OPTIONS-VOL-FWD-001 — SOURCE-ONLY CALIBRATION FREEZE V0.2

Date: 2026-10-03
Status: PRE-OUTCOME / NEW VERSION / SOURCE-ONLY

## Why V0.2 exists

V0.1 remains immutable.

Its frozen trigger was |put mark IV - call mark IV| >= 5.0 percentage points.
The completed three-hour forward batch (run 37100393588) produced:
- 173 valid BTC pairs;
- 177 valid ETH pairs;
- zero qualifying V0.1 signals;
- zero Event Futures outcomes.

No V0.1 threshold is changed or rescued.

V0.2 asks a different pre-registered question:

> Does the direction of statistically extreme options skew, where "extreme" is defined only
> from the forward source distribution and never from price outcomes, predict the 10-minute
> Event Futures shadow direction?

## Calibration source

Exactly reuse the already validated Deribit public source algorithm:
- production unauthenticated public endpoints only;
- BTC and ETH inverse options;
- nearest active expiry in [7,30] days;
- actual delta validation in [0.15,0.35] absolute;
- select closest actual delta to +/-0.25, no interpolation;
- pair timestamp spread <=5000 ms;
- finite positive mark/bid/ask IV, quote prices/amounts, index and underlying price;
- one source round per UTC minute;
- no retry inside a minute.

Canonical skew:
`skew_pp = put mark_iv - call mark_iv`.

## Forward-only calibration boundary

Only source rounds strictly after the first commit containing this freeze may enter V0.2 calibration.

The V0.1 three-hour batch is context only and contributes ZERO calibration rows.

No MEXC payout, MEXC index, future price, return, win/loss, PnL or Event Futures outcome
may be accessed by the calibration process.

## Healthy minute

A symbol-minute is valid only when the frozen source algorithm returns a matched valid pair.
Missing/invalid source minutes are MISSING, never imputed.

Keep exact raw hashes and source timestamps.

## Calibration minimum

Before any V0.2 activation freeze:

Per symbol require:
- >= 1440 UTC calibration minutes observed;
- >= 1200 valid matched-pair minutes;
- no unresolved source-integrity violations.

If the minimum is not met, status remains `SOURCE_CALIBRATION_INCOMPLETE`.

## Threshold rule frozen now

For EACH symbol independently:

1. take `abs(skew_pp)` over all valid calibration minutes;
2. compute the nearest-rank 95th percentile:
   rank = ceil(0.95 * n), sorted ascending;
3. the value at that rank is the sole allowed symbol threshold.

No alternative quantile search.
No direction-dependent threshold.
No volatility filter.
No payout filter.
No future-return optimization.

If the resulting threshold is <=0 or nonfinite, calibration FAILS CLOSED.

## Future activation template — NOT ACTIVE

After calibration minimum passes, a separate pre-outcome activation freeze must commit
the exact BTC and ETH numeric thresholds and calibration artifact hashes before any V0.2
Event Futures outcome is opened.

Frozen future rule:

- direction policy: FOLLOW_INSURANCE_SKEW;
- skew >= +threshold(symbol) => DOWN;
- skew <= -threshold(symbol) => UP;
- otherwise NO_SIGNAL;
- horizon exactly 10 minutes;
- source signal age <=5 seconds;
- same V0.13 exact payout/index/expiry protocol;
- first-only unresolved overlap;
- min N=100 per symbol;
- 30-day frozen batch evaluation;
- no significance peeking before batch boundary.

## Governance

- V0.1 remains unchanged and may not inherit V0.2 calibration;
- no outcomes during calibration;
- no live trading;
- no orders;
- no login;
- no private/account endpoints;
- no merge to main.
