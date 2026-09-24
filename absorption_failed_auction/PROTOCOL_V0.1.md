# ABSORPTION-FAILED-AUCTION-001 — Prospective Protocol V0.1.1

Status: **FROZEN / OUTCOME-BLIND / RESEARCH-ONLY**  
Parent sensor lab: `TV-FOOTPRINT-CALIBRATION-001`  
This V0.1.1 supersedes the preliminary V0.1 **before any economic outcome was opened**.

## Research question

When canonical exchange aggressor flow is extreme and participation is material, but current-bar auction response is inefficient or fails to migrate with that flow, does subsequent price action differ from bars where the same kind of extreme aggression is efficiently accepted?

This is a market-mechanism study, not a trading strategy.

## Why V0.1.1 exists

The preliminary freeze used a 288-bar rolling baseline. Before the parent sensor calibration reached a terminal verdict and before any economic outcomes were opened, the design was hardened to use a full **2,016 prior forward 5-minute bars (7 days)**. This removes dependence on pre-boundary history, reduces one-day regime sensitivity, and aligns the event baseline with the parent calibration evidence horizon.

No values from the initial transport receipts were used to choose these thresholds.

## Hard prerequisites

Economic outcomes remain CLOSED until all gates pass:

1. `TV-FOOTPRINT-CALIBRATION-001 = PASS_STRONG`.
2. Evidence Vault reports no conflicting same-key receipts.
3. Transport coverage over the relevant window is >=99%.
4. MM-V1 structural fields are present on >=99% of valid bars.
5. Structural invariants hold on every used bar:
   - `VAL <= POC <= VAH`;
   - imbalance row counts are non-negative;
   - imbalance row counts do not exceed footprint row count;
   - `ltf_intrabars` is in [0,5].

If any prerequisite fails, this lab remains `SENSOR_BLOCKED` or `SOURCE_BLOCKED`. No substitute sensor may rescue this Lab ID.

## Frozen universe

- Venue/instrument: `BINANCE:BTCUSDT` spot.
- Event bars: closed UTC 5-minute bars.
- Canonical flow authority: Binance spot aggTrades.
- Structural sensor after PASS_STRONG: MM-V1.
- No other asset, venue, timeframe, or footprint definition under this Lab ID.

## Prospective event boundary

The first eligible event candidate is the **first complete 5-minute bar after the committed parent PASS_STRONG receipt**.

Bars collected before that point may be used only as causal rolling-baseline history. They can never become events in this lab.

## Causal baseline

Every candidate bar requires **2,016 immediately preceding valid forward bars**.

Thresholds are computed only from those preceding bars. The candidate bar and all future bars are excluded.

Frozen rolling quantiles:

- extreme directional aggression = q95 of prior `abs(agg_delta_pct)`;
- minimum participation = q75 of prior canonical `agg_base_volume`;
- low path efficiency = q25 of prior `ltf_path_efficiency`;
- high path efficiency = q75 of prior `ltf_path_efficiency`;
- low price displacement = q25 of prior `abs(bar_return_bps)`.

## Event direction

For an eligible candidate:

`d = sign(agg_delta_pct)`

Zero-delta bars cannot be events.

## Extreme-flow eligibility

A bar can enter either primary group only if both hold:

`abs(agg_delta_pct) >= rolling_q95_abs_agg_delta_pct`

`agg_base_volume >= rolling_q75_agg_base_volume`

No session, weekday, volatility, news, funding, open-interest or discretionary filter is allowed in V0.1.1.

## FAILED_AUCTION event

An extreme-flow bar is `FAILED_AUCTION` only if all hold:

1. `ltf_path_efficiency <= rolling_q25_ltf_path_efficiency`;
2. `d * poc_migration_bps <= 0`;
3. current-bar price response is weak, defined as either:
   - `d * bar_return_bps <= 0`, or
   - `abs(bar_return_bps) <= rolling_q25_abs_bar_return_bps`.

Interpretation: aggressive flow is strong, but the auction fails to travel efficiently with it.

