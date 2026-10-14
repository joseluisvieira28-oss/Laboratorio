# MICROSTRUCTURE SCALPING LAB — MAKER-ASSISTED GATE V0.1 PRE-OUTCOME FREEZE

Date: 2026-09-25
Status: SOURCE/FILL-MODEL GATE — NO MAKER OUTCOMES

## Rationale
The frozen taker-only MVE showed weak raw directional information but economics far below taker fees.

Maker-assisted execution is a distinct execution hypothesis and was explicitly blocked until a defensible fill model exists.

## Source requirement
Historical public trades must be independently available and joinable to historical L2.

Bybit documents:
- orderbook matching-engine timestamp cts can be correlated with public-trade T;
- orderbook seq and public-trade seq are cross-sequence fields.

No trade/L2 join may be assumed until raw historical files are probed.

## Conservative passive-fill principles
A passive order is NOT filled because:
- the market merely touches the price;
- the best quote disappears from a snapshot;
- future price moves through the level without evidence of executed volume.

A fill may be credited only under a predeclared conservative rule supported by executed trades and queue/depth evidence.

## Initial model target
For an order posted at current best bid/ask:
- record displayed quantity ahead at the level at placement;
- accumulate executed aggressive volume at that exact price after placement;
- require executed volume to exceed a conservative queue-ahead estimate before crediting a fill;
- cancellations ahead MUST NOT automatically improve queue position unless separately justified;
- if event ordering between L2 and trades is ambiguous, fail closed.

## Required outputs before maker Discovery
1. historical trade archive SOURCE_FEASIBLE
2. timestamp/sequence join audit
3. fill-model unit tests
4. explicit queue-ahead convention
5. fee model
6. latency model
7. adverse-selection measurement protocol

Until all pass:
MAKER_DISCOVERY = BLOCKED
