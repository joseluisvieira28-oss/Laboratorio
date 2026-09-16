# CRYPTO EDGE RADAR V0.2

Status: **PUBLIC SHADOW INFRASTRUCTURE ONLY**  
Development branch: `crypto-edge-radar-v0.1`  
Draft PR: `#22`  
Live trading: **FORBIDDEN**  
Authenticated exchange APIs: **FORBIDDEN**  
Order creation / cancellation / mutation: **NOT IMPLEMENTED**

## Purpose

Provide a strategy-agnostic public market monitoring service that can run continuously and accept a future Crypto Lab strategy **only after prospectively governed promotion to shadow**.

The radar does not discover edges, tune rules, rescue rejected candidates, auto-promote strategies, or authorize capital. Research governance remains upstream and authoritative.

## Current capability

- Binance USD-M public market-data GET endpoints only.
- Core universe: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT.
- Optional `liquid` observation universe using frozen 24h quote-volume and max-symbol filters.
- Empty strategy registry by default.
- Only `PROMOTED_SHADOW` adapters may emit `VALID_SIGNAL`.
- SQLite evidence log with SHA-256 payload hashes and chained event hashes.
- Heartbeat event persisted after each successful service cycle.
- Atomic JSON health/status file.
- Local JSONL notification sink for service failures and future valid shadow signals.
- Bounded service mode for CI soak tests and unbounded service mode for a future authorized host.
- `status` and `verify-evidence` commands.
- No dashboard, webhooks, API keys, balances, positions, orders, cancels, amendments, or exchange mutation.

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
PUBLIC SHADOW SERVICE
   |
   +--> public market observation
   +--> deterministic evaluation
   +--> heartbeat/status
   +--> evidence chain
   +--> local notification sink
   |
   X  no order path exists
```

## Run locally

Requires Python 3.11+ and no third-party runtime packages.

```bash
cd crypto_edge_radar
python -m radar once
python -m radar service --interval 30
python -m radar service --interval 5 --max-cycles 3
python -m radar status
python -m radar verify-evidence
```

Environment variables:

```bash
RADAR_DB=radar_evidence.sqlite3
RADAR_STATUS=radar_status.json
RADAR_NOTIFICATIONS=radar_notifications.jsonl
RADAR_UNIVERSE_MODE=core5          # core5 | liquid
RADAR_MAX_SYMBOLS=50
RADAR_MIN_QUOTE_VOLUME=50000000
RADAR_HTTP_TIMEOUT=10
```

## Health semantics

Successful service cycles publish `health=OK`, cycle number, selected universe, registered strategy count, valid signal count and the evidence receipt.

Any market-data/evaluation failure publishes `health=FAIL_CLOSED`, emits no valid signal, records the failure when persistence is available and writes a local failure notification. Service intervals below five seconds are rejected.

## Notifications

V0.2 deliberately uses a local JSONL sink rather than Telegram, email, Discord or webhooks. External delivery is a later transport layer and must not create an exchange-order path. A future `VALID_SHADOW_SIGNAL` notification is informational/paper-only unless a separate governance phase explicitly authorizes something else.

## Real public-data validation

CI contains two gates:

1. offline compile + unit/safety tests;
2. a bounded three-cycle soak using real Binance public USD-M data, followed by evidence-chain verification and assertions that the final heartbeat is healthy, the Core5 is present, the strategy registry is empty and valid-signal count is zero.

The bounded CI soak proves the public path; it is **not** represented as a 24/7 deployment.

## Promotion contract

A future strategy adapter must have immutable identity and explicit prospective `PROMOTED_SHADOW` status from its own research authority package. `RESEARCH`, `CANDIDATE`, `REJECTED`, `CLOSED`, unknown and missing promotion states fail closed.

## Current strategy state

No strategy is bundled as promoted. This is intentional: the radar can mature operationally while the Crypto Lab continues hunting for an edge that actually survives the scientific gates.
