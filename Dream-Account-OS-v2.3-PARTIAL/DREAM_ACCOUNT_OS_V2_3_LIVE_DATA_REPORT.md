# DREAM ACCOUNT OS v2.3 — LIVE DATA REPORT

Observation: 2026-09-07 20:08 UTC

## STATUS: PARTIAL

The deployable external-runtime package and fail-closed collector/engine boundary are implemented and locally validated. A real MEXC end-to-end run is not claimed: this workspace rejects outbound MEXC traffic before a request can complete, and no external runtime is connected.

## RUNTIME

- Current: restricted-egress workspace.
- Prepared: persistent Docker service with long-running Python, restart policy, health endpoint and persistent SQLite disk; Render blueprint included.
- External deployment: **PENDING CONNECTION**.
- Execution: **NONEXISTENT**; public market data only.

## NETWORK DIAGNOSIS

| Layer | Result | Exact observation |
|---|---:|---|
| Proxy variables | PRESENT | HTTP(S) proxy at loopback port 41991; SOCKS5H proxy at loopback port 46323. No credentials exposed. |
| Firewall/egress | BLOCKED | The environment rejected outbound MEXC network access before completion. |
| DNS | UNVERIFIED HERE | No trustworthy process-level result returned after egress rejection. |
| HTTPS/TLS | BLOCKED/UNVERIFIED HERE | Infrastructure restriction, not classified as a MEXC failure. |
| Spot REST | BLOCKED HERE | Infrastructure restriction. |
| Futures REST | BLOCKED HERE | Infrastructure restriction. |
| Spot WebSocket | BLOCKED HERE | Infrastructure restriction. |
| Futures WebSocket | BLOCKED HERE | Infrastructure restriction. |

`scripts/network_diagnostic.py` records DNS, direct TLS, REST and WebSocket results independently, including exact exception classes, when run externally.

## REST: IMPLEMENTED / LIVE VALIDATION PENDING

Connection/read timeouts, retries, exponential backoff, jitter, 429/5xx awareness, circuit breaker, health metrics and short metadata cache remain active. API errors never become zero, empty market facts or signals.

## WEBSOCKET: CORE IMPLEMENTED / LIVE VALIDATION PENDING

Reconnect, heartbeat, stale detection, timestamp/sequence checks and REST reconciliation exist. Live reconnect and gap recovery cannot pass until an external handshake succeeds.

## DATA COVERAGE: 0% LIVE VERIFIED HERE

Formula: `VERIFIED / expected × 100`; operational gate: ≥95%. `PARTIAL`, `STALE` and `INVALID` snapshots cannot generate signals.

## PAIR COUNT

- Discovered: UNAVAILABLE
- Validated: 0 live-verified
- Failed: UNAVAILABLE

## FAILED DATA SOURCES

MEXC Spot REST, Futures REST, Spot WebSocket and Futures WebSocket are blocked by this runtime. The independent BTC/ETH/SOL cross-check was not run because MEXC data was not VERIFIED.

## LATENCY P50 / P95

**UNAVAILABLE / UNAVAILABLE** — no fabricated values.

## CURRENT MARKET REGIME

**UNVERIFIED — FAIL CLOSED**

## TOP 10 / TOP 3

**WITHHELD** because the live data gate did not pass.

## SOL / BTC

- SOL: **UNVERIFIED**. Old `$107` level is neither preserved nor replaced without live VERIFIED candles.
- BTC: **UNVERIFIED**. Old `$80,500` level is neither preserved nor replaced without live VERIFIED candles.

## PAPER SHADOW

- Live paper signals: 0
- Paper open: 0
- Paper closed from v2.3 live data: 0
- Current expectancy: **INSUFFICIENT SAMPLE**

## VALIDATION

- Tests: **23/23 PASS**.
- v2.3 coverage: 95% boundary, stale/partial exclusion, cross-check anomaly flag, normalized snapshot persistence after restart.
- Compilation: PASS.
- Execution-capability scan: PASS; no order/cancel/withdraw/transfer/secret-key implementation.
- Scoring, hard filters, risk engine, setup logic and thresholds: **UNCHANGED**.

## CURRENT BEST MOVE

**NO TRADE — WAIT.** Deploy the persistent runtime, require ≥95% VERIFIED coverage, reconcile WebSocket with REST, and only then allow the first real scan.

## KNOWN LIMITATIONS

1. External service is prepared but not provisioned because no cloud runtime connection is available.
2. Real endpoint compatibility, symbol count, latency, coverage and live stream recovery remain unverified.
3. Cross-check logic is tested but has no live paired observations.
4. A real A/A+ Paper Shadow signal must occur naturally and is not manufactured.

## NEXT STEP

Connect Render, deploy this package, run the included diagnostic, complete one ≥95% MEXC snapshot and cross-check BTC/ETH/SOL. Keep it running until the market naturally produces an A/A+ paper signal.

Official contracts:

- https://mexcdevelop.github.io/apidocs/spot_v3_en/
- https://www.mexc.com/api-docs/spot-v3/websocket-market-streams/
- https://mexcdevelop.github.io/apidocs/contract_v1_en/
