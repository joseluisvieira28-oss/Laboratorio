# MEXC EVENT FUTURES LAB — OPTIONS-SPOTPERP SIGNAL TRANSFER FREEZE V0.8

Date: 2026-10-02
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## Prior Event Futures state

V0.3.1 simple continuation/reversal: 0 robust discovery passers.
V0.4 technical chart-state: 27 basic eligible, 0 BH-selected.
V0.5 cross-asset lead/lag: 7 basic eligible, 0 BH-selected.
V0.7 session/calendar: 5 basic eligible, 0 BH-selected.
September-2026 historical holdout remains unopened in those families.

## Distinct V0.8 hypothesis

V0.8 does NOT derive a signal from Event Futures chart history.

It transfers the already frozen daily directional signal from:
`OPTIONS-SPOTPERP-001 / V2.1`

Parent signal:
`CALL_IV_MINUS_PUT_IV`

Frozen parent direction:
- positive skew -> LONG / UP
- negative skew -> SHORT / DOWN
- zero -> no signal

Parent execution timing:
- signal date = t
- parent entry = 00:00 UTC on t+1
- parent exit = 00:00 UTC on t+2

V0.8 asks only whether that already-existing signal direction predicts the shorter Event Futures horizons starting from the exact parent entry timestamp.

No options parameter, moneyness band, DTE band, sign, threshold, entry clock, or parent signal identity may be changed in V0.8.

## Immutable parent evidence

Discovery parent artifact:
- workflow run: `34858777691`
- artifact id: `10354131731`
- artifact name: `options-spotperp-001-discovery-v01-34858777691-1`
- expected ledger: `OPTIONS_SPOTPERP_001_DISCOVERY_LEDGER_V01.csv`
- parent signal dates: 2021-04 through 2024-12
- expected ledger rows: 1210

Independent 2025 parent OOS artifact:
- workflow run: `35231711508`
- artifact id: `10504812106`
- artifact name: `options-spotperp-001-v21-oos-2025-35231711508-1`
- expected ledger: `v21_oos_output_2025/OPTIONS_SPOTPERP_001_V21_2025_OOS_LEDGER_V01.csv`
- expected ledger rows: 363
- parent classification: `TIER_2_PROMOTED_CANDIDATE__QUASE_DIAMANTE__HIGH_RISK_FRAGILITY`

V0.8 consumes only parent signal date/sign from these immutable artifacts.
The parent's 1-day forward outcome columns are not used to select V0.8 horizons or thresholds.

## Underlying price proxy

Primary V0.8 outcome source:
MEXC standard-futures BTC index-price Min5 public route:

`https://contract.mexc.com/api/v1/contract/kline/index_price/BTC_USDT`

Clock correction:
a raw Min5 close stamped `s` is treated as observable at `s + 300 seconds`.

This is a proxy for Event Futures settlement, not proven exact Event Futures history.

If the public MEXC route cannot return the required historical periods, classification is:
`SOURCE_BLOCKED_MEXC_INDEX_HISTORY`.

No source substitution is allowed after outcome inspection.

## Event Futures horizons

Frozen before outcomes:
- 10 minutes
- 30 minutes
- 60 minutes
- 1440 minutes

Entry:
00:00 UTC on signal date t+1.

Prediction:
- parent position +1 => UP
- parent position -1 => DOWN
- parent position 0 => no event

Outcome:
sign(index[t+1 00:00 + H] - index[t+1 00:00]).

Tie:
recorded separately; excluded from binomial N.

## Discovery / OOS

Discovery:
parent signal dates from the immutable 2021-2024 Discovery ledger.

Independent OOS:
parent signal dates from the immutable 2025 OOS ledger.

No 2026 signal data are used in V0.8.

This deliberately preserves a clean, already-existing 2025 independent parent signal period for the Event Futures translation.

## Discovery gate

Reference payout:
80%.

Break-even directional accuracy:
55.5555556%.

For each of the four frozen horizons:

- non-tie N >= 500;
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- at least 3 of the 4 calendar years 2021-2024 have accuracy > 50%;
- one-sided exact binomial p-value vs p0=55.5555556% is computed.

Apply Benjamini-Hochberg FDR q=0.05 across all four discovery horizons.

Only BH-selected horizons may open the immutable 2025 OOS ledger.

## 2025 OOS gate

For a frozen selected horizon:

- non-tie N >= 250;
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- one-sided exact binomial p-value vs p0=55.5555556% < 0.05;
- illustrative EV at 80% payout > 0;
- at least 3 of 4 calendar quarters have accuracy > 50%.

Any survivor is:
`EVENT_FUTURES_PROXY_CANDIDATE__OPTIONS_SIGNAL_TRANSFER`

It is NOT an exact MEXC Event Futures edge.

## Exact-product blockers preserved

Promotion to exact Event Futures remains prohibited until:
- historical or prospective payout-at-entry is available;
- exact Event Futures settlement-index equivalence is proven;
- entry/expiry rounding semantics are proven.

## Hard boundaries

- No live Event Futures trading.
- No Event Futures order submission.
- No authenticated MEXC request.
- No account mutation.
- No post-outcome horizon rescue.
- No parent signal modification.
- No merge to main.
