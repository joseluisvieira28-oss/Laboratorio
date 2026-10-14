# SOURCE GATE V0.1 — INFORMATION-PROPAGATION-GRAPH-001

Frozen: 2026-09-24
Purpose: determine what can be observed, timestamped, reconstructed, and tested without hindsight.

## Source matrix

| Surface | Candidate source | Live | Historical/backfill | Timestamp / sequence evidence | Gate |
|---|---|---:|---:|---|---|
| Binance spot/perp trades + book | Binance public WebSocket / Data portal | PASS | PARTIAL/PASS depending dataset | exchange event/trade timestamps; book update IDs where applicable; local recv timestamp required | SOURCE_PASS for live; historical provenance to verify per dataset |
| Binance funding | Binance public REST/streams | PASS | PASS for funding history subject to endpoint coverage | fundingTime is explicit | SOURCE_PASS |
| Binance OI/basis | Binance public REST | PASS | PARTIAL: official OI-stat endpoint has limited lookback; archive route must be pinned | endpoint timestamps explicit | SOURCE_PARTIAL |
| Deribit options | Deribit public WebSocket + REST | PASS | PASS for trades/DVOL; surface history must be reconstructed/pinned | per-instrument order guaranteed; change_id/prev_change_id for books; native timestamps + local recv | SOURCE_PASS |
| Deribit IV/greeks/mark surface | ticker / incremental_ticker / markprice.options | PASS | PARTIAL unless archived surface corpus is defensibly reconstructed | per-instrument ordering; cross-instrument timing asynchronous | SOURCE_PARTIAL for historical causal surface; SOURCE_PASS forward |
| Polymarket expectations | Public market WebSocket/API | PASS | PARTIAL; market selection must be frozen ex ante | market events include millisecond timestamps | SOURCE_PARTIAL |
| Ethereum public mempool | Local Geth txpool / node peer view | PASS with node | No canonical public historical mempool | node-local view; pending/queued; receive time is observer-specific | FORWARD_ONLY |
| Aave liquidation state | Aave protocol data / onchain state | PASS | reconstructable onchain in principle, but full position census/oracle state cost must be proven | chain block timestamp + oracle/state provenance required | SOURCE_PARTIAL |
| CCTP cross-chain USDC | Circle CCTP onchain burn/mint/messages | PASS | chain history reconstructable | source/destination chain event timestamps are not one global clock | SOURCE_PARTIAL |
| Chainlink/oracle/sequencer state | Chainlink feeds / onchain feed state | PASS | chain-dependent | block/feed timestamps; must preserve staleness and chain clock | SOURCE_PARTIAL |

## Primary official evidence

### Binance
- WebSocket market streams support raw and combined streams and carry exchange event data:
  https://developers.binance.com/en/docs/products/derivatives-trading-coin-futures/websocket-market-streams/Connect
- Official market-data endpoints expose funding, basis and OI; OI statistics document a limited recent-history window:
  https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/rest-api/Get-Funding-Info
- Public archive/data surface:
  https://data.binance.vision/

### Deribit
- API supports WebSocket/HTTP; WebSocket is recommended for real-time market data:
  https://docs.deribit.com/
- Market-data guide states that event ordering is guaranteed within each instrument while cross-instrument timing is asynchronous; book sequence IDs support gap detection:
  https://docs.deribit.com/articles/market-data-collection-best-practices
- Options guide exposes ticker greeks/IV, markprice.options, historical DVOL, trades and backfill methods:
  https://docs.deribit.com/articles/options-data-collection-best-practices

### Polymarket
- Public real-time market WebSocket supplies order-book, price-change and last-trade events with timestamps:
  https://docs.polymarket.com/market-data/realtime-data

### Ethereum mempool
- Geth txpool exposes pending and queued transactions from the observer's local node:
  https://geth.ethereum.org/docs/interacting-with-geth/rpc/ns-txpool

### Aave
- Health Factor < 1 defines liquidation eligibility; health factor depends on collateral/debt values and liquidation thresholds:
  https://aave.com/help/borrowing/liquidations
- Current Aave MCP documentation shows read access to live protocol position/health information:
  https://aave.com/docs/mcp/getting-started

### Circle CCTP
- CCTP burns USDC on the source chain and mints on the destination chain:
  https://developers.circle.com/cctp

### Chainlink
- Chainlink exposes Data Feeds/Data Streams and cross-chain/oracle infrastructure:
  https://docs.chain.link/

## Fail-closed rules

1. Never substitute local receive time for source event time without labelling the distinction.
2. Never compare timestamps across venues without storing measured clock offset / observation latency.
3. Never infer historical option surface state from present instrument metadata.
4. Never treat a present Aave health factor as historical liquidation pressure.
5. Never treat a mempool absence as proof that a transaction did not exist; private order flow can be invisible to a node.
6. Never select a Polymarket market after seeing BTC outcomes; market mapping must be frozen before target outcomes.
7. If source coverage changes mid-window, split the regime or block the comparison.
8. Any derived propagation edge must have an explicit event-time definition and a sensitivity test to timestamp jitter.

## Gate verdict V0.1

CORE GRAPH: SOURCE_PARTIAL, with enough defensible sources to build a minimal forward collector immediately and enough historical components to prepare a narrow Discovery corpus.

MEMPOOL: FORWARD_ONLY.
ORACLE/SEQUENCER: SOURCE_PARTIAL.
AAVE LIQUIDATION CONVEXITY: SOURCE_PARTIAL.
CCTP FLOW: SOURCE_PARTIAL.
POLYMARKET EXPECTATIONS: SOURCE_PARTIAL.

No predictive outcome has been tested in this gate.
