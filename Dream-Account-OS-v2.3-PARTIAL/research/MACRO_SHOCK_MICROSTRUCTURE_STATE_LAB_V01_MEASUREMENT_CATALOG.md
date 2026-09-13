# Macro Shock Microstructure State Lab V0.1 — Measurement Catalog

Status: **PRE-DATA MEASUREMENT CATALOG / NO EDGE HYPOTHESIS**

## Authority boundary

This catalog is downstream of the frozen pre-data charter, the provenance gate PASS, and the schema/alignment specification. It defines only mechanical state descriptors that can be implemented and tested without accessing target outcomes.

It does **not** authorize a directional H02, target-outcome inspection, event-family selection, threshold tuning, live trading, exchange mutation, MEXC access, main merge, or Render deployment.

`H02_STATUS = NOT_AUTHORIZED`

## Design principle

A measurement may enter this catalog only if it can be defined without looking at whether BTC or ETH later went up or down. Any numeric window, threshold, depth band, venue priority, event subset, or trading interpretation must be separately frozen prospectively before target-data inspection.

## Candidate measurement primitives

### 1. Best-bid/ask state

Mechanical descriptors:

- `mid = (best_bid + best_ask) / 2`
- `spread = best_ask - best_bid`
- `spread_bps = spread / mid * 10000`
- top-of-book bid quantity
- top-of-book ask quantity
- top-of-book imbalance = `(bid_qty - ask_qty) / (bid_qty + ask_qty)` when denominator is positive

Interpretation boundary: these describe contemporaneous liquidity state only. A positive or negative imbalance is **not** a trading direction.

### 2. L2 depth state

Permitted generic primitives:

- cumulative bid depth over an explicitly caller-supplied level count or price-distance band;
- cumulative ask depth over the same frozen definition;
- normalized depth imbalance = `(bid_depth - ask_depth) / (bid_depth + ask_depth)` when denominator is positive;
- depletion/refill deltas between two already-defined book states.

No number of levels, basis-point band, or refresh horizon is frozen here. Those are research parameters and must be frozen before target-outcome access.

### 3. Trade intensity

For a caller-supplied interval that has been frozen before target-outcome inspection:

- trade count;
- base quantity traded;
- quote/notional quantity traded where source semantics support it;
- trades per unit time;
- notional per unit time.

No event window is selected here.

### 4. Signed-flow intensity

Permitted only where venue semantics unambiguously support aggressor/maker-side classification.

Generic primitives:

- aggressive buy notional;
- aggressive sell notional;
- signed notional = buy notional − sell notional;
- normalized signed flow = signed notional / total notional when total is positive.

No threshold, persistence rule, directional mapping, or continuation/reversal interpretation is authorized.

### 5. Realized-volatility state

Given an independently frozen sampling interval and observation window:

- log return between consecutive valid mid-price observations;
- sum of squared log returns;
- realized volatility derived mechanically from those returns.

This catalog deliberately freezes no interval length or scaling convention because choosing them after target inspection would create tuning risk.

### 6. Cross-venue price-state primitives

Using only deterministic backward as-of alignment from the schema spec:

- venue A mid;
- venue B latest eligible mid at or before anchor time;
- raw cross-venue mid difference;
- relative/basis difference = `(mid_A / mid_B) - 1` where both are valid;
- alignment skew in nanoseconds;
- missing-alignment flag.

No venue is declared the leader. No lag horizon is selected. No future observation may populate an earlier anchor.

### 7. Reconstruction-quality diagnostics

Permitted diagnostics:

- sequence continuity/monotonicity where source semantics exist;
- synchronized/unsynchronized book state;
- parse-failure count;
- stale/missing alignment count;
- duplicate/conflict count;
- source-message provenance hash coverage;
- exchange-time versus collector-time latency metadata when available.

These are quality controls, not edge features.

### 8. Read-only execution-condition proxies

Permitted descriptive proxies without placing orders:

- quoted spread in bps;
- top-of-book available quantity;
- cumulative depth under an independently frozen depth definition;
- hypothetical market-impact/slippage calculation for an explicitly caller-supplied notional, provided the notional is not selected from target outcomes;
- post-observation adverse-selection descriptors only under a separately frozen non-directional measurement contract.

No live/paper order placement is authorized by this catalog.

## Parameter governance

The following may **not** be chosen from target data:

- event family;
- symbol subset;
- venue priority;
- depth levels or price bands;
- time windows;
- sampling cadence;
- skew tolerance;
- imbalance thresholds;
- volatility thresholds;
- trade/flow thresholds;
- slippage notionals;
- continuation/reversal labels;
- entry/exit/stop/TP rules.

If a numeric choice becomes necessary, it must come from independent mechanism/literature/operational justification and be frozen before the relevant target data are inspected.

## What a PASS means

A PASS at this stage means the measurement layer is deterministic, auditable, provenance-preserving, and technically implementable. It does **not** mean predictive information exists and does not imply profitability.

## Next allowed review

Only an **independent pre-data measurement-design review** may follow. That review may decide whether there is sufficient non-outcome-based mechanism to justify a future prospective contract.

It may not inspect target outcomes and may not authorize H02 by itself.

Final boundary: **STOP BEFORE TARGET OUTCOMES OR H02 FREEZE.**
