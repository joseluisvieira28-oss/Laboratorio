# MEXC-BITGET-NVDA-LEADLAG-001 — PRE-OUTCOME FREEZE V0.9

Date: 2026-10-04
Status: FROZEN BEFORE SEPTEMBER NVIDIA OUTCOMES

## Source authority

MEXC `NVIDIA_USDT` ↔ Bitget `NVDAUSDT`

Source gate:
`MEXC_BITGET_NVDA_SOURCE_PASS`

MEXC public contract metadata explicitly includes `BITGET_FUTURE` among NVIDIA index origins.

## Contamination firewall

Prior NVIDIA-linked research inspected pre-September 2026 outcomes.

September was explicitly locked/not fetched by the prior Event Futures families, and the prior Global Asset index-basis run stopped before September.

V0.9 therefore excludes ALL pre-September 2026 observations.

## Mechanism

Hypothesis:

> a sufficiently large one-minute NVDA move on Bitget, when the MEXC NVIDIA contract moves less in the same minute, may lead a subsequent MEXC catch-up move in the Bitget direction.

This is a cross-venue information-propagation family.

## Frozen signal

For each fully closed aligned one-minute candle at observable time `t`:

`bitget_ret = 10000 * (BG_close[t] / BG_close[t-1] - 1)`

`mexc_ret = 10000 * (MEXC_close[t] / MEXC_close[t-1] - 1)`

`lag_gap = bitget_ret - mexc_ret`

Signal only if:

1. `abs(bitget_ret) >= shock_threshold`;
2. `sign(lag_gap) == sign(bitget_ret)`;
3. `abs(lag_gap) >= lag_gap_threshold`.

Direction:
`FOLLOW_BITGET`

No fade mode is authorized in V0.9.

## Frozen grid

Bitget shock thresholds:
- 10 bps
- 20 bps
- 40 bps
- 80 bps

Underreaction gap thresholds:
- 5 bps
- 10 bps
- 20 bps
- 40 bps

MEXC outcome horizons:
- 1 minute
- 2 minutes
- 5 minutes
- 15 minutes

64 cells total.

## Entry proxy

Signal information comes only from a completed minute.

Entry proxy is the MEXC **open of the next one-minute candle**.

This is not proof of executable fill quality; forward BBO/depth shadow is required before any execution promotion.

Exit is the MEXC close at the frozen horizon after that next-minute open.

## Frozen windows

Discovery:
`2026-09-05T00:00:00Z <= signal t < 2026-09-20T00:00:00Z`

Retrospective OOS:
`2026-09-20T00:00:00Z <= signal t < 2026-10-01T00:00:00Z`

Hard fetch boundary:
`2026-10-01T00:00:00Z`

October is not opened.

The September 5 start is chosen before outcomes because Bitget documents roughly one month of queryable 1m candle data on the public current-candle endpoint.

## Discovery gate

Per cell:
- N >= 30 non-overlapping signals;
- mean gross signed bps > 0;
- win rate > 50%;
- mean gross signed bps > 0 in every chronological discovery third;
- exact one-sided binomial p-value vs 50% defined.

Holm-Bonferroni FWER 0.05 across all eligible discovery cells.

Only Holm-selected cells may open OOS.

## OOS gate

No changes to shock, gap, horizon, direction or entry proxy.

Required:
- N >= 15;
- mean gross signed bps > 0;
- win rate > 50%;
- exact one-sided binomial p < 0.05;
- both chronological half means >= 0.

## Economic hurdle reporting

Scientific existence and execution feasibility remain separate.

Report mean net under 0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps round-trip costs.

Also report whether mean gross clears 12 / 14 / 16 bps.

These represent the current standard-MEXC-API fee-only hurdle scenarios already frozen in the Global Asset execution gate. Spread/slippage remain additional costs.

## No rescue

After outcomes open, V0.9 may not:
- change venue binding;
- lower shock or lag-gap thresholds;
- add fade direction;
- change entry proxy;
- change horizons;
- select a favorable subperiod;
- weaken statistical gates.

## Promotion ceiling

OOS PASS =>
`NVDA_CROSSVENUE_OOS_SIGNAL_CANDIDATE`

No live trading, account read, private endpoint, wallet, order or exchange mutation is authorized.
