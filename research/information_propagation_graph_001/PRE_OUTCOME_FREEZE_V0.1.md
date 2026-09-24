# PRE-OUTCOME FREEZE V0.1

Frozen: 2026-09-24
Lab: INFORMATION-PROPAGATION-GRAPH-001

## Minimal viable experiment

Target asset: BTC
Decision horizon: 1 second to 15 minutes
No live execution.

### Nodes

A. OPTIONS_STATE
- Deribit front-end ATM IV change
- 25-delta risk-reversal / skew change when derivable without interpolation leakage
- DVOL change
- option trade signed-flow proxy where source semantics permit

B. PERP_STATE
- Binance perp mark/index change
- funding / predicted funding change when supplied
- basis change
- open-interest change
- aggressive trade imbalance

C. SPOT_STATE
- Binance spot return
- aggressive trade imbalance
- top-of-book spread
- depth depletion / replenishment where reconstruction is reliable

### Event clock

For every message/event retain:
- source_event_ts_ms
- recv_monotonic_ns
- recv_wall_ts_ms
- source_sequence or update id if available
- source
- venue
- instrument
- event_type
- raw payload hash

Derived features may be aligned only after clock-quality flags are computed.

### Episode trigger

Do NOT trigger on target-price return.

An episode begins when any upstream node crosses a threshold defined only from its own trailing historical distribution:
- absolute robust z-score >= 3.0 using data strictly before event time;
- or source-native discrete state change (instrument lifecycle, funding rule change, etc.).

Threshold 3.0 is frozen for the first Discovery pass. It may be rejected later, but not rescued after outcome inspection.

### Primary tests

For each upstream trigger:
1. latency to first statistically abnormal PERP_STATE response;
2. latency to first statistically abnormal SPOT_STATE response;
3. BTC forward return at 1s, 5s, 15s, 30s, 1m, 5m, 15m;
4. signed continuation vs reversal;
5. conditional results by pre-event volatility/crowding state;
6. permutation/null test obtained by timestamp-shifting upstream events inside matched regime blocks.

### Propagation graph rule

An edge X -> Y is only eligible if:
- X event timestamp precedes Y response after jitter allowance;
- the relationship survives matched-regime null testing;
- it is not explained solely by simultaneous BTC price movement;
- it reproduces out of sample;
- sample count and missingness pass pre-declared minimums.

### Minimums for Discovery eligibility

- >= 200 independent episodes for a generic edge.
- >= 50 episodes for a rare discrete-event edge, which cannot be promoted beyond exploratory without additional forward evidence.
- >= 95% timestamp completeness for the fields used in an edge.
- zero unresolved sequence gaps inside the measurement window for order-book-derived features.

### Anti-overfit constraints

- No ML in V0.1.
- No feature search across arbitrary transformations.
- No target-driven feature selection.
- No post-outcome threshold changes.
- One primary graph and one matched null framework.
- Child mines (mempool, Aave, CCTP, Polymarket, oracle) remain separate until each passes its own source gate.

## Possible verdicts

SOURCE_BLOCKED
NO_EDGE
SURVIVES_DISCOVERY
BLOCKED_PENDING_OOS

Nothing else is permitted at this stage.
