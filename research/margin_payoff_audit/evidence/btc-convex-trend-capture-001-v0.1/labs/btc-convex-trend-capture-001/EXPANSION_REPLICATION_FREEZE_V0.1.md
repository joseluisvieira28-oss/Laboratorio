# BTC-CONVEX-TREND-CAPTURE-001 — EXPANSION REPLICATION FREEZE V0.1

**Frozen:** 2026-09-23 before any economic outcomes from this universe are opened  
**Role:** second independent cross-sectional replication  
**Parent only for adjudication:** recovered V5 causal rule  
**No retuning permitted**

## Universe

Exactly:
- XRPUSDT
- DOGEUSDT
- ADAUSDT
- LINKUSDT
- AVAXUSDT

No asset may be removed after outcomes.
No additional asset may be added to rescue failure.

## Timeframe / dates

- timeframe: 1h
- warm-up: official data before 2021-01-01 as available
- economic window: 2021-01-01 00:00 UTC through 2025-12-31 23:00 UTC
- 2026 remains locked

If an asset lacks defensible complete source coverage under the source rules below:
- classify it DATA_BLOCKED;
- do not shift its economic start date;
- do not replace it after outcomes.

## Exact Parent rule

Unchanged from recovered V5:
- zEntrada = -2.0
- lookback = 20
- stopInicial = 4%
- trailPerc = 12%
- ativaTrail = +5%
- mmRegime = 200
- score >= 3
- long only
- close > SMA200 regime filter
- original non-latched trailing semantics

No asset-specific changes.

## Causal execution

Unchanged:
- signal only on completed bars;
- entry next bar OPEN;
- no same-bar historical reentry using final current-bar information;
- stop active during a bar is known before that bar path;
- peak/high and close-dependent state update only after bar completion.

## Costs

Exactly the same as the first untouched replication:
- commission = 10 bps per executed side
- REPRO slippage = 0 bps/side
- BASE = 2 bps adverse/side
- STRESS = 5 bps adverse/side
- official historical USD-M perpetual funding

## Source hierarchy

Market bars:
1. official Binance Vision monthly USD-M 1h klines;
2. if a specific hourly bar is absent from the monthly archive, use the official daily USD-M 1h kline at the same exact timestamp;
3. conflicting monthly/daily values => FAIL_CLOSED;
4. no interpolation.

Funding:
- official Binance funding-history records;
- raw timestamp preserved;
- nearest-hour normalization only if deviation <= 1,000 ms;
- >1,000 ms => DATA_TIMESTAMP_BLOCKED.

Funding mark:
1. direct funding-record markPrice;
2. official monthly USD-M 1h markPriceKline OPEN at exact normalized timestamp;
3. official daily USD-M 1h markPriceKline OPEN at exact normalized timestamp;
4. otherwise DATA_BLOCKED.

No spot fallback.
No ordinary market-price fallback for funding mark.
No nearest-neighbor substitution.

## Pre-registered outputs

Per asset BASE/STRESS:
- trades
- win rate
- net return
- CAGR
- PF
- max mark-to-market DD
- max losing streak
- funding
- commission
- slippage
- top-1 / top-3 dependence
- year-by-year PnL

Family:
- equal-weight mean return
- median return
- positive asset count
- PF>1 asset count
- positive-after-top1-removal count

## Frozen gate

Expansion replication SURVIVES only if all hold:
1. at least **3 of 5** non-blocked assets have positive BASE return;
2. at least **3 of 5** non-blocked assets have BASE PF > 1;
3. STRESS equal-weight family mean > 0;
4. at least **2 of 5** non-blocked assets remain positive after removing their single largest winner;
5. at least **4 of 5** assets are source-valid and adjudicable;
6. no provenance or causal-execution blocker.

Otherwise:
- CROSS_SECTION_EXPANSION_FAIL, or
- DATA_BLOCKED if fewer than four assets are source-valid.

## No-rescue rules

After outcomes:
- no threshold changes;
- no asset removal;
- no timeframe changes;
- no fee/slippage reduction;
- no funding omission;
- no direction flip;
- no choosing a “best subset” as the family result;
- no opening 2026 to rescue the outcome.

This experiment cannot promote itself to live trading.
