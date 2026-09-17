# CRYPTO EDGE RADAR — LOCAL OPERATOR NODE V1

Status: READ-ONLY / SHADOW / PRE-EXECUTION

## Purpose

Use an always-on home Windows PC as the low-latency local operator node while
keeping Render as a separate observability/canary layer.

## Recommended hybrid architecture

```text
SCIENTIFIC AUTHORITY (GitHub / Drive)
              |
              v
      FROZEN STRATEGY ADAPTERS
              |
              v
HOME PC — LOCAL OPERATOR NODE
- MEXC public market feed
- exact-timing scheduler
- gate / risk logic
- local evidence cache
- future local secret store
- future authenticated transport
- local dashboard: 127.0.0.1:8787
              |
              +---------------------> MEXC
              |
              v
RENDER — REMOTE CONTROL ROOM / WATCHDOG
- read-only dashboard
- canary
- heartbeat / external visibility
- no exchange credentials
```

## Why the PC is useful

- no free-host sleep/wake penalty;
- secrets can remain local rather than in a public web service;
- exact-timing scheduler can stay continuously running;
- local process can eventually own exchange transport without exposing the
  credentials to the dashboard;
- easier emergency physical kill switch: stop service, disconnect network, or
  shut down the node.

## What becomes harder

- home power and internet outages are now operational risks;
- Windows updates/reboots must be controlled;
- system clock accuracy matters;
- process auto-restart and watchdogs are required;
- remote observability must be separated from local execution permissions.

## V1 operating rules

1. Windows sleep/hibernation must be disabled while the node is armed.
2. The Windows clock must remain synchronized.
3. Prefer wired Ethernet over Wi-Fi where practical.
4. Exchange credentials are forbidden in Git, the browser dashboard, logs and
   notification payloads.
5. The dashboard remains loopback-only by default.
6. No authenticated order transport exists in V0.7.
7. Render remains a read-only secondary observer, not the sole timing authority.
8. A future executor must fail closed if the local node loses clock, network,
   market data, risk state, strategy identity or exchange acknowledgement.

## Current launcher

From `crypto_edge_radar` on Windows:

```bat
windows\start_radar_node.bat
```

Then open:

```text
http://127.0.0.1:8787
```

## Packaging path

After the timing soak passes:

1. freeze runtime dependencies;
2. build a signed/hashed Windows package or executable;
3. add auto-start/restart supervision;
4. add local health watchdog;
5. only then design a separate authenticated MEXC transport module.
