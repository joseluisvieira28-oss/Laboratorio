# COMPOUND-INVENTORY-PERSISTENCE-001 — DISCOVERY FREEZE V0.1

Date: 2026-09-27
Status: FROZEN_PRE_OUTCOME / DISCOVERY 2023–2024 ONLY
Primary family: CREDIT
Secondary family: MICRO / FLOW

## 1. Question

When Compound III has **known seized collateral inventory still positive after the liquidation block has finished**, does that collateral asset underperform BTC over the next 24 hours?

This tests persistent protocol-inventory overhang, not the liquidation event itself.

## 2. Pre-outcome authority

Source/mechanism evidence was opened first and contained no market prices:
- 894 AbsorbCollateral logs;
- 999 BuyCollateral logs;
- 43 closed lower-bound known-inventory episodes;
- 31/43 persisted >20 blocks;
- 27/43 persisted >100 blocks;
- median closed duration 28,171 blocks.

Market-source coverage gate then passed 120/120 Binance Data Vision monthly Spot 1m archive objects for 2023–2024:
BTCUSDT, ETHUSDT, LINKUSDT, UNIUSDT, COMPUSDT.

No price row or return was opened by that gate.

## 3. Frozen inventory construction

For each collateral asset independently:
- AbsorbCollateral increments known lower-bound inventory by collateralAbsorbed.
- BuyCollateral decrements by collateralAmount, floored at zero.
- Unknown inventory before 2023-01-01 is never fabricated.
- An episode starts when known lower-bound inventory moves 0 -> positive.
- There is at most one signal per episode.
- A candidate episode is eligible only if known lower-bound inventory remains positive after all Comet logs in the start block have been processed.
- Same-block-cleared episodes are excluded because no persistent post-block state exists.

Later inventory clearing is not used to select the 24h outcome horizon.

## 4. Frozen assets

Comet collateral -> Binance Spot:
- WETH -> ETHUSDT
- LINK -> LINKUSDT
- UNI -> UNIUSDT
- COMP -> COMPUSDT

Benchmark: BTCUSDT.

WBTC is excluded because BTC is the benchmark leg.
wstETH and cbBTC are excluded because no direct Binance Spot mapping was frozen.

No asset may be added after outcomes.

## 5. Timing

For each eligible episode:
- obtain the canonical Ethereum timestamp of the episode start block;
- entry = first Binance 1m bar open strictly after the block timestamp;
- exit = Binance 1m bar open exactly 24h after entry.

Require exact BTC and asset bars at entry and exit.
Episode must have the full 24h window ending before 2025-01-01T00:00:00Z.

Missing bars => SOURCE_INCOMPLETE for that episode; no interpolation.

## 6. Primary response

For asset A:

R_A = ln(A_exit / A_entry)
R_BTC = ln(BTC_exit / BTC_entry)

REL_24H_BPS = (R_A - R_BTC) * 10,000

Frozen expected sign: negative.

No inverse-direction rescue.

## 7. Independence and sample gate

Primary observation unit = inventory episode, never minute bars.

Before scientific adjudication, sample adequacy requires:
- >=12 eligible episodes;
- >=3 represented collateral assets;
- >=8 distinct UTC ISO weeks containing episode starts;
- both 2023 and 2024 represented.

If any sample condition fails:
DISCOVERY_INSUFFICIENT_SAMPLE
and no NO_EDGE claim is allowed.

## 8. Primary inference

Cluster episodes by UTC ISO week of episode start.

Deterministic cluster bootstrap:
- resample ISO-week clusters with replacement;
- 10,000 resamples;
- seed 20260927;
- statistic = equal-weight mean REL_24H_BPS across sampled episode rows.

Because expected sign is negative, primary 95% interval must have upper bound < 0.

## 9. Frozen pass gates

DISCOVERY_MECHANISM_SUPPORTED only if ALL hold:
1. sample gate PASS;
2. global mean REL_24H_BPS < 0;
3. clustered bootstrap 95% upper bound < 0;
4. >=75% of represented asset means are negative;
5. 2023 mean < 0 and 2024 mean < 0;
6. every leave-one-episode-out global mean remains < 0.

Otherwise, with adequate sample:
DISCOVERY_FAIL_NO_SUPPORT.

No asset, year, horizon, threshold or direction may rescue a failure.

## 10. Diagnostics — zero promotion credit

Report:
- N by asset/year/month/week;
- mean/median/win-sign fraction;
- asset means;
- yearly means;
- leave-one-out extrema;
- inventory episode duration in blocks;
- inventory amount raw only as source diagnostic.

Do not use diagnostics to change the frozen primary.

## 11. Interpretation boundary

A pass means only:
persistent known Compound seized-collateral inventory contains directional information relative to BTC at the frozen 24h horizon.

It does NOT establish executable PnL, capacity, fees, slippage, Tier status or live-trading authority.

A pass may authorize only a separately frozen untouched 2025 OOS protocol.
A failure closes this exact 24h child with no rescue.
2025+ remains unopened.

## 12. Firewall

2025_plus_opened=false
fees_or_pnl_computed=false
live_trading=false
orders=false
exchange_mutation=false
capital=false
paid_data=false
main_merge=false
post_outcome_tuning=false
