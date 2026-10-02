# OPTIONS-ETH-SKEW-SHOCK-001 — PRE-OUTCOME FREEZE V0.1

Date: 2026-10-02
Status: FROZEN_PRE_OUTCOME
Branch: `options-eth-skew-shock-v01-2026-10-02`

## Scientific context

The exact BTC V2.1 level-skew transfer to ETH was rejected in 2024 Development because its positive gross PnL was too concentrated in one quarter.

That 2024 result is known and therefore calendar 2024 is NOT treated as independent confirmation for this new hypothesis.

This new candidate tests a different mechanism:

> Directional information may lie in the *change* in ETH call-vs-put implied-volatility skew, rather than in the absolute skew level.

No 2021-2023 ETH skew-shock outcome has been inspected before this freeze.
Calendar 2025 remains fully protected.

## Candidate identity

Candidate ID: `OPTIONS-ETH-SKEW-SHOCK-001-V0.1`

Underlying: ETH

Options source:
- Deribit historical public option trades
- currency = ETH
- kind = option
- accepted instrument prefix = `ETH-`

Outcome source:
- Binance Spot public monthly klines
- symbol = `ETHUSDT`
- 1d interval

## Frozen daily skew

For each UTC calendar date t:

- DTE: 30 to 120 calendar days inclusive
- Calls: strike / index_price in [1.05, 1.20]
- Puts: strike / index_price in [0.80, 0.95]
- Reject any row with missing, non-finite or non-positive IV or index_price
- Require >= 5 distinct eligible call instruments
- Require >= 5 distinct eligible put instruments
- Per instrument/day IV = median transaction IV
- Call-side IV = median eligible call-instrument daily IV
- Put-side IV = median eligible put-instrument daily IV
- `skew_t = call_side_iv_t - put_side_iv_t`

## Frozen skew-shock signal

A signal exists only when both calendar dates t and t-1 have a valid daily skew.

`shock_t = skew_t - skew_(t-1 calendar day)`

Direction:
- shock_t > 0 => LONG ETH
- shock_t < 0 => SHORT ETH
- shock_t = 0 => FLAT

No threshold.
No z-score.
No magnitude scaling.
No percentile filter.
No direction reversal.
No subgroup filtering.
No DTE/moneyness retuning.
No weekday/month/quarter filter.
No post-outcome rescue.

## Frozen outcome

For signal date t:
- entry = ETHUSDT spot open at 00:00 UTC on t+1
- exit = ETHUSDT spot open at 00:00 UTC on t+2
- forward return = log(exit / entry)
- aligned gross return = position * forward return

The scientific outcome is spot-based to avoid mixing the hypothesis test with MEXC execution mechanics.

## Frozen causal risk scaling

Risk-history start: 2020-01-01 UTC.

- ETHUSDT close-to-close daily log returns
- RV window = 20 valid daily returns
- expanding baseline = median of all valid RV20 values available through signal date t
- minimum valid RV20 history = 60
- weight = min(1.0, expanding_median_RV20_t / RV20_t)
- max weight = 1.0
- no leverage >1x in science
- no additional filters or floors

## Costs

BASE = 10 bps at full notional, linearly scaled by weight.
STRESS = 20 bps at full notional, linearly scaled by weight.

STRESS20 is diagnostic only, not an automatic veto.

## Evaluation windows

### Stage A — unseen historical back-validation

Signal dates: 2021-01-01 through 2023-12-31.

This window was not used to formulate the skew-shock hypothesis.

2024 is excluded from promotion adjudication because the prior ETH level-skew result from 2024 was already inspected before this new hypothesis was frozen.

A signal is evaluable only if t-1 skew and t+1/t+2 prices remain inside the Stage-A source/outcome boundary available to the runner.

### Stage A hard gates

All must pass:

A. Provenance/source/leakage gate PASS.
B. Entered scaled trades N >= 300.
C. Average executed notional >= 0.40.
D. BASE10 net mean > 0 bps/opportunity.
E. BASE10 profit factor > 1.00.
F. BASE10 cumulative net return > 0.
G. At least 2 of 3 calendar years have non-negative BASE10 mean.
H. No single calendar year contributes >60% of total positive gross PnL.
I. Exact frozen signal/direction/horizon/cost/risk-scaling identity unchanged.

Decision:
- all A-I pass => `BACKVALIDATION_SURVIVES__2025_OOS_UNLOCKED`
- source/provenance failure => `BACKVALIDATION_BLOCKED_SOURCE_PROVENANCE`
- otherwise => `BACKVALIDATION_REJECTED__2025_REMAINS_LOCKED`

Max drawdown < -50% is a mandatory `HIGH_RISK_FRAGILITY` flag but does not rewrite the frozen decision table.

### Stage B — one-shot calendar-2025 OOS

Calendar 2025 remains LOCKED unless Stage A passes all gates.

If unlocked:
- exactly one OOS attempt
- signal dates = calendar 2025 only
- no 2026 source or outcome may be used
- signals requiring 2026 to resolve t+2 remain unresolved

OOS hard gates:

A. Provenance/source/leakage gate PASS.
B. Resolved entered scaled trades N >= 50.
C. Average executed notional >= 0.40.
D. BASE10 net mean > 0 bps/opportunity.
E. BASE10 profit factor > 1.00.
F. BASE10 cumulative net return > 0.
G. At least 2 of 4 calendar quarters have non-negative BASE10 mean.
H. No single calendar quarter contributes >60% of total positive gross PnL.
I. Exact identity unchanged.

Decision:
- all A-I pass => `SKEW_SHOCK_SURVIVES_2025_OOS__FORWARD_ELIGIBLE`
- N < 50 => `INSUFFICIENT_OOS_SAMPLE`
- source/provenance failure => `OOS_BLOCKED_SOURCE_PROVENANCE`
- otherwise => `OOS_REJECTED_SKEW_SHOCK`

## Governance

Research-only.
No live trading.
No orders.
No exchange mutation.
No wallets.
No main merge.
No 2026 access.
No post-outcome tuning.
No gate lowering.
No 2024 promotion claim for this new hypothesis.
No automatic live authority even if 2025 survives.
