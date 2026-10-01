# EXTREME-FLOW-REVERSION-OOS-001 — 2025 OOS V0.1

Status: FROZEN PRE-OOS / RESEARCH ONLY
Branch: extreme-flow-reversion-oos-v0.1

## Discovery origin
FLOW-PATH-ABSORPTION-HIST-002 tested 2020-2024 and returned NO_MECHANISM for the failed-auction vs efficient-acceptance contrast. Its Discovery showed both primary groups with negative median signed R60. The 2025 OOS window was NOT opened by that lab.

This new hypothesis is therefore explicitly Discovery-derived and must be tested only once on untouched 2025 data. It does not reinterpret the failed parent as a success.

## Hypothesis
After extreme BTCUSDT spot aggressor flow with elevated participation, price tends to mean-revert against the aggressor direction over the next 60 minutes, regardless of path-efficiency class.

## Source
Official public Binance Vision BTCUSDT Spot 1m monthly kline archives, each verified against official .CHECKSUM.

For each UTC-aligned 5m bar:
- base_volume = sum of the five 1m base volumes
- taker_buy = sum of the five 1m taker-buy base volumes
- aggressive_sell = base_volume - taker_buy
- delta_pct = (taker_buy - aggressive_sell) / base_volume
- direction d = sign(delta_pct)

Exactly five aligned 1m bars are required.

## Frozen event rule
Rolling baseline: previous 2,016 valid 5m bars.

Extreme-flow event candidate iff:
- abs(delta_pct) >= rolling q95 of prior abs(delta_pct)
- base_volume >= rolling q75 of prior base_volume
- direction is non-zero

Accepted event cooldown: 12 bars / 60 minutes. A candidate inside cooldown is suppressed and does not count.

No path efficiency, POC, VA, imbalance, session, volatility, news, side, price-level, or trend filter is allowed.

## Outcome
Primary:
R60 = d * (close_T+60m / close_T0 - 1) * 10000

R60 < 0 = reversal against aggressor direction.
R60 > 0 = continuation.

R5/R15/R30/R240 may be stored as secondary descriptive outcomes only. They have zero rescue authority.

## Frozen OOS
Warmup/source context: 2024-12.
Evaluable window: 2025-01-01 00:00 UTC through 2026-01-01 00:00 UTC.

No data from 2025 was opened by the predecessor runner before this freeze.

## Minimum evidence
- >=200 accepted extreme-flow events
- >=30 distinct UTC event dates
- >=99% valid 5m source coverage
- >=99% valid R60 coverage
- zero unresolved source conflicts

## Primary OOS gate
OOS_REVERSION_SURVIVES requires ALL:
1. median R60 < 0
2. deterministic 10,000-resample bootstrap 95% CI for median R60 has upper bound < 0
3. reversal rate P(R60<0) > 50%
4. Wilson 95% lower bound of reversal rate > 50%
5. at least 3 of 4 UTC calendar quarters in 2025 have median R60 < 0

If minimum evidence is met but any primary condition fails: OOS_REVERSION_FAILED.

Bootstrap seed: 20261001.

## Anti-rescue
After OOS opens:
- no threshold/quantile change
- no cooldown change
- no horizon change
- no added filter
- no side split
- no session split
- no lag shift
- no alternative source
- no event deletion
- no quarter deletion
- no secondary-horizon rescue

Any changed design requires a new identity and new untouched holdout.

## Authority
Mechanism research only.
No live trading.
No order routing.
No exchange mutation.
No main merge.
No edge/promotion claim from this lab alone.
Trading authority: NONE.
