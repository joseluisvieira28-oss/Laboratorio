# RADAR KEEPALIVE — CAUSE-BOUND OPERATIONS FORENSICS 2026-10-10

Status: ROOT_CAUSE_PARTIAL_VERIFIED / INTEGRITY_REMEDIATION_NOT_DEPLOYED / NO_LIVE_AUTHORITY.

## Read-only proofs
- Canonical Render service: `crypto-edge-radar-v05-canary`, `srv-dalqkpu1egvs73fhiehg`; workspace `Laboratorio`. Render service config is `plan=free`, `numInstances=1`, `autoDeploy=off`, `startCommand=cd crypto_edge_radar && python -m radar web-service --interval 30`. This is PUBLIC_SHADOW_ONLY; not the MEXC Windows operator.
- Latest Render deploy viewed: `dep-db4skqd9fdbs73aopjpg`, commit `b9d8e28ff0ec0fe8a67cc9e1970e8c1050c2fa36`, build/deploy succeeded 2026-10-10 05:19:27 UTC, `status=live`. This means deployment was live in Render's control plane, NOT proof of a continuously running 24/7 process.
- Render application logs contain repeated 30-second cycles 09:09–09:18 UTC, no further app logs in queried 09:18–12:18 UTC window. Ledger last persisted `RADAR_RUNTIME_LIVENESS` 09:15:26 UTC and remains at 2,676 events as of 12:14 UTC. The runtime writer may have idled, slept, stopped or lacked traffic. No exact shutdown reason was found among read service events.
- The scheduled [main keepalive workflow](https://github.com/joseluisvieira28-oss/Laboratorio/blob/main/.github/workflows/radar-v09-keepalive.yml) requests `*/8 * * * *`; actual GitHub scheduled keepalive executions in this interval were 2026-10-10 02:38:57 UTC (success) and 09:03:25 UTC (cancelled), a 6h24 gap. Scheduling intent is NOT delivery SLA. `cancel-in-progress=true` and job timeout three minutes.
- Cancelled run [38040036492](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38040036492): curl GET /health at 09:03:31 timed out with 0 bytes after ~90 sec at 09:05:00, retried and timed out ~90 sec at 09:06:35; runner cancelled at 09:06:41 (approaching 3-minute job limit). No successful health payload in that run.
- Successful run [38017728759](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38017728759) at 02:38:57–02:40:17 UTC: `mode=PUBLIC_SHADOW_ONLY`, `health=OK`, `orders_created=false`, `live_capital_enabled=false`; successful GET after ~71 seconds does NOT certify subsequent uptime.
- The persisted [gap event](https://github.com/joseluisvieira28-oss/Laboratorio/blob/audit/radar-authority-economic-integrity-2026-10-10/audits/RADAR_AUTHORITY_ECONOMICS_INTEGRITY_AUDIT_2026-10-10.md) of Oct10 09:05 records 12,841.725 seconds, with `requires_missed_window_review=true`.

## Adjudication
P0: CONTINUITY_NOT_DEFENSIBLE_ON_FREE_KEEPALIVE_ARCHITECTURE. A successful deployment or a healthy liveness bucket does not prove all missed signal windows were observed. The 09:03 scheduled keepalive run demonstrably FAILED; this is a concrete operational failure. There is insufficient evidence to attribute every missing interval solely to Render sleep, GitHub schedule delay, repeated redeploys, firewall, or a Python crash.

P0: CED1D current `FAIL_CLOSED` due official Binance Vision bookDepth 2026-10-08 HTTP 404. Main Radar runtime's health calculation `"health": "OK" if not errors` resets to OK on later cycles despite persisted failed CED1D status. Proposed telemetry-only correction is isolated under branch `fix/radar-triple-gate-truth-v01-2026-10-10`; NOT deployed.

## Safe remedy, separated by authority
1. READ-ONLY: preserve hash-bound logs, exact deploy identity, liveness gap event IDs, GitHub scheduled workflow IDs and missed windows. Do not fabricate synthetic liveness, signals or fills.
2. Fix keepalive as **honest diagnostics**, not a guarantee: bound cold-start probe, do not claim healthy on non-JSON/incorrect mode, report 90-second timeout as failure (not success), and separate deployment heartbeat from scientific watcher signal continuity. A push-branch patch alone does NOT repair GitHub scheduler delays.
3. If 24/7 forward signal capture is mandatory, require a **genuinely always-on host/scheduler** with persistent single writer, immutable deploy SHA and measured >= expected uptime. Provider service plan change may incur cost: NEVER upgrade automatically. A free-instance + opportunistic GitHub cron does not provide hard uptime guarantees.
4. Resolve CED1D latest archive 404 only via frozen-source retry/transport authority. Do not substitute another venue, change science, fabricate backfills or retune.
5. Windows MEXC operator state remains separately UNVERIFIED; no exchange/authenticated account reads, arming, manual restart or orders were performed by this investigation.

No main merge, deployment, capital, exchange mutation, orders or post-outcome tuning.
