# BTC-CONVEX-TREND-CAPTURE-001 — CROSS-ASSET + COST VALIDATION FREEZE V0.1

**Frozen:** 2026-09-23 before ETH/SOL/BNB economic outcomes are opened  
**Mode:** research-only / fail-closed / no live trading  
**Parent:** recovered Quant Trailing v5 (Payoff Invertido)  
**Child:** STICKY TRAIL H1, already frozen before cross-asset outcomes

## 1. Objective

Test whether the recovered 1H mechanism transfers mechanically beyond BTC after:
- causal order timing;
- actual historical perpetual funding;
- frozen execution-slippage overlays;
- no asset-specific or timeframe-specific retuning.

This is the first potentially independent cross-asset evidence path for this family.

## 2. Untouched universe

Exactly:
- ETHUSDT perpetual
- SOLUSDT perpetual
- BNBUSDT perpetual

No asset may be removed after outcomes because it performs poorly.
No additional asset may be added to rescue a failed result.

BTC is excluded from adjudication because its outcomes were already inspected.

## 3. Timeframe and dates

Timeframe: **1h only**.

Warm-up:
- use official data before 2021-01-01 as available solely to initialize indicators.

Economic evaluation:
- 2021-01-01 00:00 UTC through 2025-12-31 23:00 UTC.

Locked:
- 2026-01-01 onward is not opened in this historical cross-asset experiment.

If a symbol lacks defensible source coverage for the required evaluation window:
- classify that asset DATA_BLOCKED;
- do not shift the start date post hoc to improve results.

## 4. Parent signal — frozen exactly

Defaults:
- zEntrada = -2.0
- lookback = 20
- stopInicial = 4%
- trailPerc = 12%
- ativaTrail = +5%
- mmRegime = 200

Entry:
- SMA20 / STDEV20 Z-score;
- RSI14 < 30;
- close < SMA20 - 2×STDEV20;
- volume > SMA20(volume);
- score >= 3;
- close > SMA200;
- long-only while flat.

No parameter changes are allowed per asset.

## 5. Parent causal execution

- evaluate entry only on completed bars;
- enter market at next bar open;
- no same-bar reentry after intrabar exit;
- no final current-bar OHLC/volume may be used before bar close;
- peak updates only after completed-bar information is causally available;
- active stop during a bar is frozen from the previous causal decision point;
- original non-latched +5% trail-selection semantics are preserved.

## 6. Sticky-Trail H1

Same exact entry, cost model, stop, trail, universe and dates.

Only change:
- after a completed-bar close first reaches >= +5% profit, trailing mode remains active until exit.

No threshold changes.

## 7. Fee and slippage layers — frozen

The parent source uses:
- commission = **10 bps per executed side**.

This parent fee is retained for all comparisons.

Slippage:
- REPRO view: 0 bps/side;
- BASE economic view: **2 bps/side adverse slippage**;
- STRESS economic view: **5 bps/side adverse slippage**.

For long market entries:
- execution price is shifted upward by the frozen slippage.

For stop/market exits:
- execution price is shifted downward by the frozen slippage.

These slippage values are fixed stress assumptions, not claims of exact historical realized slippage.

## 8. Historical funding — frozen source and formula

Primary funding source:
- official Binance USD-M Futures public funding-rate history endpoint:
  `GET /fapi/v1/fundingRate`.

Binance documents this endpoint as the historical funding-rate source for USD-M perpetuals.

For each funding timestamp occurring while a long position is open:

`funding_cashflow = - quantity × funding_mark_price × funding_rate`

Positive funding rates therefore cost the long.
Negative funding rates credit the long.

Mark-price hierarchy:
1. use the funding record's official `markPrice` where present;
2. if an old historical record lacks markPrice, use the official Binance 1h market **OPEN** whose open timestamp equals the funding timestamp as a pre-frozen fallback;
3. if neither is available, fail closed for that asset.

Funding is accumulated into account equity and trade net PnL.

Funding event ordering is frozen as follows:
- a position carried open from before a funding timestamp pays/receives that funding event;
- a position first opened exactly at that funding timestamp does **not** pay/receive that event;
- if a carried position later stops out during the same funding bar, funding is applied first, then the intrabar exit.

No funding source may be switched after outcomes because another provider gives a better result.

## 9. Starting capital and sizing

Each asset is an independent account:
- initial equity = 10,000 USDT;
- default position allocation = 95% of current equity;
- no leverage rescue;
- no portfolio netting across assets.

Family summaries use normalized percentage returns, not pooled dollar equity.

## 10. Pre-registered outputs

For Parent and Sticky H1, per asset and cost layer:
- closed trades;
- win rate;
- net return;
- CAGR;
- profit factor;
- max drawdown;
- max losing streak;
- funding paid/received;
- commission paid;
- slippage cost;
- top-1 and top-3 winner dependence;
- year-by-year PnL;
- if a position remains open at 2025-12-31 23:00 UTC, force-liquidate it at that final bar CLOSE using the applicable adverse slippage and exit commission; report that forced end liquidation separately.

Family-level:
- equal-weight mean return across the three assets;
- median asset return;
- count of positive assets;
- count with PF > 1;
- count remaining positive after removing the top winner.

## 11. Frozen scientific gates

### Parent cross-asset replication: SURVIVES

Require all:
1. at least **2 of 3 assets** have positive BASE net return;
2. at least **2 of 3 assets** have BASE PF > 1;
3. equal-weight family mean return is > 0 under STRESS;
4. at least **1 of 3 assets** remains positive after removing its single largest winner under BASE;
5. no provenance/leakage/reproduction blocker.

If not, classify:
**CROSS_ASSET_REPLICATION_FAIL** or **DATA_BLOCKED** as appropriate.

This gate does not authorize promotion or live trading by itself.

### Sticky H1

No binary “winner” is selected from this historical cross-asset experiment.

Report only pre-registered deltas versus Parent:
- return;
- PF;
- drawdown;
- tail dependence;
- asset consistency.

Any future choice between Parent and Sticky requires prospective evidence after freeze.

## 12. No-rescue rules

After outcomes:
- no threshold changes;
- no asset removal;
- no timeframe switch;
- no fee/slippage reduction;
- no funding omission;
- no direction flip;
- no “best two assets only” rescue;
- no opening 2026 to rescue 2021-2025;
- no new child hypothesis presented as validation of this one.

## 13. Forward boundary

Prospective forward boundary for this family:
**2026-09-23 after this freeze commit.**

Any future forward evidence must use the exact frozen rule and causal execution semantics.
Historical backfill after this timestamp cannot substitute for actually observed prospective evidence.

## Verdict authority

This document controls the next cross-asset run.
If code conflicts with this freeze, the freeze wins and the run is invalid.
