# MEXC EVENT FUTURES LAB — V0.7 CLOSEOUT + V0.8 VOLATILITY-SHOCK FREEZE

Date: 2026-10-02
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## V0.7 closeout

V0.7 tested fixed calendar/session directional bias across all five displayed Event Futures underlyings.

Result:
- frozen discovery cells: 840
- basic discovery-eligible cells: 5
- Benjamini-Hochberg FDR q=0.05 selected: 0
- August OOS opened: 0
- September 2026 holdout: LOCKED / NOT FETCHED

Verdict:
**NO_PROXY_SURVIVOR for the frozen session/calendar family.**

## V0.8 hypothesis family

Test whether unusually large pre-entry price moves, standardized by trailing realized volatility, create short-horizon continuation or reversal strong enough to clear the Event Futures 80%-payout reference hurdle.

This is distinct from:
- V0.3.1 unconditional continuation/reversal;
- V0.4 classic technical chart-state rules;
- V0.5 cross-asset lead/lag;
- V0.7 calendar/session bias.

No V0.8 outcomes have been inspected at freeze time.

## Source and clock

Public MEXC standard-futures index-price Min5 proxy:
`https://contract.mexc.com/api/v1/contract/kline/index_price/{symbol}`

Each raw Min5 close stamped `s` is observable only at `s + 300 seconds`.

Assets:
- BTCUSDT -> BTC_USDT
- ETHUSDT -> ETH_USDT
- NVDAUSDT -> NVIDIA_USDT
- MUUSDT -> MUSTOCK_USDT
- SPCXUSDT -> SPCXSTOCK_USDT

September 2026 remains LOCKED / MUST NOT BE FETCHED.

## Frozen event horizons

- 10m
- 30m
- 60m
- 1440m

## Frozen pre-entry shock windows

- 10m
- 30m
- 60m
- 240m

## Frozen volatility estimator

At entry timestamp `t`:
1. use only completed Min5 closes available at or before `t`;
2. compute Min5 log returns over the trailing 24 hours = latest 288 Min5 returns;
3. require at least 240 valid returns;
4. compute sample standard deviation `sigma5`;
5. compute signed shock return:
   `R_L = ln(P_t / P_{t-L})`;
6. normalize:
   `Z_L = R_L / (sigma5 * sqrt(L/5))`.

If sigma5 <= 0, the observation is invalid.

## Frozen shock thresholds

Absolute standardized shock thresholds:
- `|Z| >= 1.5`
- `|Z| >= 2.0`
- `|Z| >= 3.0`

Each threshold is a separate pre-frozen cell and all cells are included in multiple-testing correction.

## Frozen signal modes

For qualifying shocks:

- `FOLLOW_SHOCK`:
  predict the same sign as `Z_L`.

- `FADE_SHOCK`:
  predict the opposite sign.

No threshold, estimator, lookback, horizon, or signal mode may be changed after viewing V0.8 outcomes.

## Entry sampling

For a shock window L and event horizon H:
`entry_stride = max(L, H)`.

Entries are UTC-aligned to the stride.
This limits overlap and repeated reuse of the same shock.

Outcome:
`sign(P[t+H] - P[t])`.

Target ties are recorded and excluded from binomial N.

## Partitions

Discovery:
2026-04-01T00:00:00Z <= t < 2026-08-01T00:00:00Z

Retrospective OOS:
2026-08-01T00:00:00Z <= t < 2026-09-01T00:00:00Z

Historical holdout:
2026-09-01 through 2026-09-30 — LOCKED / NOT FETCHED.

## Discovery gate

Illustrative payout reference:
80%.

Break-even directional accuracy:
55.5555556%.

Minimum non-tie N:
- 10m >= 80
- 30m >= 60
- 60m >= 50
- 1d >= 15

A cell is discovery-eligible only if:
- minimum N is met;
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- accuracy > 50% in each of three chronological discovery thirds;
- one-sided exact binomial p-value vs p0=55.5555556% is computable.

Apply Benjamini-Hochberg FDR q=0.05 across the entire eligible V0.8 family.

Only BH-selected cells may open August OOS.

## OOS gate

No parameter change.

A selected cell passes OOS only if:
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- one-sided exact binomial p < 0.05 vs p0=55.5555556%;
- illustrative EV at 80% payout > 0.

Any survivor remains a **PROXY CANDIDATE**, not an exact Event Futures edge.

## Exact-product boundary

MEXC's current support documentation says Event Futures payout is internally based on volatility/market risk and can fluctuate. V0.8 does NOT assume historical payout was always 80%.

The 80% level is only a fixed reference hurdle chosen before outcomes.

## Hard boundaries

- No September 2026 data.
- No payout-history fabrication.
- No exact Event Futures profitability claim.
- No authentication.
- No orders.
- No account mutation.
- No merge to main.
