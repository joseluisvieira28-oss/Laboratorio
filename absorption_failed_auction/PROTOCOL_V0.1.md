# ABSORPTION-FAILED-AUCTION-001 — Prospective Protocol V0.1

Status: FROZEN / OUTCOME-BLIND / RESEARCH-ONLY  
Parent sensor lab: `TV-FOOTPRINT-CALIBRATION-001`

## Research question

When aggressive flow is extreme but current-bar price/auction response is inefficient or fails to migrate with that flow, does subsequent price action differ materially from bars where extreme aggression is efficiently accepted?

This is a market-mechanism study, not a trading strategy.

## Hard prerequisite

Economic outcomes remain CLOSED until `TV-FOOTPRINT-CALIBRATION-001` reaches terminal `PASS_STRONG`.

- `PASS_STRONG` -> this lab may open.
- `PASS_LIMITED`, `FAIL_SENSOR`, or `INSUFFICIENT_SAMPLE` -> this lab remains `SENSOR_BLOCKED`.
- No alternative sensor may rescue this Lab ID.

## Frozen universe

- Venue/instrument: BINANCE:BTCUSDT spot
- Event bars: closed 5-minute UTC bars
- TV sensor: MM-V1
- Flow authority after unlock: canonical Binance spot aggTrades aggressor delta
- TV-derived context: LTF path efficiency, POC migration, footprint imbalance counts, volume context
- No other asset, venue, timeframe, or footprint definition under this Lab ID.

## Baseline

Every candidate bar requires 288 immediately preceding valid 5-minute bars.

Rolling empirical thresholds are computed using **only those prior 288 bars** and never include the candidate bar or future bars.

Frozen quantiles:

- extreme aggression threshold = q90 of prior `abs(agg_delta_pct)`
- low path efficiency = q30 of prior `ltf_path_efficiency`
- high path efficiency = q70 of prior `ltf_path_efficiency`
- low displacement = q30 of prior `abs(bar_return_bps)`

No quantile may be changed after outcomes are opened.

## Event direction

For an eligible candidate bar:

`d = sign(agg_delta_pct)`

Bars with zero canonical aggressor delta are not events.

## Extreme-aggression eligibility

A candidate is eligible only when:

`abs(agg_delta_pct) >= rolling_q90_abs_agg_delta_pct`

No volume, session, weekday or volatility filter is permitted in V0.1.

## FAILED_AUCTION event

An extreme-aggression bar is classified `FAILED_AUCTION` only if **all** hold:

1. `ltf_path_efficiency <= rolling_q30_ltf_path_efficiency`
2. `d * poc_migration_bps <= 0`
3. current-bar response is weak, defined as either:
   - `d * bar_return_bps <= 0`, or
   - `abs(bar_return_bps) <= rolling_q30_abs_bar_return_bps`

This definition is frozen before future outcomes are opened.

## EFFICIENT_ACCEPTANCE control

An extreme-aggression bar is classified `EFFICIENT_ACCEPTANCE` only if **all** hold:

1. `ltf_path_efficiency >= rolling_q70_ltf_path_efficiency`
2. `d * poc_migration_bps > 0`
3. `d * bar_return_bps > 0`

Extreme-aggression bars meeting neither definition are `UNCLASSIFIED_EXTREME` and are preserved but not used in the primary comparison.

## Outcomes

Outcome clock starts at event-bar close.

For horizon H in {5m, 15m, 30m, 60m, 240m}:

`R_H = d * (close_T+H / close_T0 - 1) * 10000`

Interpretation:

- positive `R_H`: continuation in aggressor direction
- negative `R_H`: reversal against aggressor direction

Primary horizon: 60 minutes.

No MAE/MFE, stop, target, entry slippage, PnL or leverage is part of V0.1.

## Minimum evidence

Terminal adjudication requires:

- >=100 `FAILED_AUCTION` events
- >=100 `EFFICIENT_ACCEPTANCE` events
- events spanning >=30 distinct UTC dates
- valid outcome coverage >=95% at 60m in both groups
- no unresolved evidence conflicts
- parent sensor remains PASS_STRONG

Otherwise state = `INSUFFICIENT_SAMPLE` or `SOURCE_BLOCKED`, as appropriate.

## Primary scientific gate

`MECHANISM_SURVIVES` requires all:

1. median R60 for FAILED_AUCTION < 0
2. median R60 for EFFICIENT_ACCEPTANCE > 0
3. median contrast `EFFICIENT_ACCEPTANCE - FAILED_AUCTION > 0`
4. two-sided 95% bootstrap CI for the median contrast excludes 0
5. FAILED_AUCTION reversal rate at 60m > 50%
6. Wilson 95% lower bound for that reversal rate > 50%

If minimum evidence is met but any primary condition fails: `NO_MECHANISM`.

## Secondary robustness

Report, without rescue authority:

- group counts by UTC date
- medians at 5m/15m/30m/60m/240m
- reversal rates at each horizon
- contrast at each horizon
- weekday breakdown
- volume-z terciles
- sign of aggression (buy vs sell)

Secondary slices cannot overturn the primary classification.

## Anti-rescue

After outcome opening, forbidden under this Lab ID:

- changing q90/q30/q70
- changing 288-bar baseline
- adding volume/session/weekday/volatility filters
- changing event horizon
- using another venue/asset/timeframe
- changing POC or path-efficiency rules
- asymmetric buy/sell rules
- deleting news or high-volatility bars
- lag shifting
- using TV delta instead of canonical Binance aggressor delta
- adding MAE/MFE, stops, targets or PnL to rescue a failed mechanism

## State machine

- `FROZEN_OUTCOME_BLIND`
- `SENSOR_BLOCKED`
- `COLLECTING`
- `INSUFFICIENT_SAMPLE`
- `SOURCE_BLOCKED`
- `MECHANISM_SURVIVES`
- `NO_MECHANISM`

No state in this lab grants live-trading authority.
