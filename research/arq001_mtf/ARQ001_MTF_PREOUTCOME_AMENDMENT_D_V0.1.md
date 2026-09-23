# ARQ-001-MTF-001 — PRE-OUTCOME IMPLEMENTATION AMENDMENT D V0.1

Date: 2026-09-23
State when frozen: source gates PASS; no Discovery trade return, expectancy, PnL, bootstrap result or robustness outcome has been computed.

## Best-1% robustness

For N D-confirmed observations:
- remove exactly max(1, ceil(0.01 * N)) observations with the highest BASE12 net return;
- ties at the cutoff are ordered deterministically by (net return descending, event timestamp ascending, ALT symbol ascending);
- recompute the pooled arithmetic mean on the remaining observations;
- gate requires mean > 0.

No alternative percentile convention is allowed after outcomes.

## Best-ALT removal robustness

For each ALT, compute its D-confirmed BASE12 arithmetic mean.

The "best ALT" is the ALT with the highest mean.
- ties are broken lexicographically by symbol;
- remove all D-confirmed observations for exactly that ALT;
- recompute pooled BASE12 arithmetic mean on the remaining four ALTs;
- gate requires mean > 0.

## D-confirmed minus D-rejected

The primary incremental delta is:
mean(BASE12 net return of all D-confirmed baseline-A observations)
minus
mean(BASE12 net return of all D-rejected baseline-A observations).

If either set is empty, this gate fails closed.

## Arithmetic mean

Every expectancy/mean gate in this Discovery uses the unweighted arithmetic mean across the stated ALT-event observations. No per-ALT equal weighting or post-outcome weighting is permitted.

No other scientific rule changes.
