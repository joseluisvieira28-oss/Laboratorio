# MEXC NVIDIA CASH-CLOSE DISCOVERY — PRE-OUTCOME FREEZE V0.3

Date: 2026-10-04
Status: FROZEN BEFORE CASH-CLOSE OUTCOMES

## Source authority

Target:
- MEXC `NVIDIA_USDT`

Historical external legs:
- Binance Futures `NVDAUSDT`
- Bitget Futures `NVDAUSDT`

Cash-close transport source gate:
- run `37227015100`
- verdict `NVIDIA_CASHCLOSE_SOURCE_PASS`

The source-verification date `2026-09-30` is burned and excluded from outcomes.

## Frozen discovery span

Weekday sessions:

`2026-09-09 ... 2026-10-02`

excluding:

`2026-09-30`

U.S. cash close in this span:

`20:00 UTC`

Signal timestamp:

`19:59 UTC observable time`

A 1-minute candle stamped at raw minute start `s` becomes usable at `s+60s`.

No forward fill.
No interpolation.
No nearest-neighbor matching.

## External consensus

At any observable timestamp:

`external = mean(Binance_close, Bitget_close)`

Both external legs must be present exactly.

## Family A — MEXC-NVIDIA-CASHCLOSE-BASIS-FADE-001

At 19:59 UTC:

`basis_bps = 10000 * (MEXC / external - 1)`

Trade-sign predictor:

`side = -sign(basis_bps)`

Mechanism:
as U.S. regular-session equity-linked anchors stop updating at 20:00 UTC, any MEXC premium/discount versus the 24/7 Binance+Bitget consensus may compress.

No basis threshold is allowed.

Frozen horizons:
- 2 minutes
- 5 minutes
- 15 minutes
- 30 minutes

## Family B — MEXC-NVIDIA-CASHCLOSE-EXTMOM-FOLLOW-001

At 19:59 UTC:

`external_momentum_5m_bps = 10000 * (external_19:59 / external_19:54 - 1)`

Trade-sign predictor:

`side = sign(external_momentum_5m_bps)`

Mechanism:
external 24/7 repricing immediately before the close may continue after regular-session anchors stop updating.

No momentum threshold is allowed.

Frozen horizons:
- 2 minutes
- 5 minutes
- 15 minutes
- 30 minutes

## Outcome

`gross_signed_bps = side * 10000 * (MEXC_close[t+h] / MEXC_close[t] - 1)`

Gross scientific return only; not an executable fill model.

## Discovery gate

A cell is pre-Holm eligible only if:
- N >= 15
- mean gross signed return > 0
- median gross signed return > 0
- win rate > 50%
- first chronological half mean > 0
- second chronological half mean > 0

Exact one-sided binomial p-values versus 50% are computed.

Holm-Bonferroni is applied across all four horizons within each economic family at family-wise alpha 0.05.

## Cost reporting

Illustrative round-trip scenarios:
0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps.

Costs do not decide scientific survival.

## Promotion ceiling

A Holm-selected cell is only:

`NVIDIA_CASHCLOSE_DISCOVERY_CANDIDATE_ONLY`

No retrospective OOS is authorized.

Any survivor requires a new pre-outcome forward freeze.

## No rescue

After outcomes are opened, do not:
- add thresholds;
- move the 19:59 signal time;
- change the 5m momentum lookback;
- add/remove horizons;
- change direction;
- change the external consensus;
- reinclude 2026-09-30;
- select favorable dates;
- lower N/stability/Holm gates.

No private endpoints, account reads, wallets, orders, exchange mutation or live trading are authorized.
