# ETF-CME EVENT FUTURES TRANSFER — MIN30 SOURCE TRANSFER FREEZE V1.0.2

Date: 2026-10-02
Status: PRE-OUTCOME / FAIL-CLOSED

## Source remediation basis

V1.0 produced no scored outcomes because historical MEXC Min5 data was unavailable in 2022–2025.
V1.0.1 was SOURCE-ONLY and established that official MEXC BTC_USDT historical index-price K-lines are available in 2022, 2023, 2024 and 2025 at **Min30 and coarser** intervals.

No V1.0 directional outcome was observed.

Therefore this source-only transfer is frozen before outcomes.

## Preserved external signal

Exactly preserve `ETF-CME-INSTFLOW-001`:

- CFTC dataset: `6dca-aqww`
- contract code: `133741`
- signal = delta(noncommercial_long - noncommercial_short) / current open interest
- positive => UP
- negative => DOWN
- zero => FLAT
- information-safe timestamp = report date + 8 calendar days at 00:00 UTC
- no magnitude threshold
- no direction inversion
- no filtering by price outcome

## Price proxy transfer

MEXC public standard-futures index-price K-line:
`/api/v1/contract/kline/index_price/BTC_USDT`

Frozen raw interval:
`Min30`

Clock rule:
a Min30 close stamped `s` is treated as observable at `s + 1800 seconds`.

Required exact proxy timestamps are never interpolated.

## Evaluable Event horizons

- 30m
- 60m
- 1440m

10m is explicitly:
`SOURCE_UNOBSERVABLE_IN_HISTORICAL_MEXC_MIN30`

and may not be approximated.

## Historical partitions

Discovery:
2022-01-01 <= exact entry < 2025-01-01 UTC.

OOS:
2025-01-01 <= exact entry < 2026-01-01 UTC.

2026:
LOCKED / NOT SCORED / NOT FETCHED.

## Statistical gate

Reference payout:
80%, break-even accuracy 55.5555556%.

Discovery, for each of three horizons:
- N >= 100 non-ties;
- point accuracy >55.5555556%;
- Wilson 95% lower bound >50%;
- each chronological discovery third >50%;
- exact one-sided binomial p vs p0=55.5555556%.

Apply BH FDR q=.05 across basic-passing horizons.

Only BH-selected horizons open 2025 OOS.

OOS pass:
- N >=30;
- accuracy >55.5555556%;
- Wilson lower >50%;
- exact one-sided p <.05;
- EV at illustrative 80% payout >0.

Report EV at 70/75/80/85/90% and required payout for EV=0.

## Interpretation

Any survivor is only:
`ETF_CME_TO_EVENT_FUTURES_MIN30_PRICE_PROXY_CANDIDATE`

It is not exact Event Futures profitability because historical payout-at-entry and settlement-index equivalence remain unproven.

## Hard boundaries

- No 10m approximation.
- No 2026 scoring.
- No post-outcome tuning.
- No authenticated MEXC.
- No orders.
- No account mutation.
- No main merge.
