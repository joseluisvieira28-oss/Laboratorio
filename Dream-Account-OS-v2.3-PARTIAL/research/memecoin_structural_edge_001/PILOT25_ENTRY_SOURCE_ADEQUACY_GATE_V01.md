# MSEL-001 — PILOT25 ENTRY SOURCE ADEQUACY GATE V0.1

Status: RESEARCH-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Trigger

The frozen V12 entry rule requires a fresh Pump economic BUY execution in the final 60 seconds before T+5 with quote notional >= 0.01 SOL. V13B bound the exact pre-outcome inputs and reported only 2/25 mints with at least one such eligible entry execution.

No future raw transaction was decoded by V13B. No return, label, slice statistic, or verdict was computed.

## Scientific consequence

V14 MUST NOT run under the exact V12 entry rule as if the 25-launch pilot were evaluable. Two evaluable mints cannot support the frozen 5/13/5 safest/risk slices or the full-universe catastrophic-risk comparisons.

This is not NO_EDGE. The correct state is:

`INSUFFICIENT_ENTRY_COVERAGE_PRE_OUTCOME`

## Frozen adequacy requirement

Before any future-outcome decode, the entry authority used for Pilot25 evaluation must produce a mechanically defined, point-in-time, executable entry reference for all 25 frozen launches, or the Pilot25 outcome evaluation remains blocked.

Missing entry coverage must not be repaired by outcome-aware selection, lowering thresholds after outcomes, cherry-picking active tokens, or silently excluding launches.

## Authorized next action

Run a local-only entry-source coverage audit using only already captured <=T+5 Pump TradeEvent evidence and the V13B binding. The audit may measure source availability and reserve-state reconstructability, but it may not decode any V13 future transaction or compute any outcome.

A possible later protocol amendment may use a deterministic T+5 executable bonding-curve quote derived from historically verified reserve state, but only if the source audit shows that state is reconstructible without future data. Such an amendment must be frozen explicitly before V14 and must not be chosen by looking at outcomes.

## Explicit prohibitions

- Do not run V14 yet.
- Do not decode the 904 V13 future transactions.
- Do not calculate returns or labels.
- Do not widen the 60-second window merely to improve coverage.
- Do not lower 0.01 SOL merely to improve coverage.
- Do not exclude the 23 currently uncovered launches.
- Do not call this a failed edge hypothesis.
