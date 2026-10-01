# PERP-LAUNCH-IMPULSE-REVERSION-001 — V0.1

Status: FROZEN PRE-DISCOVERY / RESEARCH ONLY
Branch: perp-launch-impulse-reversion-v0.1

## Source authority
Reuse immutable PERPETUAL-LAUNCH-SHOCK-001 source population:
- SOURCE_DATA_PASS
- 170 exact first Binance USD-M USDT perpetual launches
- 83 events in 2023
- 87 events in 2024
- one event per exact symbol
- 2024 market values remain unopened by predecessor and by PERP-LAUNCH-BASIS-CONVERGENCE-001.

## Economic mechanism
The first minutes after perpetual launch can overshoot because leverage and new short/hedging access arrive abruptly.
Instead of assuming a universal bullish/bearish direction, measure the token's first 15-minute relative impulse versus BTC and fade that impulse market-neutrally.

## Frozen timing and signal
At T0 = frozen futures first_open_time:
- require contiguous token USD-M perpetual and BTCUSDT USD-M 1m bars;
- observe the first 15 complete minutes;
- token impulse = ln(token close at T0+15m / token open at T0);
- BTC impulse = ln(BTC close at T0+15m / BTC open at T0);
- excess_impulse = token_impulse - BTC_impulse;
- direction = -sign(excess_impulse).

Entry:
- simultaneous equal-USD token-perp / BTC-perp pair at the close of minute 15;
- if excess_impulse > 0: SHORT token / LONG BTC;
- if excess_impulse < 0: LONG token / SHORT BTC;
- exact zero => NO TRADE.

Exit:
- simultaneous close exactly 360 minutes after entry;
- no stop, target, trailing logic or intra-window rescue.

## Gross pair return
gross_pair_bps =
direction * 10000 * [ln(token_exit/token_entry) - ln(BTC_exit/BTC_entry)]

Positive = reversal of the initial token-vs-BTC excess impulse.

No-trade event return = 0.

## Costs
Inherited unchanged from PLS-OOS-ORBREAKOUT-001:
- BASE 60 bps all-in pair round trip
- STRESS 160 bps all-in pair round trip

No cost reduction after outcomes.

## Sequential design
Discovery = all 2023 source-qualified events.
OOS = all 2024 source-qualified events, opened only if every Discovery gate passes.
Discovery failure => STOP; 2024 remains unopened.

## Minimum evidence
Per phase:
- >=60 complete source-eligible events
- >=50 executed pair trades
- zero unresolved event/source conflicts

## Primary gate — ALL required
1. mean STRESS net across all eligible events > 0
2. UTC-entry-date cluster bootstrap 95% CI lower bound for mean STRESS net > 0
3. median STRESS net among executed trades > 0
4. STRESS hit rate among executed trades >= 52%
5. STRESS profit factor among executed trades >= 1.20
6. mean BASE net across all eligible events > 0

Bootstrap:
- cluster UTC entry date
- 10,000 replications
- seed 20261001
- 95% CI

## Classifications
Discovery:
- IMPULSE_REVERSION_SURVIVES_DISCOVERY
- NO_IMPULSE_REVERSION_EDGE
- INSUFFICIENT_SAMPLE
- SOURCE_OR_TECHNICAL_BLOCKED

OOS:
- OOS_IMPULSE_REVERSION_SURVIVES
- NO_EXECUTABLE_OOS_EDGE
- INSUFFICIENT_OOS_SAMPLE
- SOURCE_OR_TECHNICAL_BLOCKED

## Anti-rescue
After 2023 outcomes open:
- no observation-window change
- no hold change
- no minimum impulse threshold
- no sign inversion
- no symbol subset
- no session/volatility filter
- no cost reduction
- no stop/target optimization
- no 2024 opening after Discovery failure

Changed design => new lab ID.

## Authority
Research only. No live trading, orders, authenticated exchange access, exchange mutation, main merge, or trading authority.
