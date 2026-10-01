# PERP-LAUNCH-POSTLAUNCH-SHORT-001 — V0.1

Status: FROZEN PRE-DISCOVERY / RESEARCH ONLY
Branch: perp-launch-postlaunch-short-v0.1

## Source authority
Reuse the immutable event identity from PERPETUAL-LAUNCH-SHOCK-001:
- source MVE: PLS-BINANCE-USDTM-LAUNCH-001
- 170 qualified Binance USD-M perpetual first-launch events
- 83 events in 2023
- 87 events in 2024
- exact first_open_time is the event timestamp
- source: official Binance Data Vision

The predecessor opened only 2023 launch-intensity outcomes and explicitly left 2024 market values unopened after its Discovery failed.

## Economic hypothesis
A newly launched USD-M perpetual adds leverage and short-sale access to a token that already had a Binance Spot USDT market. After the first hour of price discovery, the token tends to underperform BTC over the next 24 hours as launch excitement/positioning mean-reverts and leveraged shorting/hedging becomes available.

Trade:
- SHORT equal-USD token USD-M perpetual
- LONG equal-USD BTCUSDT USD-M perpetual

No symbol selection, no sign filter, no launch-volume filter.

## Frozen timing
T0 = frozen perpetual first_open_time.
Require contiguous official 1m USD-M kline data.

- observation window = first 60 completed minutes after T0
- entry = OPEN of the 1m bar at T0 + 60 minutes
- exit = OPEN of the 1m bar at T0 + 1,500 minutes (24h after entry)
- no stop, target, rebalance or intra-window rule

## Gross pair return
gross_pair_bps =
10000 * [ln(BTC_exit / BTC_entry) - ln(TOKEN_exit / TOKEN_entry)]

Positive = the short-token / long-BTC pair made money before costs.

## Costs
Inherited unchanged from the prior launch strategy authority:
- BASE = 60 bps all-in completed pair trade
- STRESS = 160 bps all-in completed pair trade

base_net_bps = gross_pair_bps - 60
stress_net_bps = gross_pair_bps - 160

No post-outcome cost reduction.

## Sequential design
DISCOVERY:
- all source-qualified 2023 events
- 2024 must remain unopened unless Discovery passes every gate

OOS:
- all source-qualified 2024 events
- same exact rule, timing, costs and statistics

## Minimum evidence per phase
- >=60 eligible events with complete token and BTC 1m entry/exit data
- >=40 distinct UTC launch dates
- zero unresolved duplicate event identities

## Promotion gate — ALL required
1. mean STRESS net > 0
2. UTC-launch-date cluster bootstrap 95% CI lower bound of mean STRESS net > 0
3. median STRESS net > 0
4. STRESS hit rate >= 52%
5. STRESS profit factor >= 1.20
6. mean BASE net > 0
7. at least 3 of 4 UTC calendar quarters have median STRESS net > 0

Bootstrap:
- 10,000 replications
- cluster = UTC launch date
- seed = 20261001
- confidence = 95%

## Classification
Discovery:
- POSTLAUNCH_SHORT_SURVIVES_DISCOVERY
- NO_POSTLAUNCH_SHORT_EDGE
- INSUFFICIENT_DISCOVERY_SAMPLE
- SOURCE_OR_TECHNICAL_BLOCKED

OOS:
- OOS_POSTLAUNCH_SHORT_SURVIVES
- NO_EXECUTABLE_OOS_EDGE
- INSUFFICIENT_OOS_SAMPLE
- SOURCE_OR_TECHNICAL_BLOCKED

## Anti-rescue
After 2023 outcomes are opened:
- no entry delay change
- no hold change
- no long/short inversion
- no event subset
- no symbol subset
- no side/session/volatility filter
- no cost reduction
- no alternate benchmark
- no stop/target optimization
- no 2024 opening after failed Discovery

Any changed design requires a new lab identity and untouched holdout.

## Authority
Research only.
No live trading.
No order placement.
No authenticated exchange access.
No exchange mutation.
No merge to main.
Trading authority: NONE.
