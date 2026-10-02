# MEXC EVENT FUTURES LAB — V0.6 CLOSEOUT + V0.7 SESSION/CALENDAR FREEZE

Date: 2026-10-02
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## V0.6 exact-product public source discovery closeout

The bounded public-web asset scanner could fetch the Event Futures pages but did not obtain directly referenced static assets or defensible public Event Futures payout/time-unit API routes from the GitHub Actions environment.

Run result:
- public pages checked: 2
- static assets fetched: 0
- candidate route strings: 0
- public candidate probes: 0
- authenticated requests: 0
- orders: 0
- account mutations: 0

Verdict:
**BLOCKED_BY_BOT_OR_ASSET_ACCESS**

This is a source-access verdict only. It does not imply that a public internal route does not exist.

Official MEXC support material independently confirms that Event Futures payout varies with volatility/market risk, is fixed at submission, settlement uses the underlying index price at expiry, and API trading is currently unsupported. Those product facts remain external documentation, not a historical payout dataset.

## V0.7 hypothesis family

Test whether fixed calendar/session states contain a directional bias strong enough to clear the Event Futures 80%-payout reference hurdle.

This family is economically and statistically distinct from:
- V0.3.1 raw continuation/reversal;
- V0.4 technical chart-state signals;
- V0.5 cross-asset lead/lag.

No V0.7 outcomes have been inspected at freeze time.

## Source and clock

MEXC public standard-futures index-price Min5 proxy:
`https://contract.mexc.com/api/v1/contract/kline/index_price/{symbol}`

Each raw Min5 close stamped `s` is treated as observable at `s + 300 seconds`.

Assets:
- BTCUSDT -> BTC_USDT
- ETHUSDT -> ETH_USDT
- NVDAUSDT -> NVIDIA_USDT
- MUUSDT -> MUSTOCK_USDT
- SPCXUSDT -> SPCXSTOCK_USDT

Historical September 2026 remains LOCKED and MUST NOT be fetched.

## Event horizons

- 10m
- 30m
- 60m
- 1440m

## Frozen calendar/session contexts

### Family A — UTC 4-hour bucket
Six fixed bins:
- UTC00_04
- UTC04_08
- UTC08_12
- UTC12_16
- UTC16_20
- UTC20_24

### Family B — UTC weekday
Seven categories:
MON, TUE, WED, THU, FRI, SAT, SUN.

### Family C — broad UTC session
- ASIA: 00:00–07:59 UTC
- EUROPE: 08:00–12:59 UTC
- US: 13:00–20:59 UTC
- LATE: 21:00–23:59 UTC

### Family D — US cash-market windows
Using `America/New_York` timezone to respect DST:
- US_OPEN_HOUR: 09:30 <= local time < 10:30
- US_MIDDAY: 11:30 <= local time < 14:30
- US_CLOSE_HOUR: 15:00 <= local time < 16:00
- US_OFF_HOURS: all other timestamps

Family D is evaluated on all five assets, but interpretation for crypto assets is strictly “calendar correlation,” not equity-market causation.

## Frozen directions

For each context cell test two deterministic predictions:
- ALWAYS_UP
- ALWAYS_DOWN

No direction is selected after observing discovery data; both are part of the frozen family.

## Entry sampling

For each event horizon H:
- anchor timestamps are aligned to H-minute UTC boundaries;
- event windows do not overlap within a cell because entry stride = H;
- for the 1-day horizon, anchors are 00:00 UTC only.

Outcome:
sign(proxy_price[t + H] - proxy_price[t]).

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
- 10m >= 120
- 30m >= 100
- 60m >= 80
- 1d >= 20

A cell becomes discovery-eligible only if:
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- the same direction is >50% in each of three chronological discovery thirds;
- minimum N is met.

Each eligible cell receives a one-sided exact binomial p-value vs p0 = 55.5555556%.

Apply Benjamini-Hochberg FDR q=0.05 across the entire V0.7 eligible family.

Only BH-selected cells may open August OOS.

## OOS gate

No context/direction changes.

Pass only if:
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- exact one-sided binomial p < 0.05 vs p0=55.5555556%;
- illustrative EV at 80% payout > 0.

Any survivor is only a **PROXY CANDIDATE**.

## Hard boundaries

- No September 2026 data.
- No exact Event Futures profitability claim.
- No historical 80% payout claim.
- No authenticated exchange calls.
- No live trading.
- No account mutation.
- No merge to main.
