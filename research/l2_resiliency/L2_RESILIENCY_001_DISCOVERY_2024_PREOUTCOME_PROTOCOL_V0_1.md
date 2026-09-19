# L2-RESILIENCY-001 — DISCOVERY 2024 PRE-OUTCOME PROTOCOL V0.1

Status: FROZEN BEFORE REPLENISHMENT / MIDPOINT OUTCOME ACCESS

## Scope
- Source: official Hyperliquid BTC l2Book 2024 corpus already source/schema/timing validated.
- 2025 remains LOCKED. 2026 FORBIDDEN.
- Information-transmission Discovery only. No PnL, Sharpe, leverage, execution or live-trading claim.

## Event
Use the already-frozen normalized sweep rule and reproduce exactly the canonical event counts:
- ASK consumed: post best ask > pre best ask, prior best ask absent post-snapshot, bid not simultaneously adverse.
- BID consumed: post best bid < pre best bid, prior best bid absent post-snapshot, ask not simultaneously adverse.
- both sides adverse = AMBIGUOUS_BOTH_SIDES, excluded.
- stale late payloads cannot form transitions.
- continuity resets at missing-hour segment boundaries.

## Consumed-side direction
- ASK consumed => direction +1.
- BID consumed => direction -1.

## Pre-sweep depth
For each valid sweep, PRE_DEPTH5 is the sum of displayed sizes at the first five levels on the consumed side in the immediately preceding accepted normalized snapshot.
If PRE_DEPTH5 <= 0, the event is classified ZERO_PRE_DEPTH_UNDEFINED and excluded from all scientific cells. It may not be repaired or substituted.

## Replenishment ratio
For replenishment horizon R in {1s, 5s, 15s}:
RR_R = HORIZON_DEPTH5_R / PRE_DEPTH5
where HORIZON_DEPTH5_R is the sum of displayed sizes of the first five levels on the same consumed side at the canonical R-horizon sampled state.
No price-level matching, interpolation, alternate depth count or reconstructed level is allowed.

## Weak / strong — fixed semantic threshold
- WEAK replenishment: RR_R < 1.0 (less displayed top-5 depth than immediately pre-sweep).
- STRONG replenishment: RR_R >= 1.0 (fully restored or over-restored top-5 depth).
The 1.0 threshold is semantic, not fitted: it is exact restoration of pre-sweep top-5 displayed depth.

## Causal primary cells
Only replenishment measurements strictly earlier than their midpoint outcome horizon are eligible:
- R1 -> Y5
- R1 -> Y15
- R1 -> Y60
- R5 -> Y15
- R5 -> Y60
- R15 -> Y60
No R>=Y cell is analyzed, preventing contemporaneous/look-ahead interpretation.

## Midpoint response
For each causal cell (R,Y), use the midpoint of the canonical sampled R state as the response baseline and the midpoint of the canonical sampled Y state as the endpoint.
DIRECTIONAL_RESPONSE_BPS = direction * 10,000 * (MID_Y / MID_R - 1).
Positive = continuation in sweep direction after the replenishment observation.
Negative = reversal after the replenishment observation.

## Timing eligibility
Every R and Y state must independently satisfy the frozen horizon rule:
- first accepted normalized state at or after anchor+horizon;
- lateness <= 1,100 ms;
- no interpolation;
- no cross-segment lookup.
If either required state is unavailable, that event is MISSING_SOURCE_TIMING for that cell and excluded only from that cell.

## Primary comparison
For each of the six cells compare WEAK versus STRONG directional response.
Daily group means are computed by UTC calendar date of the sweep anchor.
For each eligible day/cell:
DAILY_CONTRAST = mean(response_bps | WEAK) - mean(response_bps | STRONG).
Days missing either group are not used for that cell's daily contrast.

## Dependence control
Event-level observations are not treated as independent because sweeps overlap heavily.
Inference is performed on UTC-day clusters.
For each cell: point estimate = unweighted mean of DAILY_CONTRAST across eligible days.
95% percentile confidence interval = 10,000 bootstrap resamples of eligible UTC days with replacement, deterministic seed 20260919.

## Global primary statistic
For each UTC day, compute GLOBAL_DAILY_CONTRAST as the unweighted mean of all available cell DAILY_CONTRAST values among the six causal cells.
GLOBAL_EFFECT = unweighted mean of GLOBAL_DAILY_CONTRAST across eligible days.
Global 95% percentile CI uses 10,000 UTC-day bootstrap resamples with replacement, seed 20260919.

## Prospectively frozen Discovery verdict
DISCOVERY_MECHANISM_SUPPORTED only if ALL are true:
1. GLOBAL_EFFECT > 0;
2. global bootstrap 95% CI lower bound > 0;
3. at least 4 of 6 cell point estimates are > 0;
4. each replenishment horizon R={1s,5s,15s} has at least one positive causal-cell point estimate.

If the global CI includes or falls below zero, or sign-consistency gates fail: DISCOVERY_FAIL_NO_SUPPORT.
No threshold, horizon, side, segment, date, cost, filter or subgroup rescue is permitted after outcome access.

## Secondary descriptive outputs
For each cell report valid N, weak N, strong N, timing-missing N, zero-pre-depth N, weak mean response, strong mean response, daily contrast estimate and bootstrap CI.
Also report results by sweep side as descriptive diagnostics only; side diagnostics cannot rescue a failed primary verdict.

## Hard firewalls
- No 2025/2026.
- No PnL, trading costs, execution simulation, Sharpe, leverage or position sizing.
- No tuning after outcomes.
- No main merge, deployment, alerts, webhooks or exchange mutation.
