# MSEL-001 — KILLER FILTER GATE FREEZE V0.1

Status: PRE-OUTCOME / QUANTITATIVE GATE FROZEN
Branch: `memecoin-structural-edge-v0.1`
Date: 2026-09-15

## 1. Purpose

Freeze objective criteria before any MSEL-001 future outcomes are opened. This prevents moving the goalposts after seeing results.

This gate evaluates whether T+5m structural information is useful enough to justify further research. It does NOT certify a trading strategy or diamond.

## 2. Primary evaluation population

All qualifying launches in each temporal OOS block, without conditioning on later graduation, survival, volume or listing.

Primary decision timestamp: T+5m.

Primary catastrophic outcome: mechanically defined -80% executable mark-to-market/adverse outcome within the frozen future window once the execution/outcome schema is finalized. The label definition may be clarified only before outcomes are computed and must then be hashed/frozen.

## 3. Ranking evaluation — avoids cutoff tuning

Every approved model outputs a risk score using T+5m data only.

Evaluate fixed population slices:
- safest 20%
- safest 50%
- riskiest 20%

The slice sizes are fixed now and may not be changed after outcomes.

## 4. Primary SURVIVES criteria

MSEL-001 Killer Filter earns `SURVIVES_MVE` only if ALL are true in temporal OOS:

1. **Catastrophic-risk reduction**
   - catastrophic-outcome incidence in the safest 20% is <= 60% of the full-universe incidence (>=40% relative reduction).

2. **Broader useful separation**
   - catastrophic-outcome incidence in the safest 50% is <= 80% of full-universe incidence (>=20% relative reduction).

3. **Risk concentration**
   - riskiest 20% catastrophic incidence is >= 1.5x full-universe incidence.

4. **Winner retention**
   - safest 50% retains >= 50% of all +100% future winners in the same OOS population.
   - this condition prevents a trivial filter that simply removes nearly all volatile launches, including winners.

5. **Structural incremental value**
   - structural model must improve catastrophic-risk reduction by at least 15 percentage points relative to the price/volume-only control at the same safest-20% coverage OR deliver materially better winner retention at equal risk reduction.

6. **Temporal stability**
   - direction of risk reduction must hold in at least 3 chronological OOS blocks;
   - no single block may contribute >50% of total avoided catastrophic cases.

7. **Leakage/source integrity**
   - zero known future-derived wallet clustering/reputation leakage;
   - source/reconstruction gate remains PASS.

## 5. Strong-survival flag

`STRONG_SURVIVES_MVE` if, in addition to all SURVIVES criteria:
- safest-20% catastrophic incidence <= 40% of baseline (>=60% relative reduction), and
- safest-50% retains >= 60% of +100% winners, and
- result remains directionally stable after conservative execution-cost sensitivity.

This flag is still NOT a diamond and does not authorize live trading.

## 6. FAIL / NO_EDGE criteria

Classify `NO_EDGE_MVE` if any of the following occurs after a valid data gate:
- safest-20% catastrophic incidence > 85% of full-universe incidence (<15% relative reduction);
- structural model does not materially beat price/volume-only control;
- effect reverses sign in multiple chronological OOS blocks;
- apparent effect disappears after point-in-time wallet/creator leakage controls;
- result is driven by one source bug, one narrow regime or one duplicated actor cluster;
- winner retention collapses below 30% in the safest 50% while risk reduction remains modest;
- realistic costs/latency show no plausible route from classification value to economic value.

## 7. Intermediate result

If the result lies between FAIL and SURVIVES, classify `WEAK_SIGNAL_MVE`.

`WEAK_SIGNAL_MVE` does NOT authorize post-outcome threshold tuning. One pre-registered replication in a separate regime may be allowed; otherwise close the mechanism.

## 8. Statistical reporting

Report at minimum:
- counts and base rates;
- risk ratios and absolute risk differences;
- bootstrap or binomial confidence intervals appropriate to the metric;
- temporal-block results separately;
- calibration / ranking diagnostics;
- winner-retention tradeoff;
- price/volume-control comparison.

AUC alone cannot pass the gate.

## 9. Next-stage authorization

Only `SURVIVES_MVE` or `STRONG_SURVIVES_MVE` can unlock:
- richer ML rankers;
- Survivor Ranker experiments;
- executable trading-model design.

No live trading, no exchange mutation, no merge to main.
