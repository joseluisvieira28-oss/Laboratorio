# CBBTC-ETH-MINT-BURN-FLOW-001 — PRE-OUTCOME MARKET MECHANISM FREEZE V0.1

Frozen: 2026-09-26
Freeze timing: BEFORE source census distribution, before q10/q90 values, and before any BTC price outcome is opened.

## Economic hypothesis

cbBTC is created when BTC is moved from Coinbase into wrapped on-chain form and redeemed when cbBTC returns to Coinbase and is unwrapped.

Hypothesis:

- POSITIVE_EXTREME normalized net mint flow represents unusually strong BTC migration from Coinbase into Ethereum DeFi/on-chain use and is expected to precede positive BTC spot performance.
- NEGATIVE_EXTREME normalized net burn flow represents unusually strong wrapped-BTC return/unwrapping flow and is expected to precede negative BTC spot performance.

Both tails are mandatory.

## Entry timing firewall

Flow state for UTC day t is only known after day t is complete.

Therefore no same-day BTC return is allowed.

Primary entry timestamp:
00:00 UTC of day t+1.

Primary exit timestamp:
00:00 UTC of day t+2.

Primary horizon:
24 hours.

Secondary diagnostic horizon:
entry at t+1 00:00 UTC, exit at t+4 00:00 UTC.

The 72h diagnostic cannot rescue a failed 24h primary.

## Price source

Official Binance public historical Spot market data.

Instrument:
BTCUSDT Spot.

Interval:
1d UTC klines.

Required source:
Binance public historical data files from data.binance.vision.

All used archives must be checksum-verified when official checksum files are available.

No exchange account/API key is required.

## Primary outcome

For event day t:

raw_return_24h =
(exit_open_tplus2 - entry_open_tplus1) / entry_open_tplus1

signed_return_24h:
- POSITIVE_EXTREME: +raw_return_24h
- NEGATIVE_EXTREME: -raw_return_24h

Positive signed return supports the frozen directional mechanism.

## 2026 firewall

Discovery event days may only be used when the full primary outcome remains inside 2025.

Therefore:
event day t <= 2025-12-29

Events on 2025-12-30 or 2025-12-31 are predictor evidence only and may not open 2026 prices.

For the 72h diagnostic:
event day t <= 2025-12-27

No 2026 Binance archive/file/API response may be accessed.

## Discovery sample requirement after outcome eligibility

Even after FLOW_PREDICTOR_SAMPLE_PASS, the primary outcome test requires:

- >=20 eligible events total;
- >=6 POSITIVE_EXTREME;
- >=6 NEGATIVE_EXTREME.

If boundary censoring reduces the sample below this:
DISCOVERY_OUTCOME_INSUFFICIENT_SAMPLE.

No threshold or date rescue.

## Frozen statistical gate

If sample minimum passes:

1. pooled mean signed_return_24h;
2. mean signed_return_24h for POSITIVE_EXTREME;
3. mean signed_return_24h for NEGATIVE_EXTREME;
4. 10,000 deterministic event-row bootstrap resamples;
5. bootstrap seed = 20260926;
6. percentile 95% confidence interval of pooled mean.

FLOW_DISCOVERY_PASS requires ALL:

- pooled mean signed_return_24h > 0;
- bootstrap 95% lower bound > 0;
- POSITIVE_EXTREME mean signed return > 0;
- NEGATIVE_EXTREME mean signed return > 0.

Otherwise:
FLOW_DISCOVERY_FAIL.

The 72h diagnostic cannot alter the primary verdict.

## No-rescue rules

If Discovery fails, do NOT:
- invert the sign;
- drop one tail;
- switch q10/q90;
- use raw flow instead of normalized flow;
- change entry timing;
- switch to same-day returns;
- change 24h primary horizon;
- choose 72h as new primary;
- select a subperiod/weekday/month;
- switch price venue.

## OOS / holdout

2026 remains protected and CLOSED.

Only FLOW_DISCOVERY_PASS may permit a separate, newly frozen OOS/holdout opening authority.

## Trading firewall

Even FLOW_DISCOVERY_PASS is mechanism evidence only.

No fees, slippage, execution venue, position sizing, PnL or live trading are authorized by this freeze.
