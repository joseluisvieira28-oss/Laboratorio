# CRYPTO EDGE RADAR V0.3 — AGGRESSIVE MODE

Status: **PUBLIC MARKET OBSERVATION + FAIL-CLOSED CONTROL ROOM**  
Development branch: `crypto-edge-radar-aggressive-v0.3`  
Scientific governance: **unchanged / fail-closed**  
Authenticated live order transport: **NOT ENABLED IN REPOSITORY**

## Purpose

Operate the Crypto Lab's prospectively governed candidates as a real-time monitoring and deployment-preparation system without weakening the scientific rules that created them.

The intended production chain is:

```text
RADAR -> ELIGIBILITY GATE -> RISK FIREWALL -> EXECUTION-READY INTENT -> EXCHANGE TRANSPORT
```

The current branch implements the public market layer, deployment/risk gates, receipts, deterministic automation contract and read-only web control room. Real order transport remains a separate final boundary and must never bypass strategy-specific execution/risk gates.

## Current capabilities

- Binance USD-M public market feed.
- Binance Spot market-data-only infrastructure feed.
- **MEXC Futures public market feed** using the current `https://api.mexc.com` domain.
- MEXC public paths are allowlisted to contract detail and ticker only.
- No API key, secret, signing or order method exists in the market-data provider.
- Core5 universe: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT.
- SQLite evidence chain with SHA-256 receipts.
- Heartbeat/status JSON and local JSONL machine events.
- Deployment gate and default micro-live risk firewall.
- Exact ETF-CME institutional-flow signal/source trap.
- Multi-bot read-only web control room.
- One-process `control-room` mode that runs public observation and dashboard together.
- Deterministic automation policy in `AUTO_EXECUTION_CONTROL_CONTRACT_V1.json`.

## Focus bots shown in the control room

- `ETF-CME-INSTFLOW-001` — Tier 2 promoted candidate / fragile; source binding live; execution instrument and strategy-specific risk contract still required.
- `BNB-LAUNCHPOOL-DEMAND-001` — Tier 3 forward shadow only.
- `BTC-OPTIONS-EXPIRY-REVERSAL-001` — Tier 3 weak-candidate shadow only.
- `HTF-DH03-12H` — diagnostic secondary survivor; shadow only until legitimately re-certified.

Rejected / failed candidates remain blocked by the registry and are never rescued by the dashboard.

## Risk firewall defaults

These are launch-validation caps, not a claim that every strategy already has an executable risk model:

- planned risk per trade: **0.10% equity**
- max simultaneous planned risk: **0.30% equity**
- daily stop: **0.30% equity**
- weekly stop: **0.75% equity**

A strategy without a frozen bounded-loss or explicit exposure-loss model stays blocked from real capital.

## Run locally — MEXC control room

Requires Python 3.11+ and no third-party runtime packages.

```bash
cd crypto_edge_radar
set RADAR_PROVIDER=mexc_futures_public
python -m radar control-room --host 127.0.0.1 --port 8787 --interval 30
```

Then open:

```text
http://127.0.0.1:8787
```

The dashboard refreshes its state automatically. It is read-only and exposes no credential or order endpoint.

Other useful commands:

```bash
python -m radar once
python -m radar service --interval 30
python -m radar dashboard --host 127.0.0.1 --port 8787
python -m radar status
python -m radar verify-evidence
python -m radar etf-cme-signal
python -m radar risk-budget --equity 5000
```

Environment variables:

```bash
RADAR_DB=radar_evidence.sqlite3
RADAR_STATUS=radar_status.json
RADAR_NOTIFICATIONS=radar_notifications.jsonl
RADAR_PROVIDER=mexc_futures_public      # mexc_futures_public | binance_usdm | binance_spot_public
RADAR_UNIVERSE_MODE=core5               # core5 | liquid
RADAR_MAX_SYMBOLS=50
RADAR_MIN_QUOTE_VOLUME=50000000
RADAR_HTTP_TIMEOUT=10
```

## Automation state machine

The frozen control contract uses:

```text
BLOCKED -> SHADOW -> GATED -> ARMED -> TRADE_READY -> SUBMITTED -> FILLED -> EXIT_PENDING -> CLOSED
                                               \-> FAIL_CLOSED
```

`TRADE_READY` is impossible unless the scientific tier, exact strategy identity, source, timing window, execution instrument, current cost model, strategy-specific risk model, account risk firewall, duplicate check and pre-trade receipt all pass.

Late-entry chasing, martingale, revenge sizing, duplicate event execution and post-signal strategy-rule changes are explicitly forbidden.

## Security boundary

- Never commit exchange credentials to Git.
- Never expose credentials in the dashboard.
- Public MEXC market observation requires no API key.
- Any future authenticated transport must use a local/host secret store and remain downstream of the deterministic gate/risk engine.
- The dashboard remains read-only even when a future transport layer is enabled.

## CI

CI currently performs:

1. compile + unit/safety tests;
2. bounded Binance public shadow soak;
3. ETF-CME public source-trap capture;
4. evidence-chain verification;
5. bounded real **MEXC Futures public observation** of the Core5;
6. MEXC heartbeat/provider assertions and artifact upload.

Passing these infrastructure gates proves connectivity and fail-closed behavior. It does **not** promote a strategy or authorize capital by itself.
