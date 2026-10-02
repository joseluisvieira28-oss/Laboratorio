# MEXC EVENT FUTURES LAB — ETF-CME SIGNAL TRANSFER FREEZE V1.0

Date: 2026-10-02
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## Prior Event Futures proxy result

V0.3.1 through V0.9 tested ordinary price/chart/session/cross-asset/volatility families.
Across those frozen families, no candidate survived the pre-frozen robust discovery gates.
September 2026 remained unopened.

V1.0 is deliberately different: it transfers an **independently frozen external information signal** from the existing Crypto Lab strategy `ETF-CME-INSTFLOW-001`.

## Independent source strategy preserved

Source strategy identity:
`ETF-CME-INSTFLOW-001`

Frozen CFTC contract code:
`133741`

Frozen source rule:
`signal = Δ(noncommercial_long - noncommercial_short) / current_open_interest`

Direction:
- positive => UP / LONG
- negative => DOWN / SHORT
- zero => FLAT

Frozen information lag from the source strategy:
8 calendar days after the CFTC observation date.

For an observation dated `D`, the information-safe / exact source-strategy entry timestamp is:
`D + 8 days at 00:00:00 UTC`.

V1.0 does not alter the CFTC signal, threshold it, rescale it, reverse it, or select only favorable magnitudes.

## New transfer hypothesis

Question:

> Does the independently frozen ETF-CME institutional-flow direction predict the sign of the MEXC BTC index-price move over Event Futures-like horizons beginning at the exact information-safe timestamp?

Only the **original frozen direction** is tested.

No inverted-direction rescue is permitted in V1.0.

## Event horizons

- 10m
- 30m
- 60m
- 1440m

For each signal:
- entry proxy = MEXC BTC_USDT standard-futures index price at the exact information-safe timestamp;
- expiry proxy = same index-price series at entry + horizon;
- UP wins if expiry > entry;
- DOWN wins if expiry < entry;
- equality = tie.

## Sources

Signal source:
CFTC Public Reporting dataset `6dca-aqww`, contract code `133741`.

Price proxy:
MEXC public standard-futures index-price K-lines for `BTC_USDT`.

Preferred raw interval:
Min5.

Min5 bar close stamped `s` is treated as observable at `s + 300 seconds`.

This is NOT yet proven identical to exact Event Futures settlement pricing.

## Historical partitions frozen before source/outcome access

Warm-up/source history:
2021-01-01 through 2021-12-31.

Discovery:
2022-01-01T00:00:00Z <= entry < 2025-01-01T00:00:00Z.

Retrospective OOS:
2025-01-01T00:00:00Z <= entry < 2026-01-01T00:00:00Z.

2026:
LOCKED / NOT SCORED in V1.0.

This avoids reusing the 2026 Event Futures proxy periods already inspected in V0.x as a rescue.

## Source gate

Before scoring:
- CFTC observations must be chronological and unique;
- open interest must be >0;
- previous/current observations must be consecutive returned observations for the contract code;
- exact information-safe timestamp must be derivable without using price outcomes;
- MEXC must return exact proxy timestamps required for entry/expiry.

Missing exact price timestamps => observation missing, never interpolated.

## Primary statistical test

There are only 4 primary cells, one per Event horizon.

Reference economic hurdle:
80% payout => break-even accuracy = 55.5555556%.

Discovery gate for a horizon:
- non-tie N >= 100;
- accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- one-sided exact binomial p-value vs p0=55.5555556%;
- accuracy >50% in each of the three chronological discovery thirds.

Apply Benjamini-Hochberg FDR q=0.05 across the 4 discovery horizon p-values that satisfy the basic gate.

Only BH-selected horizons may open 2025 OOS.

## OOS gate

No changes.

Pass requires:
- non-tie N >= 30;
- accuracy >55.5555556%;
- Wilson 95% lower bound >50%;
- one-sided exact binomial p-value vs p0=55.5555556% <0.05;
- EV under illustrative 80% payout >0.

Report EV at payout:
70%, 75%, 80%, 85%, 90%.

Report required payout for EV=0.

## Interpretation

A survivor is:
`EXTERNAL_SIGNAL_EVENT_FUTURES_PROXY_CANDIDATE`

It is NOT:
- proof of exact MEXC Event Futures profitability;
- authorization to trade Event Futures;
- permission to open the 2026 holdout;
- permission to alter the independently frozen ETF-CME source strategy.

## Hard boundaries

- No 2026 scoring.
- No September 2026 access for this experiment.
- No direction inversion.
- No threshold/magnitude filter.
- No post-outcome tuning.
- No authenticated MEXC calls.
- No order submission.
- No account mutation.
- No merge to main.
