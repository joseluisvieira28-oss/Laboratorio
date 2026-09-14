# ETF-SHORTFLOW-001 — PRE-DISCOVERY PROTOCOL V0.1

STATUS: FROZEN PRE-OUTCOME / SOURCE-DATA GATE NEXT

LAB: `ETF-SHORTFLOW-001`

MVE: `ESF-IBIT-SHORTVOL-5D-001`

## Scientific question

Does an increase in FINRA-reported off-exchange short-sale volume share for IBIT, relative to its own recent history, predict a negative subsequent 5-calendar-day BTC return after the FINRA daily file is safely public?

## Important source interpretation

FINRA Daily Short Sale Volume is NOT short interest and is NOT a complete all-venue short-sale measure. It covers publicly disseminated off-exchange short-sale trades reported to FINRA facilities. MVE0 tests the information content of this published flow measure only.

## Frozen source

Official FINRA Consolidated NMS Daily Short Sale Volume files.

Canonical URL pattern:
`https://cdn.finra.org/equity/regsho/daily/CNMSshvolYYYYMMDD.txt`

Required fields:
- Date
- Symbol
- ShortVolume
- ShortExemptVolume
- TotalVolume
- Market

Primary security: `IBIT` only.

No other spot-Bitcoin ETF may replace, rescue or be pooled with IBIT under this MVE ID after outcomes are opened.

## Frozen source window

2024-01-11 through 2024-12-31 inclusive.

Expected U.S. regular trading dates in this interval: 245, using weekdays minus the frozen 2024 full-market holidays after the start date:
- 2024-01-15
- 2024-02-19
- 2024-03-29
- 2024-05-27
- 2024-06-19
- 2024-07-04
- 2024-09-02
- 2024-11-28
- 2024-12-25

2025 source/outcome access: FORBIDDEN during Discovery.

2026 source/outcome access: FORBIDDEN.

## Frozen information availability

FINRA states that Daily Short Sale Volume files are posted no later than 18:00 ET on the relevant trade date.

For trade date `t`, MVE0 defines:

`information_safe_time_t = next 00:00 UTC after trade date t`

This is deliberately later than 18:00 ET in both EST and EDT and avoids reconstructing intraday publication seconds.

## Frozen signal

For each valid IBIT FINRA trade date t:

`short_share_t = ShortVolume_t / TotalVolume_t`

The 20 prior valid FINRA IBIT observations are used as a causal one-trading-month baseline:

`baseline20_t = mean(short_share_(t-20) ... short_share_(t-1))`

`signal_t = short_share_t - baseline20_t`

No current-day value may enter the baseline.

No z-score, percentile, winsorization, volatility filter, price filter, sentiment filter, ETF-flow filter, CFTC filter, funding filter, OI filter or threshold beyond zero is allowed in MVE0.

Frozen direction:
- `signal_t > 0` -> expected subsequent BTC return NEGATIVE;
- `signal_t < 0` -> expected subsequent BTC return POSITIVE;
- `signal_t == 0` -> flat for the companion sign strategy.

## Frozen outcome

Instrument for return measurement: canonical public Binance BTCUSDT spot daily data.

Entry:
- BTCUSDT 00:00 UTC open at `information_safe_time_t`.

Exit:
- BTCUSDT 00:00 UTC open exactly 5 calendar days after entry.

Forward return:
`r5_t = exit_price / entry_price - 1`

Any event whose entry or exit requires 2025 is excluded BEFORE outcome computation.

No 2025 or 2026 price source may be opened in Discovery.

## Frozen primary statistical test

Regression:

`r5_t = alpha + beta * signal_t + error_t`

Primary directional hypothesis:

`beta < 0`

Inference:
- OLS coefficient;
- HAC/Newey-West covariance;
- frozen HAC lag = 5 daily observations;
- one-sided p-value for `beta < 0`.

There is exactly one primary MVE hypothesis. No horizon family sweep is authorized.

## Frozen companion economic strategy

For interpretability only:
- LONG BTC when `signal_t < 0`;
- SHORT BTC when `signal_t > 0`;
- FLAT when `signal_t == 0`.

Costs per completed 5-day position:
- BASE: 10 bps round trip;
- STRESS: 20 bps round trip.

Overlap is allowed for the regression because daily signals have overlapping 5-day outcomes and HAC is explicitly used for that dependence.

For companion strategy accounting, each signal is treated as an independent fixed-notional research sleeve; no portfolio leverage interpretation is permitted.

## Frozen Discovery promotion gates

ALL primary gates must pass:

1. at least 180 evaluable signal/outcome observations after 20-day causal baseline and protected-period firewalls;
2. regression beta < 0;
3. one-sided HAC p-value <= 0.05;
4. BASE10 mean net sign-strategy return > 0;
5. BASE10 Profit Factor > 1.00;
6. at least 3 of 4 calendar quarters with evaluable trades have non-negative BASE10 aggregate return;
7. no single calendar month contributes more than 35% of total positive gross strategy PnL across positive months.

STRESS20 must be reported but is diagnostic, not an independent promotion gate.

Leave-one-month-out regression/sign diagnostics must be reported but are diagnostic in MVE0 because Discovery spans only one calendar year.

## Source/Data Gate requirements

Before any BTC market source is opened, the source gate must establish:
- official FINRA source route reproducibility;
- exact 245 expected source dates return valid files;
- header/schema validity;
- trade-date/file-date consistency;
- unique IBIT row per file;
- IBIT coverage >= 240 of 245 dates;
- numeric validity: ShortVolume >= 0, TotalVolume > 0, ShortExemptVolume >= 0, ShortExemptVolume <= ShortVolume;
- no source date after 2024-12-31;
- per-file URL, byte length and SHA256 captured;
- parsed IBIT source row captured for provenance;
- no ratio, predictive outcome, BTC price, return or PnL computed during the source gate.

Missing IBIT source rows are not imputed. Any eventual Discovery may use only source rows accepted by the frozen gate and must preserve the 20-prior-valid-observation baseline rule.

## Classifications

- `SOURCE_DATA_PASS`
- `SOURCE_ACCESS_BLOCKED`
- `DATA_FAILURE`
- `TECHNICAL_FAILURE_PREOUTCOME`
- `DISCOVERY_MVE0_PASS`
- `DISCOVERY_FAIL_NO_PROMOTION`

Blocked/data/technical states are not NO_EDGE.

## Next authorized action

Execute exactly one outcome-blind FINRA Source/Data Gate under this frozen contract. Stop before BTC price access even if the source gate passes.
