# L2-RESILIENCY-001 — SWEEP EVENT OPERATIONAL CLARIFICATION V0.1

Status: FROZEN PRE-OUTCOME / EVENT-CONSTRUCTION ONLY

## Purpose
The original authority defines a sweep as a transition where the best price on one side moves by at least one tick while displayed quantity at the prior best falls materially. The word materially had no numeric definition.

## Materiality rule
For V0.1, materially is operationalized as COMPLETE DEPLETION of the prior best displayed level in the next eligible normalized snapshot: post-snapshot displayed quantity at the exact prior-best price = 0.

This is not a fitted threshold. It is the non-tunable mechanical interpretation of a best-price worsening in a discrete order book: if any displayed quantity remained at the prior best price, that price would still be the best on that side.

## Price-move rule
- ASK-SIDE CONSUMPTION candidate: post best ask > pre best ask.
- BID-SIDE CONSUMPTION candidate: post best bid < pre best bid.
- Strict inequality is sufficient for 'at least one tick' because official L2 price levels are discrete; no synthetic tick-size parameter is introduced.

## Ambiguity rule
- Exactly one consumed-side adverse best-price move must occur.
- If both best ask worsens and best bid worsens in the same consecutive normalized transition, classify AMBIGUOUS_BOTH_SIDES and do not create a sweep event.
- Improvements on the opposite side do not invalidate the single consumed-side event.

## State/clock rule
- Use only normalized accepted book states in top-level envelope arrival order.
- STALE_LATE_PAYLOAD records remain preserved but may not create transitions.
- Continuity resets at every missing-hour segment boundary.
- Event availability/anchor time is the post-transition top-level envelope time.

## Preflight authorization
Allowed before Discovery: count candidate sweep events, count ambiguous transitions, measure source cadence and record event anchors/side labels.
Still forbidden: replenishment ratios, weak/strong labels, midpoint response, forward direction, returns, PnL, protected-period access, tuning or rescue.

## Horizon sampling remains separate
The frozen scientific horizons remain replenishment +1s/+5s/+15s and midpoint +5s/+15s/+60s. This clarification does not choose a lateness/interpolation tolerance for horizon sampling. That source-timing rule must be frozen separately before outcome construction.
