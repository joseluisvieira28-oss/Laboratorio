# FOREX EUR/ECB V0.2 — technical setup, activation locked

Candidate: `FOREX-ECB-EURUSDT-DISLOCATION-FWD-001`.
Parent: `94813ec386d0a94579eaab38ce2b0fa5fd4d7bdd`.
Historical V0.1 stays `SOURCE_BLOCKED`, scientific mechanism untested.

This package implements a public-only source sampler, durable SQLite raw-byte
archive, receipt hash chain, restart-safe deduplication, single-instance lease,
crash recovery checks and synthetic tests for the frozen pure signal/fill model.
It emits no economic signals, orders or PnL from real observations. No credentials.
The complete method is in `PRE_OUTCOME_METHOD_FREEZE_V02.json`; activation is
explicitly locked. Technical capability is not evidence of economic edge.

Python 3.11 or later, no third-party dependency:

```bash
python -m unittest -v test_forward.py
python collector.py --cycles 3 --interval 5
python collector.py --verify-only
```

Run these commands from this directory on a persistent runtime. On Windows use
`py -3` instead of `python` if needed. Reuse the same state directory on restart;
do not delete or overwrite earlier observations. Keep `state/burnin.sqlite3` and
exported `evidence/raw` on persistent disk, back them up after a graceful stop.
The default run is bounded and safe to repeat. A process killed mid-transaction
rolls back its incomplete write; its lease expires after 180 seconds. There is no
promise of uninterrupted capture after the ChatGPT session ends.

The sampler captures metadata, clocks, depth, recent public trades, ticker,
index/fair diagnostics and official ECB index/calendar. Clock/RTT observations
are preserved; no missing exchange clock is fabricated. Immutable raw content
hashes deduplicate bytes; receipts retain every retrieval's arrival time. Update
identity deduplication survives restart. Receipt conflicts and corrupt state fail
closed. There are no private endpoint paths or arbitrary user-supplied URLs;
redirects are rejected. TLS verification remains enabled.

REST sampling at >=5 seconds is for source capability, not the required 1-second
event runtime. Binance REST depth has no exchange event timestamp. Documented
Spot bookTicker also has none. A correctly bootstrapped timestamped diff-depth
stream and continuity checks remain required. The official public Binance
market-data-only domain is selected prospectively, on access/documentation
grounds, not outcomes. The MEXC reference index is not an independent venue.

ECB index/calendar raw capture is implemented. Semantic target-release discovery,
first-publication detection and persisted first-seen event identity are **not yet
implemented or event-tested**. Generic page hash changes never create a T0. This
is a blocker, not an armed watcher. Server timestamps are not global publication
times. The setup collector hard-stops on 23 October 2026 UTC and cannot open the
protected 29 October event. No event-capture mode or automated arm flag exists.

Next steps, preserving the committed method:

1. Establish real MEXC EUR_USDT JSON access on a persistent operator runtime.
2. Implement/qualify timestamped event streams and semantic ECB publication
   watcher; test reconnect, sequence gaps and latency with durable evidence.
3. Capture qualified burn-in: >=21,600 paired grids, >=5 weekdays, >=99% daily
   coverage. Source-only sampler rows do not automatically meet that gate.
4. Apply the frozen calibration formula without computing burn-in strategy PnL.
5. Commit calibration/activation receipt before 26 October UTC. If any gate
   fails, retain `OPERATIONALLY_BLOCKED` and do not arm the event.

GitHub Actions is not configured as a continuous feed: a scheduled job cannot
guarantee tick timing, durable local state or missed-window recovery. No Render,
paid deployment or main merge. No background process is claimed active.
