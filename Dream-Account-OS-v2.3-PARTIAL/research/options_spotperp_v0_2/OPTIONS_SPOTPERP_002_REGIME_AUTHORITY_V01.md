# OPTIONS-SPOTPERP-002 — Regime Child Experiment Authority V0.1

Status: FROZEN BEFORE EXECUTION
Parent: OPTIONS-SPOTPERP-001 V0.1
Branch: options-spotperp-regime-v0.2
Purpose: test whether the parent near-edge is economically useful only in pre-defined observable BTC regimes.

## Governance
- Research-only; fail-closed.
- Parent result remains DISCOVERY_FAIL_NO_PROMOTION and is never rewritten.
- This is a new child experiment, not a rescue/reclassification of the parent.
- No live trading, no exchange mutation, no deployment, no merge to main.
- No parameter tuning after observing this child experiment's outcomes.
- 2025 remains LOCKED during child Discovery.
- 2026 remains LOCKED throughout.
- Canonical immutable source chain must bind to monthly raw run 34778911131 and final Source/Data Gate run 34811277716, or execution blocks.

## Frozen discovery window
2021-04-01 through 2024-12-31 only.

## Parent signal — unchanged
Reuse OPTIONS-SPOTPERP-001 V0.1 exactly:
- BTC Deribit trade-implied call-minus-put IV skew.
- DTE 30..120 calendar days.
- Calls strike/index 1.05..1.20.
- Puts strike/index 0.80..0.95.
- Minimum 5 distinct eligible call instruments and 5 distinct eligible put instruments per day.
- Daily skew = median(call instrument median IV) - median(put instrument median IV).
- Position sign = sign(skew).
- Outcome = next-day BTC open-to-following-day open log return, aligned to signal sign.
- Base cost = 10 bps per entered trade.
- Stress diagnostic = 20 bps.
- HAC regression lags = 7.

## Frozen regime variables
Regime state is determined only from BTC daily opens known on or before the signal date.

1. TREND_30D
- UP if ln(Open_t / Open_t-30) > 0.
- DOWN otherwise.

2. REALIZED_VOL_30D
- Daily log returns from BTC opens.
- Sample standard deviation of the most recent 30 daily open-to-open log returns, annualized by sqrt(365).
- HIGH if annualized realized volatility >= 0.80 (80%).
- LOW otherwise.

No year label, future outcome, future BTC price, options outcome, or post-signal information may enter regime assignment.

Four frozen regimes:
- UP_HIGH
- UP_LOW
- DOWN_HIGH
- DOWN_LOW

Signal days without the required 30-day BTC history are unevaluable for V0.2.

## Discovery statistics per regime
For each frozen regime compute:
- evaluable entered trades n;
- HAC(7) beta and one-sided p-value for skew -> forward BTC return;
- net mean bps/trade at 10 bps cost;
- profit factor at 10 bps;
- net mean bps/trade at 20 bps stress (diagnostic only);
- calendar-year counts and 10 bps net means;
- maximum single-year share of positive gross PnL.

## Flexible child classification gates
A regime is DISCOVERY_ELIGIBLE when all hold:
A. n >= 120.
B. beta > 0 and one-sided HAC p <= 0.10.
C. 10 bps net mean > 0.
D. 10 bps profit factor > 1.0.
E. At least 2 distinct calendar years each have >= 25 entered trades in that regime and nonnegative 10 bps net mean.
F. No single calendar year contributes > 70% of total positive gross PnL.
G. Provenance/leakage/firewall checks all pass.

Child classification:
- CANDIDATE_NEAR_EDGE: at least one frozen regime passes A..G.
- CONTEXT_DEPENDENT: no regime passes all A..G, but at least one regime passes A,B,C,D,G.
- DISCOVERY_FAIL_NO_CANDIDATE: otherwise.

These child classifications are deliberately more permissive than parent promotion. They do not authorize live trading and do not retroactively promote OPTIONS-SPOTPERP-001.

## Deterministic candidate selection if >1 regime passes
Choose exactly one candidate for any later holdout, using this frozen lexicographic ranking:
1. greater number of qualifying nonnegative years under Gate E;
2. higher 10 bps net mean bps/trade;
3. lower one-sided HAC p-value;
4. larger n;
5. alphabetical regime label as final tie-breaker.

No manual selection is permitted.

## Holdout rule
2025 may only be opened by a separate explicitly-authorized holdout workflow if Discovery classification is CANDIDATE_NEAR_EDGE. The selected regime and all thresholds above must remain frozen. 2026 stays locked.

## Interpretation rule
A child CANDIDATE_NEAR_EDGE means 'worth a protected holdout test', not 'validated edge'. A CONTEXT_DEPENDENT result remains scientifically useful and may justify future hypothesis generation, but not a 2025 holdout under this authority.
