# AMM-LVR-CROSSVENUE-001 — FORWARD ECONOMIC FREEZE V0.1

**Frozen:** 2026-09-23 before any internal forward opportunity-PnL outcomes  
**MVE ID:** AMM-LVR-CROSSVENUE-001-FWD-MVE1  
**Mode:** public/read-only shadow; no transaction submission

## Question

Does a small, non-integrated participant have repeatable CEX–DEX stale-price headroom after executable DEX quote, CEX hedge spread/fees, gas and conservative inclusion/latency costs?

## Frozen venue and pair tranches

DEX venue: Ethereum Uniswap V3 only.

For every pair, the execution route may mechanically choose the best executable quote across the standard V3 fee tiers **100 / 500 / 3000 / 10000** at that instant. The fee-tier choice is an execution rule, not a post-result selection.

### Tranche A — stable / major
- WETH ↔ USDC
- WETH ↔ USDT

Hedge:
- ETHUSDT Spot
- USDCUSDT Spot conversion when needed

### Tranche B — cross-asset / alt
- WBTC ↔ WETH
- LINK ↔ WETH
- PEPE ↔ WETH
- SHIB ↔ WETH

Hedge:
- BTCUSDT / LINKUSDT / PEPEUSDT / SHIBUSDT Spot plus ETHUSDT where a two-leg USDT hedge is required.

No pair may be added or removed after forward economic observations under this MVE.

## Frozen notional buckets

USD-equivalent DEX input notionals:
- 100
- 500
- 1,000
- 5,000

Every eligible snapshot is evaluated at every technically executable bucket. No best-size selection may be promoted after outcomes.

## CEX execution assumptions

Public Binance Spot executable BBO/depth only.

Base taker fee:
- **10 bps per CEX hedge leg**
- source frozen from Binance regular-user Spot fee schedule observed 2026-09-23
- no VIP, BNB discount or promotional fee may be assumed.

Stress taker fee:
- **20 bps per CEX hedge leg**

A one-leg hedge pays one fee layer; a two-leg hedge pays two.

The hedge price must consume observed executable depth for the frozen notional. Mid, last trade, candle close and nearest-neighbour substitutions are forbidden.

## DEX execution

Use a direct on-chain Quoter/eth_call against current Ethereum state.

The returned amount must incorporate actual pool fee and price impact for the notional. A spot/mid pool price is not an executable quote.

If no canonical pool/quote is available for the pair/fee tier at the exact snapshot, that route is unavailable; do not synthesize it.

## Gas / inclusion envelope

Until a funded transaction can be observed without mutation, use a pre-outcome conservative envelope:

BASE:
- gas units = 300,000
- gas price = latest base fee + p50 priority fee from recent eth_feeHistory

STRESS:
- gas units = 500,000
- gas price = latest base fee + p90 priority fee from recent eth_feeHistory

Direct builder / coinbase transfers are NOT assumed to be zero for a final accessibility verdict. A shadow result that cannot bind this layer may reach only **KNOWN_COST_SURVIVOR / ACCESSIBILITY_UNPROVEN**.

## Timing / latency

Market-data source: unauthenticated Binance Spot WebSocket market stream.

Chain source: public Ethereum RPC.

Every record stores:
- local UTC receipt timestamp
- monotonic arrival timestamp
- source block number and timestamp
- CEX event timestamp when supplied

No historical backfill can count as prospective evidence.

For the first MVE, CEX hedge simulation uses the first causally observable depth state after the DEX quote snapshot. Additional retrospective markout horizons are descriptive only and cannot replace this execution rule.

## Independent event definition

Repeated 1-second snapshots are not independent trades.

For each pair × direction × notional:
1. an event begins only when full known-cost margin crosses from <= 0 to > 0;
2. later positive snapshots belong to the same event;
3. event resets only after full known-cost margin is <= 0 continuously for 5 seconds.

This definition is frozen before outcomes.

## Cost states

1. GROSS_DISLOCATION — executable DEX vs CEX discrepancy before gas/CEX fees.
2. KNOWN_COST_SURVIVOR — positive after DEX executable quote, CEX executable hedge, frozen taker fees and gas envelope.
3. ACCESSIBILITY_UNPROVEN — known-cost survivor but competitive inclusion / direct builder payment remains unbound.
4. FULL_COST_SURVIVOR — allowed only after inclusion/builder cost and failure risk are defensibly bound.
5. NO_EDGE_EXACT — exact MVE fails under frozen adjudication.

## Sample gates

Engineering pilot:
- first 20 independent events, any tranche; source/implementation only; no promotion.

Discovery eligibility:
- >=100 independent events total;
- >=20 independent events in at least 3 frozen pairs;
- at least 14 distinct UTC calendar days.

Until those gates close, the only economic state is **INSUFFICIENT_FORWARD_SAMPLE** even if point estimates are positive.

## Discovery pass gates

All are mandatory:
- base full-cost mean > 0;
- stress full-cost mean > 0;
- bootstrap lower 95% CI of base mean > 0;
- positive-event rate > 50%;
- no single pair contributes >50% of total positive PnL;
- no single UTC day contributes >25% of total positive PnL;
- at least two notional buckets remain positive under stress;
- accessibility/inclusion layer is actually bound, not assumed away.

Failure of mandatory economics after a valid sample => exact MVE dies. No pair, size, fee tier, time-of-day, direction or cost rescue.

## Governance

This freeze authorizes research-only public observation. It does NOT authorize:
- wallet use
- signing or broadcasting Ethereum transactions
- CEX orders
- authenticated trading endpoints
- paid data
- main merge
- Tier 2 / quasi-diamond promotion from a pilot

External historical paper results are context/contamination only and supply zero promotion credit.
