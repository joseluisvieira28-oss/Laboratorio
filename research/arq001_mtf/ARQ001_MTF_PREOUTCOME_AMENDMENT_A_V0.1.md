# ARQ-001-MTF-001 — PRE-OUTCOME IMPLEMENTATION AMENDMENT A V0.1

Date: 2026-09-23
State when frozen: regime source PASS; Binance 1H source census PASS; no ARQ-001-MTF scientific outcome, expectancy, PnL, coefficient or trade return has been computed.

This amendment resolves two implementation ambiguities in PREOUTCOME_AUTHORITY_V0.1. It does not change the economic hypothesis or any observed result.

## A. Causal z-score history

The parent phrase "previous 30 calendar days of corresponding event-clock observations for that exact UTC event slot" is incompatible with the separately frozen requirement of >=150 prior observations: one fixed UTC slot supplies only 30 observations in 30 days.

Frozen correction:

For each event T, BTC signal-return and residual-gap z-scores use **all valid 4H-boundary candidate observations from the immediately preceding 30 calendar days**, across the six UTC 4H boundaries (00/04/08/12/16/20).

- current event T excluded;
- maximum theoretical history = 180 candidate observations;
- require >=150 valid prior observations for each z-score;
- sample mean/std;
- std=0 => event ineligible;
- z clipping [-5,+5] unchanged.

No hour-of-day-specific normalization and no post-outcome alternative window is allowed.

## B. Primary next-hour outcome candle

For an event/entry boundary T:

- signal candle = Binance 1H candle with open_time T-1h;
- entry/target candle = Binance 1H candle with open_time T;
- primary gross outcome = signed log(close/open) of the candle whose open_time is T.

Thus "ALT_close[T+1h] / ALT_open[T]" in prose means the close timestamp of the T-opened 1H candle, not the next row with open_time T+1h.

No alternative entry delay or horizon may be introduced after outcomes.

## Invariants unchanged

- regime timeframe 4H;
- follower timeframe 1H;
- 30-day backward beta;
- btc |z| >= 0.75;
- residual |z| >= 1.0;
- five-ALT universe;
- A/B/C/D ablation;
- 10/12/14 bps costs;
- Discovery 2024;
- 2025 Confirmation locked;
- 2026 final holdout locked;
- all Discovery gates and bootstrap settings unchanged.
