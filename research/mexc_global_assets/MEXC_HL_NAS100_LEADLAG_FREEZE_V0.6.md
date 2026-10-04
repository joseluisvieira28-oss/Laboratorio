# MEXC-HL-NAS100-LEADLAG-001 — PRE-OUTCOME FREEZE V0.6

Date: 2026-10-04
Status: FROZEN BEFORE HISTORICAL NAS100 CROSS-VENUE OUTCOMES

## Source binding

MEXC: `NAS100_USDT`
Hyperliquid: `xyz:XYZ100` on DEX `xyz`

The binding was resolved at source level before historical lead/lag scoring:
- MEXC contract metadata declares `indexOrigin=["HYPERLIQUID"]`;
- Hyperliquid public xyz metadata contains `xyz:XYZ100`;
- independent public references identify XYZ100 as the Nasdaq-100 perpetual;
- targeted public proof showed the live MEXC index and Hyperliquid market on the same numerical scale with ~30.9 bps snapshot difference;
- no historical outcomes were opened during source resolution.

## Economic mechanism

Hypothesis:

> when the Hyperliquid Nasdaq-100 perpetual moves materially in one closed 1-minute bar and the MEXC NAS100 traded contract under-reacts in that same observable minute, MEXC may catch up in the same direction over the following minutes.

Direction is frozen to:
`FOLLOW_HYPERLIQUID`

No fade alternative is authorized in V0.6.

## Frozen discovery window

`2026-10-01T00:00:00Z <= observable t < 2026-10-04T09:00:00Z`

This NAS100 cross-venue outcome window was not scored before this freeze.

No data at or after 2026-10-04T09:00:00Z may enter V0.6.

## Clock

MEXC Min1 raw bucket start `s` becomes observable at `s+60s`.

Hyperliquid 1m candle open `t` becomes observable at `t/1000+60s`.

Only exact observable-minute matches are allowed.

## Frozen signal grid

Hyperliquid shock thresholds:
- 5 bps
- 10 bps
- 20 bps
- 40 bps

Lag-gap thresholds:
- 3 bps
- 5 bps
- 10 bps
- 20 bps

MEXC outcome horizons:
- 1 minute
- 2 minutes
- 5 minutes
- 15 minutes

64 cells total.

Signal exists when all are true:

1. `abs(hl_ret_1m) >= shock_threshold`
2. `sign(hl_ret_1m - mexc_ret_1m) == sign(hl_ret_1m)`
3. `abs(hl_ret_1m - mexc_ret_1m) >= gap_threshold`

Outcome direction is the sign of the Hyperliquid move.

Per-cell overlap cooldown equals the horizon.

## Discovery gate

Pre-Holm eligibility requires:
- N >= 20 non-overlapping signals;
- mean gross signed MEXC return > 0 bps;
- win rate > 50%;
- all three chronological discovery thirds have mean gross > 0;
- exact one-sided binomial p-value vs 50% is defined.

Holm-Bonferroni controls family-wise alpha at 0.05 over all eligible cells.

## Cost reporting

Costs do NOT determine existence of the scientific signal.

Report illustrative mean net bps at:
0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps round-trip.

12/14/16 bps represent the current standard public MEXC API maker-maker / maker-taker / taker-taker fee-only scenarios.

## Promotion ceiling

Any Holm survivor is only:

`NAS100_CROSSVENUE_DISCOVERY_CANDIDATE_ONLY`

V0.6 has NO retrospective OOS authority and NO live-trading authority.

## No rescue

After outcomes are opened V0.6 may not:
- change source binding;
- add USTECH aliases;
- change direction;
- lower or add thresholds;
- change horizons;
- select a subperiod;
- relax stability/Holm gates.

Any follow-up requires a new hypothesis and untouched future data.
