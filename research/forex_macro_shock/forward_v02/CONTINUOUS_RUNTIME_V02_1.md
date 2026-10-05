# FOREX EUR/ECB — continuous source setup V0.2.1

The V0.2 method freeze is unchanged. Outcome evaluation and event activation
remain locked. This is implementation/technical validation only, not a scientific
amendment or authorization for trading.

## Implemented

`feeds.py`: Binance EURUSDT timestamped diff-depth, REST 5000-level bootstrap,
buffered initial deltas, U/u bridge and continuity, absolute quantity updates and
zero-level removal. Duplicates do not advance source receipt freshness. Sequence
gaps, reversed clocks, contradictory update IDs, reconnects and invalid/crossed
books invalidate the book; a fresh bootstrap is required.

MEXC EUR_USDT uses the current official public `sub.depth` channel with unmerged
updates, full REST bootstrap and strict version+1. It requires the documented
`data.cts` matching-engine timestamp; root `ts` is archived, not silently treated
as matching-engine time. Missing cts fails closed. Gaps rebootstrap live; they
never backfill a missed observation. This path is implemented but not live
qualified while the MEXC handshake is inaccessible here.

`ecb_watcher.py`: exact official release URL/date, semantic title/policy content,
placeholder rejection, immutable content hash and first-seen evidence across
restart. Cookie/banner or index changes do not establish publication. The
runtime captures the official index, discovers only the target dated release,
retrieves/validates it and records a negative-to-positive observation interval.
Unknown first-negative interval or >2s interval never qualifies timing. The
target release does not exist yet; its real publication cannot be event-tested
today. Setup polls once a minute and **cannot** be represented as the frozen
one-second event watcher. Event mode is deliberately absent/locked.

`runtime.py`: concurrent source streams, metadata/server clocks, watcher and
one-second paired grids; durable raw frames and reconstructed book identities,
hash chain, local/monotonic times, restart lease and source-failure receipts.
Only source/burn-in basis/spread are computed, when both sources and clocks
qualify during the frozen window; never strategy PnL. Wall-clock steps, stale
quotes, timestamp mismatch, invalid metadata and >250ms grid lateness invalidate
the grid. No retroactive catch-up/interpolation. Missing paired inputs stay
invalid. Source clock uncertainty follows the frozen RTT/offset gates.

`supervisor.py`: foreground restart on persistent operator disk. Processes run
in bounded one-hour segments, reuse the same SQLite archive, and stop before
23 October UTC. Five consecutive runtime failures stop the supervisor. Source
outages within a healthy process are recorded/invalidated and retried with a
bounded 2..30s backoff. It does not install a service, scheduled task or login.

## Operator execution

On Windows: download this directory from the named branch; Python 3.11+ must be
installed. Run `start-burnin.cmd`. It creates a project-local virtual environment,
installs `websockets==16.0` and `httpx==0.28.1`, then starts the foreground supervisor. Keep the
window open and the computer awake. Stop with Ctrl+C, then restart the same file
to resume the archive. No credentials, MEXC login, accounts, orders or wallets.

On Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-runtime.txt
.venv/bin/python supervisor.py
```

For a bounded smoke test:

```bash
python -m unittest -v test_forward.py test_streams.py
python runtime.py --seconds 90
```

The Windows launcher is inspected code, not tested on a Windows host in this
execution. This runtime does not promise to remain active after the ChatGPT
session or after the operator closes its terminal. Persistent disk alone is not
continuous health; activation still requires actual observations.

## GitHub Actions

A public standard Linux runner can perform a bounded 90s source smoke with raw
SQLite/report artifacts. Push trigger is limited to this non-main branch and
these source implementation paths; workflow_dispatch allows explicit repetition.
No schedule, no secrets, no exchange mutation. This is source-health diagnosis
from a different runtime, not a replacement for continuous five-day burn-in.
Artifact TTL 90 days is not an indefinite evidence-retention claim.

## Remaining activation gates

Live MEXC JSON/WS, both source clock/sequence/latency gates, persistent continuous
operator observation, qualifying five-day burn-in, committed calibration and
activation receipt before 26 Oct UTC, and qualified one-second target publication
watcher/event shadow runner are all still required. Implemented setup watcher
logic does not remove the event-runtime lock. Do not claim FORWARD_ARMED merely
because the tests or bounded workflow succeed.

References: official MEXC native WS/order-book/maintenance docs and Binance Spot
diff-depth docs. No methodological source, threshold, horizon, fee, event list,
minimum N or statistical gate was changed.

## HTTP timing repair

The first GitHub smoke proved real MEXC/Binance public stream access and sequence
maintenance, but zero paired grids qualified. Its two cold Binance clock requests
took 667/675ms; reopening HTTP/TLS per request unnecessarily adds transport cost.
`transport.py` now reuses HTTP connections with TLS verification, normal environment
proxy settings (`trust_env=True`), explicit URL allowlist and redirects disabled.
Every actual send/receive/RTT is still recorded. No RTT is subtracted, no clock gate
relaxed, and stale quotes never refreshed by receipt alone. A subsequent smoke
must prove whether real measured RTT meets the unchanged gate.