## EFFICIENT_ACCEPTANCE control

An extreme-flow bar is `EFFICIENT_ACCEPTANCE` only if all hold:

1. `ltf_path_efficiency >= rolling_q75_ltf_path_efficiency`;
2. `d * poc_migration_bps > 0`;
3. `d * bar_return_bps > 0`.

Extreme-flow bars meeting neither definition are preserved as `UNCLASSIFIED_EXTREME` and have no primary rescue authority.

## Cluster control

To reduce repeated counting of the same market episode, after any accepted primary event (`FAILED_AUCTION` or `EFFICIENT_ACCEPTANCE`) the next **60 minutes** are ineligible for another primary event.

The first qualifying event wins. Suppressed bars are preserved as `COOLDOWN_SUPPRESSED`.

## Outcomes

Outcome clock starts at event-bar close.

For H in {5m, 15m, 30m, 60m, 240m}:

`R_H = d * (close_T+H / close_T0 - 1) * 10000`

- positive `R_H` = continuation in aggressor direction;
- negative `R_H` = reversal against aggressor direction.

**Primary horizon: 60 minutes.**

No MAE/MFE, stop, target, slippage model, leverage, position sizing or PnL is part of this mechanism test.

## Minimum evidence

Terminal adjudication requires:

- >=100 `FAILED_AUCTION` events;
- >=100 `EFFICIENT_ACCEPTANCE` events;
- events spanning >=30 distinct UTC dates;
- >=99% valid R60 outcome coverage in each primary group;
- >=99% transport coverage over the used research window;
- zero unresolved evidence conflicts;
- parent sensor remains PASS_STRONG.

Otherwise: `INSUFFICIENT_SAMPLE`, `SOURCE_BLOCKED`, or `SENSOR_BLOCKED`.

## Primary scientific gate

`MECHANISM_SURVIVES` requires all:

1. median R60 for FAILED_AUCTION < 0;
2. median R60 for EFFICIENT_ACCEPTANCE > 0;
3. median contrast `EFFICIENT_ACCEPTANCE - FAILED_AUCTION > 0`;
4. two-sided 95% event-level bootstrap CI for that median contrast has lower bound > 0;
5. FAILED_AUCTION reversal rate at 60m >50% and its Wilson 95% lower bound >50%;
6. EFFICIENT_ACCEPTANCE continuation rate at 60m >50% and its Wilson 95% lower bound >50%.

Bootstrap resamples: 10,000. Deterministic seed: 20260924.

If minimum evidence is met but any primary condition fails: `NO_MECHANISM`.

## Secondary reporting — no rescue authority

Report without changing the verdict:

- R5/R15/R30/R60/R240 medians;
- directional hit rates at each horizon;
- counts by UTC date;
- buy-aggression vs sell-aggression;
- weekday breakdown;
- volume-z terciles.

Secondary horizons or slices cannot rescue the 60-minute primary gate.

## Anti-rescue

After the parent PASS_STRONG opens prospective event collection, forbidden under this Lab ID:

- changing 2,016-bar baseline;
- changing q95/q75/q25 thresholds;
- changing 60-minute cooldown;
- adding or dropping volume/session/weekday/volatility/news filters;
- changing event definitions;
- changing the primary horizon;
- switching venue, asset or timeframe;
- changing POC/path-efficiency definitions;
- asymmetric buy/sell rules;
- deleting difficult or high-volatility bars;
- lag shifting;
- replacing canonical Binance aggressor flow with TV delta;
- adding stops, targets, MAE/MFE or PnL to rescue a failed mechanism.

Any materially different experiment requires a new Lab ID and new prospective freeze.

## State machine

- `FROZEN_OUTCOME_BLIND`
- `SENSOR_BLOCKED`
- `SOURCE_BLOCKED`
- `COLLECTING`
- `INSUFFICIENT_SAMPLE`
- `MECHANISM_SURVIVES`
- `NO_MECHANISM`

No state grants live-trading authority.
