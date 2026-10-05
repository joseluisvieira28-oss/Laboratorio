# CRYPTO-FORCED-FLOW-ATLAS-001 — V0.1
Date: 2026-10-05
Status: SOURCE/MECHANISM TRIAGE — NO MARKET OUTCOMES OPENED BY THIS ATLAS

## Mission
Answer one question:

> Where does mechanically compelled flow exist, is observable from public sources, and may leave a non-zero delay between cause and full price impact?

This atlas is mechanism-first. It does not promote correlations.

## Classification rules
A family is stronger when:
1. the actor is mechanically required to act, not merely incentivised;
2. the forcing event is public and timestampable before or while the flow occurs;
3. the forced direction or convergence target is inferable ex ante;
4. market data are public/free and sufficiently precise;
5. the impact window could realistically exceed data/decision/execution latency;
6. the universe can be built without selecting winners after outcomes;
7. sample size can support robust discovery and later holdout.

## Atlas V0.1

### A. CEX perpetual delisting / automatic settlement
Mechanics: HARD FORCED FLOW.
Public observability: HIGH.
Potential delay: HOURS TO DAYS.
Direction: not outright-price deterministic, but OI extinction and basis/spread convergence are mechanically motivated.
Source feasibility: HIGH.

Binance Futures publicly announces an exact settlement time, states that all positions will be closed and automatically settled, and restricts new risk shortly before settlement. Binance also publishes public futures market archives.

Priority: 1 — OPEN NEW SOURCE GATE.

Candidate family:
BINANCE-FUTURES-DELIST-FORCED-CONVERGENCE-001

### B. Public crypto-index rebalances
Mechanics: HARD for products mandated to track the benchmark; softer at the aggregate market level because not all index-linked exposure is physically replicated.
Public observability: HIGH.
Potential delay: DAYS.
Direction: additions/weight increases imply benchmark demand; deletions/weight decreases imply supply/hedge adjustment.
Source feasibility: HIGH.
Capacity uncertainty: material — linked product AUM/notional must be verified event-by-event or at index level.

Priority: 2 — SOURCE CENSUS AFTER A.

Candidate family:
CRYPTO-INDEX-REBALANCE-FORCED-FLOW-001

Initial public sources:
- Bitwise publishes rebalance notifications before implementation and uses rules-based monthly/quarterly schedules.
- CoinDesk 20 publishes reconstitution results and uses scheduled quarterly implementation.

### C. CEX liquidation cascades
Mechanics: HARD FORCED FLOW.
Public observability: HIGH FORWARD; historical completeness varies.
Potential delay: MILLISECONDS TO SECONDS/MINUTES.
Direction: liquidation side is explicit.
Source feasibility: already attacked elsewhere in the repository.

Existing family:
LIQUIDATION-FLOW-FWD-001

Existing authoritative state at 2026-10-05:
PARTIAL_SOURCE__ACTIVATION_BLOCKED.
Bybit public all-liquidation source emitted valid BTC events but no qualifying ETH event in the frozen one-hour window. Do not duplicate it in this atlas.

Priority: EXISTING / DO NOT DUPLICATE.

### D. Aave liquidation cliffs / borrower health-factor overhang
Mechanics: HARD once HF < 1 and liquidation is executed; pre-threshold liquidation is only conditional.
Public observability: structurally strong on-chain.
Potential delay: blocks/minutes around oracle threshold crossings.
Source feasibility: historically difficult but already deeply investigated.

Existing family:
AAVE-LIQUIDATION-OVERHANG-001

Existing repo work proves a large historical source census and substantial reconstruction work. Do not duplicate without a genuinely new source/mechanism.

Priority: EXISTING / DEFER.

### E. Options/futures expiry hedge unwind
Mechanics: contract settlement is hard; hedge unwind direction is NOT directly observable without assumptions about dealer positioning.
Public observability: medium-high.
Potential delay: minutes/hours.
Direction certainty: medium/low.

Existing related OPTIONS-VOL forward research means no duplicate attack from this atlas.

Priority: DEFER / REQUIRE NEW MECHANISM.

### F. Token unlocks / vesting
Mechanics: NOT FORCED SELLING. Tokens become transferable; recipients may hold.
Public observability: often high.
Potential delay: days.
Direction certainty: low.

Priority: REJECT AS 'FORCED FLOW' unless a specific contract/process forces market conversion.

### G. Ethereum validator exits / withdrawal queue
Mechanics: once a validator exit has been initiated, exit/withdrawal processing becomes protocol-constrained and eventual withdrawal is automatic; SELLING IS NOT FORCED.
Public observability: high on-chain.
Potential delay: hours/days/weeks.
Direction certainty for ETH price: low.

Priority: REJECT AS DIRECT FORCED-SELL SIGNAL; retain only for separate liquidity-supply research.

### H. ETF creations/redemptions
Mechanics: creation/redemption plumbing can compel AP/fund hedging or asset transfer, but publicly reported flow is often contemporaneous/lagged relative to execution.
Public observability as LEADING signal: mixed.
Potential delay: uncertain.
Direction certainty: medium.

Priority: DEFER until a pre-trade public trigger is proven.

### I. Funding payments / extreme funding
Mechanics: funding transfer is compulsory for positions held through timestamp; buy/sell is not compulsory.
Public observability: high.
Potential delay: known.
Direction certainty: low.

Priority: REJECT AS PURE FORCED-TRADE SIGNAL.

### J. Stablecoin depeg / AMM liquidity withdrawal
Mechanics: AMM inventory movement is mathematical; LP withdrawal/arbitrage is incentivised rather than compulsory.
Public observability: high on-chain.
Existing stablecoin stress research already exists.

Priority: EXISTING / DO NOT DUPLICATE.

## V0.1 answer
The cleanest not-already-exhausted public forced-flow mine in this atlas is:

BINANCE-FUTURES-DELIST-FORCED-CONVERGENCE-001

Why:
- exact public announcement;
- exact future settlement deadline;
- compulsory closure/automatic settlement of residual positions;
- new-risk restriction before settlement;
- public historical futures archives;
- plausible non-HFT horizon;
- mechanism naturally points to OI extinction and basis/spread convergence rather than an arbitrary directional candle pattern.

Second new mine:
CRYPTO-INDEX-REBALANCE-FORCED-FLOW-001

## Governance
Research-only.
No main merge.
No live trading.
No orders.
No wallets.
No account reads.
No private/authenticated exchange endpoints.
No post-outcome threshold tuning.
No market outcomes opened merely to rank this atlas.
