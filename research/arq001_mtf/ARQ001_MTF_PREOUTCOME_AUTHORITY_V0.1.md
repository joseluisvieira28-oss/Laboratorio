# ARQ-001-MTF-001 — DOMINANCE-REGIME BTC→ALT FOLLOWER — PRE-OUTCOME AUTHORITY V0.1

Date: 2026-09-23
Branch: `arq001-mtf-dominance-v0.1`
State: FROZEN_PRE_DISCOVERY / RESEARCH_ONLY / OUTCOME_BLIND

## Lineage

This is a NEW prospective sibling of ARQ-001-DRF-001.

ARQ-001-DRF-001 remains frozen as SOURCE_GATE_BLOCKED because its original contract requires 1-minute BTC.D / USDT.D / TOTAL3 observations during HH:00..HH:02.

ARQ-001-MTF-001 does NOT rewrite that failed source contract. It asks the same economic-mechanism question at a new, independently frozen clock because the 1-minute TradingView history is not available.

No ARQ-001 market outcome has been opened before this authority.

## Research question

Does a completed 4-hour BTC.D / USDT.D / TOTAL3 regime identify a subset of BTC→ALT residual-follower events on 1-hour Binance data with stronger subsequent 1-hour ALT returns after costs?

## Sources

### Regime source
Official TradingView CRYPTOCAP CSV exports supplied by the operator:
- BTC.D, 4H
- USDT.D, 4H
- TOTAL3, 4H

The canonical source receipt freezes the original file SHA256 values before any market outcome.

### Price source
Official Binance Vision USD-M Futures monthly 1h klines + published CHECKSUM sidecars for:
- BTCUSDT
- ETHUSDT
- SOLUSDT
- BNBUSDT
- XRPUSDT
- DOGEUSDT

No REST fallback, scraping mirror, exchange mutation or paid data.

## Temporal firewall

Discovery:
- information/event timestamps: 2024-01-01T04:00:00Z through 2024-12-31T20:00:00Z
- target next-hour return must remain inside calendar year 2024

Warm-up:
- Binance 1h data from 2023-12-01 is allowed only for backward-looking beta/z-score warm-up.
- TradingView regime history begins 2024-01-01; no synthetic pre-2024 regime backfill.

Locked:
- 2025 = CONFIRMATION LOCKED
- 2026 = FINAL HOLDOUT LOCKED

The supplied CSV files physically contain later rows, but the Discovery runner MUST filter to timestamp < 2025-01-01 before any regime value is used in scientific calculations.

## Event clock

Candidate event times T are exactly the 4H UTC boundaries:
04:00, 08:00, 12:00, 16:00, 20:00, 00:00.

At event time T:
1. the TradingView 4H candle with open time T-4h has fully closed;
2. the Binance 1h candle with open time T-1h has fully closed;
3. entry is conceptually at the next Binance 1h bar open T;
4. primary outcome is ALT 1h log return from T to T+1h.

No information timestamped at or after T+1h may enter the signal.

## 4H regime

Using TradingView 4H closes:

Long/risk-on regime at T:
- BTC.D 4H log return over the completed candle < 0
- USDT.D 4H log return over the completed candle < 0
- TOTAL3 4H log return over the completed candle > 0

Short/risk-off regime at T:
- BTC.D 4H log return > 0
- USDT.D 4H log return > 0
- TOTAL3 4H log return < 0

Zero change in any component = NO_FULL_REGIME_CONFIRMATION.

No magnitude threshold may be introduced after outcomes.

## 1H BTC→ALT residual follower baseline

Universe: ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT.

For each ALT and event T:

### Beta
- 30 calendar days of completed 1h log returns immediately before T-1h candle;
- OLS beta of ALT 1h returns on BTC 1h returns with intercept;
- require >= 95% of expected 720 hourly return pairs and at least 684 valid pairs;
- current signal hour is excluded from beta estimation.

### Signal-hour returns
- BTC signal return = log(close[T-1h] / open[T-1h])
- ALT signal return = log(close[T-1h] / open[T-1h])
- residual_gap = ALT signal return - beta * BTC signal return

### Causal z-scores
For BTC signal return and residual_gap separately:
- use the previous 30 calendar days of corresponding event-clock observations for that exact UTC event slot;
- current event excluded;
- require >= 150 prior valid 4H-boundary observations;
- sample mean/std;
- zero std => ineligible;
- z clipped to [-5,+5].

### Baseline signal A
Long follower:
- btc_z >= +0.75
- residual_gap_z <= -1.0

Short follower:
- btc_z <= -0.75
- residual_gap_z >= +1.0

Direction is always the BTC direction / expected ALT catch-up direction.

No parameter search.

## Ablation

A = baseline BTC + residual follower.
B = A + BTC.D sign agrees with direction.
C = B + USDT.D sign agrees with direction.
D = C + TOTAL3 sign agrees with direction (full regime).

Primary question: Does D-confirmed improve on A and survive costs?

D-rejected = baseline A signal that does not satisfy full D confirmation.

## Outcome

Primary gross signed return:
- long: +log(ALT_close[T+1h] / ALT_open[T])
- short: -log(ALT_close[T+1h] / ALT_open[T])

Primary net return deducts frozen round-trip cost.

Costs:
- LOW = 10 bps
- BASE = 12 bps
- STRESS = 14 bps

No stop, take-profit, leverage or intrabar path assumptions.

## Discovery gates — ALL required

Pooled across all five ALTs, with each ALT-event as one observation:

1. source/provenance PASS;
2. >= 200 D-confirmed observations total;
3. >= 20 D-confirmed observations in at least 4 of 5 ALTs;
4. pooled D-confirmed mean net return at BASE12 > 0;
5. pooled D-confirmed mean net return at STRESS14 > 0;
6. pooled mean(D-confirmed BASE12) - mean(D-rejected BASE12) > 0;
7. moving UTC-day block bootstrap 95% lower bound of pooled D-confirmed BASE12 mean > 0;
8. at least 3 of 5 ALTs have positive BASE12 mean;
9. remove best 1% of D-confirmed trades by BASE12 net return and pooled mean remains > 0;
10. remove the single best ALT by BASE12 mean and remaining pooled mean remains > 0.

Bootstrap:
- 10,000 repetitions
- seed 140001
- sample UTC-day blocks with replacement
- resample complete days, preserving all ALT events within each sampled day
- two-sided percentile interval; gate uses 2.5th percentile > 0.

No FDR gate is added because the primary endpoint is pooled and the five ALT results are robustness diagnostics, not independently promoted hypotheses.

## Discovery terminal states

- DISCOVERY_SURVIVES_NOT_EDGE
- DISCOVERY_FAIL_NO_PROMOTION
- SOURCE_DATA_INSUFFICIENT
- SOURCE_PROVENANCE_FAIL
- TECHNICAL_FAIL_CLOSED

If Discovery fails, exact ARQ-001-MTF-001 closes. Do not:
- change 4H/1H clocks;
- invert regime;
- alter z thresholds;
- alter beta window;
- alter outcome horizon;
- remove costs;
- subset favorable months;
- swap assets;
- open 2025.

If Discovery survives, this is still NOT a trading edge. Only then may a separate, already-frozen confirmation authority open 2025.

## Governance

No live trading.
No orders.
No exchange mutation.
No wallets.
No main merge.
No 2025/2026 access before authorized release.
