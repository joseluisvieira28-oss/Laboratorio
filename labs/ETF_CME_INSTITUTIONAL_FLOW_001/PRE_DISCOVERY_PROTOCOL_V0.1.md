# ETF-CME-INSTFLOW-001 — PRE-DISCOVERY PROTOCOL V0.1

STATUS: FROZEN — OUTCOME-BLIND / SOURCE-DATA GATE NEXT

## Scientific question

Does a week-over-week increase in speculative/non-commercial net positioning in regulated CME Bitcoin futures predict a positive subsequent one-week BTC spot return after the CFTC information is safely public?

## Governance

- research-only;
- fail-closed;
- no live trading;
- no exchange mutation;
- no merge to main;
- no post-outcome tuning;
- no cherry-picking;
- 2025 LOCKED;
- 2026 LOCKED;
- ETF flow data are NOT part of MVE0;
- only one frozen primary signal is allowed in MVE0;
- no predictive outcome, return or PnL may be computed before SOURCE_DATA_GATE_PASS.

## Frozen source

Primary source: CFTC Commitments of Traders — Legacy Futures Only — BITCOIN, CHICAGO MERCANTILE EXCHANGE, CFTC contract code `133741`.

Required source-native fields per weekly observation:
- report/as-of date;
- open interest;
- non-commercial long;
- non-commercial short;
- non-commercial spreading (stored for provenance only; not used in MVE0 signal);
- commercial and nonreportable fields may be retained for audit/provenance but are not MVE0 predictors.

The COT observation represents positions as of Tuesday. The standard CFTC publication is later in the week; because a complete historical release-date list is not available, MVE0 uses a deliberately conservative fixed information lag rather than reconstructing or guessing release timestamps.

## Frozen sample

Discovery source period: weekly COT observations with `as_of_date` from 2018-01-01 through 2024-12-31, subject to the protected-period outcome firewall below.

2017 is excluded from MVE0 because CME Bitcoin futures began only in December 2017 and therefore does not provide a full calendar year.

2025 and 2026 source/outcome access is forbidden.

## Frozen signal

For weekly observation t:

`net_nc_t = noncommercial_long_t - noncommercial_short_t`

`delta_net_nc_t = net_nc_t - net_nc_(t-1)`

`signal_t = delta_net_nc_t / open_interest_t`

No z-score, percentile, threshold, winsorization, sign filter, regime filter, volatility filter, price filter, ETF filter, basis filter or alternative trader category is permitted in MVE0.

Economic direction is frozen as:
- positive signal -> expected positive subsequent BTC spot return;
- negative signal -> expected negative subsequent BTC spot return.

## Frozen information-availability rule

To avoid lookahead from uncertain historical holiday/release timing:

`information_safe_time_t = as_of_date_t + 8 calendar days at 00:00 UTC`

This intentionally waits materially longer than the normal Friday publication following the Tuesday position date.

If source audit discovers a documented CFTC release later than this conservative timestamp for any observation, that observation MUST be excluded or the gate MUST fail closed; the lag may not be shortened after outcomes are seen.

## Frozen outcome

Outcome instrument: BTCUSDT spot daily close/open series from the same canonical public Binance spot route already used elsewhere in the research program, or an equivalently provenance-bound public BTCUSD spot series selected during source audit BEFORE outcomes are computed.

For each signal t:
- entry = first 00:00 UTC daily price at or after `information_safe_time_t`;
- exit = exactly 7 calendar days after entry at 00:00 UTC;
- forward return = `exit_price / entry_price - 1`.

Protected-period firewall:
- both entry and exit timestamps MUST be <= 2024-12-31T23:59:59Z;
- any signal whose outcome requires a 2025 price is excluded before outcome computation;
- no 2025 or 2026 price file may be fetched.

## Frozen economic test

Primary regression:

`forward_7d_return_t = alpha + beta * signal_t + error_t`

Inference: one-sided test of `beta > 0` with HAC/Newey-West standard errors. HAC lag is frozen at 2 weekly observations.

Companion sign strategy for economic interpretability:
- position_t = +1 when signal_t > 0;
- position_t = -1 when signal_t < 0;
- signal_t == 0 -> flat / no trade.

No threshold beyond zero is permitted.

## Frozen costs

Round-trip trading costs applied to the sign strategy:
- base: 10 bps per non-flat weekly trade;
- stress: 20 bps per non-flat weekly trade.

Costs are not applied to the regression coefficient; they apply to economic strategy returns.

## Frozen MVE0 promotion criteria

ALL must pass:

1. at least 300 evaluable weekly observations after all pre-outcome source/timing firewalls;
2. regression beta > 0;
3. one-sided HAC p-value <= 0.10;
4. base-cost (10 bps) sign-strategy mean net return > 0;
5. base-cost Profit Factor > 1.00;
6. at least 5 of the 7 full calendar years 2018-2024 have non-negative base-cost net strategy return, counting only years with sufficient evaluable observations;
7. no single calendar year contributes more than 40% of total positive gross strategy PnL across positive years;
8. 20 bps stress results must be reported but are diagnostic and not an independent promotion gate.

If fewer than 7 calendar years remain evaluable because of source/data gaps, annual robustness is fail-closed unless every missing year is explicitly classified as a source/data issue before outcomes and a revised protocol is independently authorized before outcome access.

## Classification rules

- `SOURCE_DATA_GATE_PASS`: source/provenance/completeness/timing firewalls pass; Discovery may run once.
- `SOURCE_DATA_BLOCKED` or `DATA_FAILURE`: canonical source cannot satisfy the frozen protocol; no predictive result.
- `DISCOVERY_MVE0_PASS`: all frozen promotion criteria pass.
- `DISCOVERY_FAIL_NO_PROMOTION`: Discovery executes validly but one or more promotion criteria fail.
- `TECHNICAL_FAILURE` / `EXECUTION_ENVIRONMENT_BLOCKED`: execution issue; never reinterpret as NO_EDGE.

## Next authorized action

Run an outcome-blind Source/Data Gate only. Confirm code 133741 history, schema stability, weekly uniqueness, field validity, chronological continuity, minimum potential sample, conservative availability timing and protected-period firewalls. Do not compute signal-return relationships, regression, strategy PnL, or open 2025/2026 during the gate.