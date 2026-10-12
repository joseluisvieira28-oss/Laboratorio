# BTC-CONVEX-TREND-CAPTURE-001 — CHILD HYPOTHESIS H2 RISING-REGIME FREEZE

**Frozen:** 2026-09-24 before outcomes from the third basket are opened  
**Status:** NEW CHILD HYPOTHESIS / ZERO PRIOR-BASKET PROMOTION CREDIT  
**Parent:** recovered V5 causal rule

## Motivation

Post-outcome comparison of the first two untouched baskets suggests that the Parent's main weakness is not its ~4% loss size but insufficient trend persistence after extreme pullback entries.

The Parent regime condition:

`close > SMA200`

may admit rebounds above a declining long-term average.

H2 tests the minimal structural change:

`close > SMA200 AND SMA200 > SMA200[mmRegime]`

with the already-existing:
`mmRegime = 200`.

No new numerical lookback is introduced.

## H2 rule

Everything is identical to Parent except:

**Parent**
`regimeOK = close > SMA200`

**H2**
`regimeOK = close > SMA200 AND SMA200 > SMA200[200]`

Unchanged:
- zEntrada = -2.0
- lookback = 20
- stopInicial = 4%
- trailPerc = 12%
- ativaTrail = 5%
- score >= 3
- long-only
- original non-latched trail semantics
- causal execution
- 95% equity allocation
- commission = 10 bps/side
- BASE slippage = 2 bps/side
- STRESS slippage = 5 bps/side
- official historical USD-M perpetual funding

## Third untouched basket

Exactly:
- LTCUSDT
- BCHUSDT
- TRXUSDT
- DOTUSDT
- UNIUSDT

No asset may be removed after economic outcomes.
No replacement asset may be added after outcomes.

## Timeframe and dates

- timeframe: 1h
- evaluation: 2021-01-01 00:00 UTC through 2025-12-31 23:00 UTC
- warm-up from official pre-boundary data
- 2026 remains locked

## Source rules

Same frozen official-source hierarchy as Amendments 004-007:
- official Binance Vision monthly 1h market klines;
- exact official daily 1h completion only for missing hourly timestamps;
- no interpolation;
- official funding-history records;
- <=1 second timestamp normalization;
- direct funding markPrice first;
- official monthly markPriceKline exact timestamp second;
- official daily markPriceKline exact timestamp third;
- otherwise DATA_BLOCKED.

At least 4/5 assets must be source-valid.

## Comparator

Run both:
- Parent unchanged
- H2 Rising-Regime

Parent outcomes on this third basket are also untouched before this freeze and act only as a frozen benchmark.

## Pre-registered H2 gate

H2 **SURVIVES** only if all hold:

1. at least **3 of 5** adjudicable assets have positive BASE return;
2. at least **3 of 5** have BASE PF > 1;
3. STRESS equal-weight family mean > 0;
4. at least **2 of 5** remain positive after removing their largest winner;
5. at least **4 of 5** assets are source-valid;
6. H2 BASE equal-weight family mean return is greater than Parent BASE family mean return on the same untouched basket;
7. no provenance or causal-execution blocker.

Otherwise:
- H2_FAIL, or
- DATA_BLOCKED if fewer than four assets are adjudicable.

## No-rescue rules

After outcomes:
- do not change the 200-bar slope comparison;
- do not change Parent thresholds;
- do not remove losing assets;
- do not change timeframe;
- do not reduce costs;
- do not omit funding;
- do not open 2026 to rescue H2;
- do not turn the better historical asset subset into the declared universe.

## Promotion boundary

A H2 pass would be evidence for a new child mechanism, not automatic live authority.

The prior ETH/SOL/BNB and XRP/DOGE/ADA/LINK/AVAX outcomes cannot be reused as independent validation for H2.
