# MEXC EVENT FUTURES LAB — V0.6 SOURCE CLOSEOUT + V0.7 SESSION FREEZE

Date: 2026-10-02
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## V0.6 source closeout

The bounded exact-product public-source scan was operationally successful after a syntax-only fix.

Result:
- public entry pages attempted: 2
- directly fetchable static assets: 0
- candidate exact-product API route strings: 0
- public GET probes: 0
- exact public payout route hits: 0
- authenticated requests: 0
- orders: 0
- account mutations: 0

V0.6 verdict:
**BLOCKED_BY_BOT_OR_ASSET_ACCESS**

This is a source-access verdict only. It does not imply that no internal/public Event Futures data route exists.

Official MEXC documentation remains authoritative for the following product facts:
- payout is dynamic and fixed at trade submission;
- Event Futures settle against the underlying index price at expiry;
- supported expiry choices include 10m, 30m, 1h and 1d;
- Event Futures currently do not support API trading.

## Why V0.7 is scientifically distinct

V0.3.1 tested simple price continuation/reversal.
V0.4 tested common technical chart states.
V0.5 tested cross-asset lead/lag.
V0.7 tests **calendar/session directional structure** with no price-derived directional feature.

No V0.7 outcomes have been inspected at freeze time.

## Source and clock

Public MEXC standard-futures index-price Min5 proxy:
`https://contract.mexc.com/api/v1/contract/kline/index_price/{symbol}`

Raw Min5 close stamped `s` is treated as observable at `s + 300 seconds`.

Mappings:
- BTCUSDT -> BTC_USDT
- ETHUSDT -> ETH_USDT
- NVDAUSDT -> NVIDIA_USDT
- MUUSDT -> MUSTOCK_USDT
- SPCXUSDT -> SPCXSTOCK_USDT

This remains a proxy, not exact Event Futures settlement history.

## Frozen Event horizons

- 10m
- 30m
- 60m
- 1440m

## Frozen calendar/session families

Each cell tests both fixed directions independently:
- UP
- DOWN

### Family A — UTC 4-hour blocks
- 00:00–04:00
- 04:00–08:00
- 08:00–12:00
- 12:00–16:00
- 16:00–20:00
- 20:00–24:00

### Family B — broad market sessions
- ASIA: 00:00–08:00 UTC
- EUROPE: 08:00–13:30 UTC
- US_CASH: 13:30–20:00 UTC
- LATE_US: 20:00–24:00 UTC

### Family C — US cash-open subwindows
Applicable to every asset; multiple-testing correction accounts for breadth.
- US_PREOPEN: 12:30–13:30 UTC
- US_OPEN_HOUR: 13:30–14:30 UTC
- US_MORNING: 14:30–16:00 UTC
- US_AFTERNOON: 16:00–20:00 UTC

For Apr–Aug 2026, US equity cash open is frozen as 13:30 UTC. No post-outcome DST adjustment is permitted.

### Family D — weekday
- Monday
- Tuesday
- Wednesday
- Thursday
- Friday
- Saturday
- Sunday

### Family E — weekday × broad session
Cartesian product of:
- weekdays
- ASIA / EUROPE / US_CASH / LATE_US

## Entry spacing

To avoid overlapping Event outcomes:
`entry_stride = event_horizon`

Candidate timestamps are aligned to the horizon from Unix epoch and then filtered by the frozen calendar condition.

## Partitions

Discovery:
2026-04-01T00:00:00Z <= t < 2026-08-01T00:00:00Z

Retrospective OOS:
2026-08-01T00:00:00Z <= t < 2026-09-01T00:00:00Z

Historical holdout:
2026-09-01 through 2026-09-30 — LOCKED / MUST NOT BE FETCHED.

## Statistical gates

Primary economic reference:
80% payout => break-even accuracy = 55.5555556%.

Discovery minimum non-tie N:
- 10m >= 120
- 30m >= 100
- 60m >= 80
- 1d >= 30

A discovery cell becomes basic-eligible only if:
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- accuracy > 50% in each of 3 chronological discovery thirds;
- minimum N is met.

For every basic-eligible cell:
- one-sided exact binomial p-value vs p0=55.5555556%.

Apply Benjamini-Hochberg FDR q=0.05 across **all V0.7 basic-eligible cells**.

Only BH-selected cells may open August OOS.

## OOS gate

No rule changes.

A cell passes OOS only if:
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- one-sided exact binomial p-value vs 55.5555556% < 0.05;
- unit EV at illustrative 80% payout > 0.

Also report:
- required payout for EV=0;
- EV at 70%, 75%, 80%, 85%, 90%.

Any OOS survivor remains a PROXY CANDIDATE only.

## Hard boundaries

- No September 2026 data.
- No live Event Futures order.
- No authenticated MEXC request.
- No account mutation.
- No historical 80% payout assumption presented as exact fact.
- No exact-product promotion.
- No merge to main.
