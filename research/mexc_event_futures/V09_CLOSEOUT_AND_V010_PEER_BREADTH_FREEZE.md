# MEXC EVENT FUTURES LAB — V0.9 CLOSEOUT + V0.10 PEER-BREADTH FREEZE

Date: 2026-10-02
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## V0.9 closeout

V0.9 tested completed-candle geometry across all five displayed Event Futures underlyings.

Result:
- frozen discovery cells: 480
- basic discovery-eligible cells: 9
- Benjamini-Hochberg FDR q=0.05 selected: 0
- August OOS opened: 0
- September 2026 holdout: LOCKED / NOT FETCHED

Verdict:
**NO_PROXY_SURVIVOR for the frozen candle-geometry family.**

## V0.10 hypothesis family

Test whether directional breadth across the other displayed Event Futures underlyings predicts the target asset's next Event Futures horizon.

This is a cross-sectional consensus hypothesis, distinct from the single-leader V0.5 lead/lag family.

No V0.10 outcomes have been inspected at freeze time.

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

September 2026 remains LOCKED and MUST NOT be fetched.

## Frozen target construction

For each target asset, the peer set is the other four assets.

At entry time `t`, for lookback `L`, calculate each peer's signed return:

`sign(P_peer[t] - P_peer[t-L])`

Peer return exactly zero is neutral and does not count as UP or DOWN.

## Frozen lookbacks

- 10m
- 30m
- 60m
- 240m

## Frozen Event Futures horizons

- 10m
- 30m
- 60m
- 1440m

## Frozen breadth thresholds

1. `THREE_OF_FOUR`
   - signal exists only if at least 3 peers have the same non-zero sign.

2. `FOUR_OF_FOUR`
   - signal exists only if all 4 peers have the same non-zero sign.

If both UP and DOWN qualification are impossible simultaneously by construction.

## Frozen modes

- `FOLLOW_BREADTH`: predict the peer-consensus sign.
- `FADE_BREADTH`: predict the opposite sign.

No weighting by asset, volatility, correlation, or market cap is allowed in V0.10.

## Entry sampling

For lookback L and event horizon H:
`entry_stride = max(L, H)`.

Entries are UTC-aligned to that stride.
Outcome:
`sign(P_target[t+H] - P_target[t])`.

Ties are recorded separately and excluded from binomial N.

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
- 10m >= 100
- 30m >= 80
- 60m >= 60
- 1d >= 20

A cell is discovery-eligible only if:
- minimum N is met;
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- accuracy > 50% in each of three chronological discovery thirds;
- one-sided exact binomial p-value vs p0=55.5555556% is computable.

Apply Benjamini-Hochberg FDR q=0.05 across the entire eligible V0.10 family.

Only BH-selected cells may open August OOS.

## OOS gate

No parameter change.

Pass only if:
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- one-sided exact binomial p < 0.05 vs p0=55.5555556%;
- illustrative EV at 80% payout > 0.

Any survivor remains a **PROXY CANDIDATE**.

## Meta-governance note

Repeated research families do not earn access to the September holdout.
The September 2026 holdout remains a separate untouched adjudication layer and will not be opened merely because a future family produces a discovery/OOS survivor.

## Hard boundaries

- No September 2026 data.
- No exact Event Futures profitability claim.
- No historical 80% payout claim.
- No authentication.
- No orders.
- No account mutation.
- No merge to main.
