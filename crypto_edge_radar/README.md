# CRYPTO EDGE RADAR V0.1

Status: **SHADOW INFRASTRUCTURE ONLY**  
Branch: `crypto-edge-radar-v0.1`  
Live trading: **FORBIDDEN**  
Authenticated exchange APIs: **FORBIDDEN**  
Order creation / cancellation / mutation: **NOT IMPLEMENTED**

## Purpose

Build the smallest strategy-agnostic real-time monitoring layer that can receive a future Crypto Lab strategy **only after that strategy has been prospectively promoted to shadow**.

The radar does **not** discover edges, tune parameters, rescue rejected candidates, rank research hypotheses, or decide that a strategy is production-ready. The laboratory remains the authority for research and promotion.

## V0.1 scope

- Binance USD-M public market-data GET endpoints only.
- Core universe: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT.
- Optional `liquid` discovery mode can observe a broader USDT-perpetual universe by 24h quote volume, but observation does not authorize trading.
- Strategy registry is empty by default.
- Only adapters with promotion status `PROMOTED_SHADOW` may emit a `VALID_SIGNAL`.
- Non-promoted adapters are hard-blocked even if their internal rule returns LONG/SHORT.
- Append-only SQLite evidence log with SHA-256 hash chaining.
- One-shot and polling-loop CLI modes.
- No dashboard, notifications, webhooks, API keys, positions, balances, orders, or exchange mutation in V0.1.

## Scientific firewall

```text
RESEARCH LAB
   |
   | explicit prospective promotion
   v
STRATEGY ADAPTER REGISTRY
   |
   | promotion_status == PROMOTED_SHADOW
   v
REAL-TIME RADAR
   |
   +--> market observation
   +--> deterministic signal evaluation
   +--> evidence log
   |
   X  no order path exists
```

A rejected or merely interesting strategy must remain outside the promoted registry. Historical labels are not sufficient.

## Run locally

Requires Python 3.11+ and no third-party runtime packages.

```bash
cd crypto_edge_radar
python -m radar once
python -m radar loop --interval 30
```

Optional environment variables:

```bash
RADAR_DB=radar_evidence.sqlite3
RADAR_UNIVERSE_MODE=core5          # core5 | liquid
RADAR_MAX_SYMBOLS=50
RADAR_MIN_QUOTE_VOLUME=50000000
RADAR_HTTP_TIMEOUT=10
```

## V0.1 outputs

Each cycle records an immutable-style evidence event containing:

- UTC timestamp;
- universe mode and selected symbols;
- observed public market snapshot;
- strategy evaluation decisions;
- payload hash;
- previous-chain hash;
- new chain hash.

No event is equivalent to an order.

## Promotion contract

A future strategy adapter must provide:

- immutable `strategy_id`;
- explicit `promotion_status`;
- deterministic evaluation from supplied market data;
- frozen signal timeframe and rule identity in its own authority package;
- no network calls to private/authenticated endpoints;
- no side effects other than returning a signal decision.

V0.1 accepts only:

```text
PROMOTED_SHADOW
```

for valid shadow signals. `RESEARCH`, `CANDIDATE`, `REJECTED`, `CLOSED`, unknown values and missing metadata fail closed.

## Current state

No strategy is bundled as promoted in V0.1. This is intentional. The radar infrastructure can be validated independently while the Crypto Lab continues searching for a strategy that actually passes its scientific gates.
