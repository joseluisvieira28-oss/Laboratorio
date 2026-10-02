# MEXC EVENT FUTURES LAB — SOURCE TRANSFER FREEZE V0.3

Date: 2026-10-02
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## Why V0.3 exists

V0.1 attempted historical Min1 MEXC index-price acquisition and returned zero historical rows in the frozen Apr-Aug 2026 windows. That was a source failure, not a scientific NO_EDGE result.

V0.2 was SOURCE-ONLY and did not calculate strategy outcomes. It established that historical MEXC index-price data is available on the official public contract API at Min5 and coarser intervals for at least BTCUSDT, ETHUSDT, and NVDAUSDT in a July-2026 probe. No historical Min1 route was found in the probed routes. MUUSDT and SPCXUSDT did not produce an old-window match in that July probe.

Because no directional outcomes were inspected in V0.1/V0.2, a source-driven transfer to Min5 is allowed before outcomes.

## Frozen source

Primary proxy source:
`https://contract.mexc.com/api/v1/contract/kline/index_price/{symbol}`

Interval:
`Min5`

Frozen mappings:
- BTCUSDT -> BTC_USDT
- ETHUSDT -> ETH_USDT
- NVDAUSDT -> NVIDIA_USDT
- MUUSDT -> MUSTOCK_USDT
- SPCXUSDT -> SPCXSTOCK_USDT

This is still a STANDARD-FUTURES INDEX-PRICE PROXY. It is not proven identical to the Event Futures entry/settlement ledger.

## Frozen test matrix

Event horizons:
- 10m
- 30m
- 60m
- 1440m

Chart lookbacks observable at Min5:
- 5m
- 15m
- 60m
- 240m
- 1440m

The V0.1 1m chart lookback is marked:
`SOURCE_UNOBSERVABLE_IN_V0.3`

Signal families remain unchanged:
- CONTINUATION
- REVERSAL

No indicator additions, no optimized threshold, no ML, no post-outcome rule changes.

Total evaluable grid before source failures:
5 assets × 4 horizons × 5 lookbacks × 2 modes = 200 cells.

## Frozen partitions

Discovery:
2026-04-01T00:00:00Z <= t < 2026-08-01T00:00:00Z

Retrospective OOS:
2026-08-01T00:00:00Z <= t < 2026-09-01T00:00:00Z

Historical holdout:
2026-09-01 through 2026-09-30 — LOCKED / MUST NOT BE FETCHED.

## Frozen gates

Break-even reference at illustrative 80% payout:
55.5555556%.

Discovery cell passes only if:
- minimum non-tie N: 10m >= 200; 30m >= 150; 60m >= 100; 1d >= 60;
- Wilson 95% lower bound accuracy > 55.5555556%;
- unit EV under an 80% payout assumption > 0;
- accuracy > 50% in each of 3 chronological discovery thirds.

Only discovery passers may be opened in August OOS.

OOS pass:
- same frozen signal;
- no parameter change;
- Wilson 95% lower bound > 55.5555556%;
- unit EV at illustrative 80% payout > 0.

Any OOS survivor is only a PROXY CANDIDATE.

## Exact-product blockers preserved

An exact Event Futures profitability claim remains prohibited because:
- historical Event Futures payout-at-entry series has not been recovered;
- equivalence between this standard-futures index series and the Event Futures settlement index has not been proven;
- exact Event Futures timestamp/rounding semantics have not been reconstructed;
- Event Futures do not expose an official trading API.

## Fail-closed rules

If an asset lacks discovery/OOS coverage, mark SOURCE_BLOCKED.
If requested timestamps are not returned, skip them and report missingness.
Do not substitute symbols after seeing outcomes.
Do not fetch September 2026.
Do not merge to main.
Do not place trades.
