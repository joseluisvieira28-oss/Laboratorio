# ATTACK ORDER V0.1

Frozen: 2026-09-24
No outcomes inspected for IPG-001.

## Tier A — attack now

### A1. CORE INFORMATION PROPAGATION GRAPH
Status: highest priority.
Why: source feasibility is strongest and existing prior art does not answer the conditional multi-surface state-transition question.

Inputs:
- Deribit options IV/greeks/DVOL/trades.
- Binance perp mark/basis/funding/OI/trades.
- Binance spot trades/book.

First output:
- event-time corpus;
- source/receive clock audit;
- asynchronous event-study graph;
- matched-null results.

### A2. OPENMARKET NEGATIVE-CONTROL / METHOD VALIDATION
Status: use public frozen corpus; do NOT treat as a new predictive mine.
Purpose:
- validate our timestamp/jitter methodology against a known synchronized dataset;
- reproduce at least one published timing result before trusting our graph code;
- verify that the lab can return NO_EDGE on a dataset whose published OOS forecasting result is null.

Pin:
- source tag v0.5.2
- dataset v0.4.3-unified
- exact dataset revision hash required before execution.

## Tier B — source gate immediately after A

### B1. LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001
Question:
How much debt/collateral crosses liquidation eligibility for each incremental oracle move, and does that convexity interact with CEX crowding/book depletion before forced flow appears?

Gate needs:
- complete or bounded position census;
- oracle source/time mapping;
- protocol parameter history;
- no present-state substitution for historical positions.

### B2. CROSSCHAIN-LIQUIDITY-MIGRATION-001
Question:
Do directional stablecoin migrations across chains precede measurable destination-chain liquidity/OI/volume changes after controlling for issuance and general market state?

Start with:
- USDC CCTP burn/mint/message events.
- destination-chain DEX liquidity/volume where public historical data is reproducible.

## Tier C — forward-only

### C1. MEMPOOL-STATE-PROPAGATION-001
Question:
Do classified pending swaps/repays/borrows/liquidations/bridge operations create measurable downstream CEX/DEX state transitions before inclusion?

Constraints:
- node-specific mempool visibility;
- private order flow invisible;
- historical canonical mempool unavailable;
- absence of observation != absence of transaction.

### C2. ORACLE-SEQUENCER-STRESS-001
Question:
Do oracle staleness, CEX-oracle divergence or L2 sequencer state changes create short-lived propagation regimes?

## Stop conditions

- Source provenance cannot prove what was observable at event time.
- Sample count below frozen minimum.
- Clock/jitter sensitivity reverses edge direction.
- Edge vanishes after controlling for contemporaneous target move.
- Result exists only after feature/threshold rescue.
