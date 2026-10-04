# MEXC NVIDIA CASH-OPEN DISCOVERY — PRE-OUTCOME FREEZE V0.2

Date: 2026-10-04
Status: FROZEN BEFORE SIGNAL OUTCOMES

## Source authority

Target:
- MEXC `NVIDIA_USDT`

Historical external legs:
- Binance Futures `NVDAUSDT`
- Bitget Futures `NVDAUSDT`

MEXC declared index origins:
- BINANCE_FUTURE
- BITGET_FUTURE
- BINANCETICKER
- PYTH
- KAIKO

Pyth NVDA identity was source-gated as `Equity.US.NVDA/USD`.

Kaiko and Pyth historical data are not required for the two V0.2 predictors and must not be silently reconstructed.

The MEXC historical endpoint is usable continuously around the cash open from 2026-09-08 onward in the current public history window.

## Frozen discovery span

Use only weekday sessions:

`2026-09-09 ... 2026-10-02`

The 2026-09-08 first-usable date is excluded from outcomes.

US cash open in this span is fixed at:

`13:30 UTC`

Signal timestamp:

`13:29 UTC observable time`

A 1-minute candle stamped at raw minute start `s` becomes usable at `s+60s`.

No forward fill.
No interpolation.
No nearest-neighbor matching.

## External consensus

At any observable timestamp:

`external = mean(Binance_close, Bitget_close)`

Both legs must be present exactly at the timestamp.

## Family A — MEXC-NVIDIA-CASHOPEN-BASIS-FADE-001

At 13:29 UTC:

`basis_bps = 10000 * (MEXC / external - 1)`

Trade-sign predictor:

`side = -sign(basis_bps)`

Interpretation:
immediately before the U.S. cash open, any MEXC premium/discount versus the 24/7 Binance+Bitget consensus may be reanchored as equity-linked Pyth/Kaiko inputs become cash-market active.

No basis threshold is allowed in V0.2.

Frozen horizons:
- 2 minutes
- 5 minutes
- 15 minutes
- 30 minutes

## Family B — MEXC-NVIDIA-CASHOPEN-EXTMOM-FOLLOW-001

At 13:29 UTC:

`external_momentum_5m_bps = 10000 * (external_13:29 / external_13:24 - 1)`

Trade-sign predictor:

`side = sign(external_momentum_5m_bps)`

Interpretation:
a 24/7 external repricing immediately before the U.S. cash open may continue as the cash market incorporates the move.

No momentum threshold is allowed in V0.2.

Frozen horizons:
- 2 minutes
- 5 minutes
- 15 minutes
- 30 minutes

## Outcome

For either family:

`gross_signed_bps = side * 10000 * (MEXC_close[t+h] / MEXC_close[t] - 1)`

This is a gross scientific return, not an executable fill model.

## Discovery gate

A cell is pre-Holm eligible only if all conditions hold:
- N >= 15
- mean gross signed return > 0 bps
- median gross signed return > 0 bps
- win rate > 50%
- first chronological half mean > 0 bps
- second chronological half mean > 0 bps
- exact one-sided binomial p-value versus 50% is defined

Holm-Bonferroni is applied separately within each economic family across its four frozen horizons at family-wise alpha 0.05.

This separation is frozen before outcomes because the two mechanisms are economically distinct.

## Cost report

Report illustrative round-trip costs:
0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps.

Costs do not decide scientific survival.

MEXC public contract metadata currently reports zero maker and taker fee for `NVIDIA_USDT`, but V0.2 does not treat that metadata as authenticated execution-fee authority.

## Promotion ceiling

A Holm-selected cell is only:

`NVIDIA_CASHOPEN_DISCOVERY_CANDIDATE_ONLY`

No retrospective OOS is authorized.

A survivor requires a new pre-outcome forward freeze before any future validation.

## No rescue

After outcomes are opened, do not:
- add thresholds;
- change 13:29 signal time;
- change 5m momentum lookback;
- add/remove horizons;
- switch FOLLOW to FADE or vice versa;
- change the external consensus;
- select favorable dates;
- lower N/stability/Holm gates.

No private endpoints, account reads, wallets, orders, exchange mutation or live trading are authorized.
