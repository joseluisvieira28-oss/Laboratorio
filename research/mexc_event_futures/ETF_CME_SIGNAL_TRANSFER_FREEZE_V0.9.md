# MEXC EVENT FUTURES LAB — ETF-CME SIGNAL TRANSFER FREEZE V0.9

Date: 2026-10-02
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## Prior Event Futures result preserved

V0.8B successfully resolved every required Binance BTCUSDT 5m proxy timestamp for the immutable OPTIONS-SPOTPERP signal transfer.

V0.8B result:
- 10m accuracy: 48.64%
- 30m accuracy: 51.78%
- 60m accuracy: 49.71%
- 1d accuracy: 51.20%
- BH-selected horizons: 0
- 2025 OOS opened: 0

Verdict:
`NO_PROXY_SURVIVOR_AT_FROZEN_V08B_GATE`.

No post-outcome rescue of OPTIONS-SPOTPERP is permitted.

## V0.9 economically distinct hypothesis

V0.9 transfers the already-frozen weekly institutional-positioning signal from:

`ETF-CME-INSTFLOW-001`

Parent scientific rule:
- regulated CFTC CME Bitcoin futures non-commercial net-position change, normalized by open interest;
- positive parent signal => UP;
- negative parent signal => DOWN;
- exact parent entry timestamp is reused from the immutable parent ledger.

This is not a retuning of V0.8B. It uses a different economic information source and a different signal cadence.

## Immutable parent evidence

Discovery:
- GitHub Actions run: `34814321802`
- artifact ID: `10336122105`
- artifact name: `etf-cme-instflow-001-discovery-34814321802-1`
- artifact digest: `sha256:9494ab9aa7bdd3f85551b74e99f0c720b798b73fe6f1a4f61c1dc8dd55c50322`
- ledger: `discovery_ledger.csv`
- expected evaluable rows: 348
- years: 2018–2024

Independent 2025 OOS:
- GitHub Actions run: `34815006815`
- artifact ID: `10335473231`
- artifact name: `etf-cme-instflow-001-oos-2025-34815006815-1`
- artifact digest: `sha256:40bd341c300532e5b67127a098c82ecf2f41e1cc4a3ce646ac824b27529f9bd1`
- ledger: `oos_2025_observations.csv`
- expected evaluable rows: 50
- parent 2025 classification: `OOS_PATH2_PASS / V2 TIER 2 PROMOTED CANDIDATE — FRAGILE`

V0.9 consumes only:
- parent entry date/timestamp;
- parent frozen position sign.

Parent 7-day outcomes are not used to choose V0.9 rules.

## Frozen outcome source

Binance public monthly spot archive:

`https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/5m/BTCUSDT-5m-YYYY-MM.zip`

Price at an Event Futures timestamp:
**open price of the exact BTCUSDT 5m bar whose open timestamp equals that UTC timestamp**.

No interpolation.
No nearest-bar substitution.
No close-price substitution.
No post-outcome source replacement.

Required source interval:
from the first parent entry month in 2018 through December 2025 only.

No 2026 source archive may be fetched.

## Frozen Event Futures horizons

- 10m
- 30m
- 60m
- 1440m

Entry:
exact immutable `entry` date from the parent ledger at 00:00 UTC.

Prediction:
- parent position +1 => UP
- parent position -1 => DOWN
- position 0 => no event

Outcome:
sign(Binance 5m open at entry+H minus Binance 5m open at entry).

Tie:
record separately; exclude from binomial N.

## Discovery gate

Reference payout:
80%.

Break-even accuracy:
55.5555556%.

Per frozen horizon:
- source coverage >=95%;
- non-tie N >=300;
- accuracy >55.5555556%;
- Wilson 95% lower bound >50%;
- at least 5 of 7 calendar years 2018–2024 have accuracy >50%;
- one-sided exact binomial p-value against p0=55.5555556%.

Apply Benjamini-Hochberg FDR q=0.05 across all four horizons.

Only BH-selected horizons may open the immutable 2025 OOS Event Futures translation.

## 2025 OOS gate

For each frozen selected horizon:
- source coverage >=95%;
- non-tie N >=45;
- accuracy >55.5555556%;
- Wilson 95% lower bound >50%;
- exact one-sided binomial p <0.05 vs p0=55.5555556%;
- illustrative EV at 80% payout >0;
- at least 3 of the 4 calendar quarters have accuracy >50%.

Any survivor becomes:

`CROSS_SOURCE_PROXY_CANDIDATE__ETF_CME_SIGNAL_TRANSFER`

This is NOT an exact MEXC Event Futures edge.

## Exact-product blockers preserved

Even a V0.9 survivor cannot be promoted to exact Event Futures profitability because:
- historical payout-at-entry is unavailable;
- Event Futures settlement-index equivalence to Binance spot is unproven;
- exact product entry/expiry rounding semantics are unproven.

## Hard boundaries

- No live trading.
- No Event Futures orders.
- No authenticated MEXC calls.
- No account mutation.
- No parent signal change.
- No horizon change after outcomes.
- No 2026 data.
- No merge to main.
