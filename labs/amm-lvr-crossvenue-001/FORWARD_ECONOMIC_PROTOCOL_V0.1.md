# AMM-LVR-CROSSVENUE-001 — FORWARD ECONOMIC PROTOCOL V0.1

**Freeze timestamp:** 2026-09-23  
**Mode:** prospective shadow research only  
**Live capital:** prohibited  
**Purpose:** test whether a small non-integrated participant can retain positive post-cost economics in observable CEX-DEX stale-price events.

## Evidence boundary

Historical free full-cost reconstruction is SOURCE_BLOCKED because the complete Dune export requires API authentication and the Binance public historical bookTicker route is not continuous through the published study period. Historical published aggregates remain context only.

The prospective route passed observability on 2026-09-23:
- public Ethereum RPC observed consecutive blocks;
- public Binance Spot BBO was observable without authentication;
- no wallet, order or authenticated CEX endpoint was used.

All evidence used for economic adjudication must be generated after this freeze.

## Frozen venues

DEX scope for V0.1:
- Ethereum mainnet Uniswap V2/V3 swaps involving a token with a directly observable Binance Spot USDT hedge.
- No other DEX may be added after outcomes are observed under this LAB_ID.

CEX hedge:
- Binance Spot public order book.
- Shadow execution only.

## Frozen notional buckets

Evaluate exactly:
- 500 USDT
- 1,000 USDT
- 5,000 USDT

A bucket may be marked INFEASIBLE when observable depth cannot support it. Do not replace it with a better-looking notional after outcomes.

## Frozen timing / latency stresses

For each eligible DEX event, reconstruct the CEX hedge using the first valid order-book state at or after:
- T0 / immediate observable hedge
- T0 + 250 ms
- T0 + 1,000 ms
- T0 + 3,000 ms

If infrastructure cannot timestamp at the required resolution, classify that latency bucket DATA_INSUFFICIENT; do not interpolate a favorable price.

## Frozen cost stack

Net economic result must deduct:
1. DEX pool fee where determinable.
2. Ethereum base fee attributable to the transaction.
3. Priority fee.
4. Direct builder / fee-recipient transfer when observable and attributable.
5. Binance Spot taker fee assumption frozen at 10 bps unless a lower verified account-specific fee is separately authorized before outcomes.
6. CEX spread and depth-consumption slippage for the frozen notional.
7. Inventory markout caused by the frozen hedge delay.
8. Failed/included transaction treatment when observable.

Unknown required cost => event cannot be used for positive-edge adjudication.

## Event inclusion

An event is eligible only when:
- Ethereum transaction hash and block timestamp are reproducible;
- DEX swap direction and quantities are decoded;
- token maps unambiguously to a Binance Spot USDT market;
- a contemporaneous Binance order-book observation exists for the required hedge side;
- required cost fields are present or conservatively bounded.

No token may be added because it looked profitable after observation.

## Primary metrics

For each notional and latency bucket:
- eligible event count;
- gross convergence value in bps;
- full-cost net bps;
- full-cost net USDT;
- win rate;
- median and mean net bps;
- p10 / p50 / p90 net bps;
- total net USDT;
- share of PnL from top token;
- share of PnL from top day;
- share of PnL from top 1% events.

## Minimum evidence before economic verdict

No SURVIVES_DISCOVERY verdict before BOTH:
- at least 500 eligible events; and
- at least 14 calendar days of forward evidence.

If 14 days elapse with fewer than 500 eligible events => INSUFFICIENT_SAMPLE, not NO_EDGE.

## Frozen survival rule

A notional bucket survives only if:
- total full-cost net USDT > 0 at T0+1000ms;
- median full-cost net bps > 0 at T0+1000ms;
- total full-cost net USDT remains > 0 at T0+3000ms;
- top token contributes <= 50% of positive PnL;
- top day contributes <= 35% of positive PnL;
- top 1% of events contributes <= 50% of positive PnL;
- no required cost layer is omitted.

Failure of the exact frozen rule => NO_EDGE for that bucket under V0.1. No rescue threshold under the same LAB_ID.

## Promotion boundary

Even SURVIVES_DISCOVERY is not Quase Diamante. Promotion requires the repository governance policy independently in force at adjudication time, including any replication/OOS/forward requirements beyond this protocol.

## Operational rule

Collectors may observe public chain and public CEX market data continuously. They must not:
- sign transactions;
- submit swaps;
- place/cancel orders;
- use exchange trading credentials;
- mutate wallets;
- spend funds.
