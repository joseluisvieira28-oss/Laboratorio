# SOURCE RELIABILITY V2.2 — pre-data paired Bybit book comparison
**Frozen before any V2.2 public capture; 2026-11-05 (Europe/Zurich).**
Parent: PR #336 / branch `research/source-reliability-v21-2026-11-04` at `d2897129720bfb3acc05289ca28d57c0705c2084`. Independent source-method study, **NO LIVE GO**. Do not amend any prior protocol, costs, signal, protected holdout, PR #333/#334/#335/#336, or main.

## Causal hypothesis and treatment
The Bybit official V5 WebSocket docs say L1 snapshot can be republished with unchanged `u` after up to 3 seconds without orderbook changes; L50 has nominal 20ms push cadence *when changed* and requires snapshot/delta reconstruction (zero volume deletes, new snapshot reset, u=1 service restart). This contradicts the assumption that every >1s interval without an accepted L1 *changed* snapshot proves transport failure. Historical V2.1 remains unchanged.

Capture **simultaneously on one Bybit V5 linear public WebSocket** `orderbook.1.BTCUSDT` and `orderbook.50.BTCUSDT` and a separate public MEXC `sub.depth.full BTC_USDT limit=5`. No liquidation/trade, trading order, PnL, synthetic returns or account access in this **source-only** comparison. Each arrival is persisted in order with UTC milliseconds and monotonic nanoseconds, full raw text, venue, event kind and connection segment. No interpolation, retrospective nearest join, backfill or post-hoc acceptance rules.

Three preregistered candidate Bybit policies, evaluated on identical raw receive-time samples with the same MEXC series:
- **A — L1 V2.1 control:** strict source-age <=1000ms, changed L1 snapshot with new `u` only; identical `u` and payload does NOT refresh book freshness. 30s quarantine on source-stale event, no false good seconds. This reproduces V2.1 freshness treatment for source-only comparison; not claimed byte-identical full V2.1 detector.
- **B — L1 receipt-refresh diagnostic:** strict <=1000ms fresh, identical valid repeated snapshot confirms receive liveness and refreshes book receipt time, otherwise identical to A. Diagnostic, not an accepted replacement of old frozen rules.
- **C — L50 candidate:** strict <=1000ms last validated book update, full local snapshot + incremental delta reconstruction, exact price levels (positive decimals), zero-size delete, sequence/uptick integrity and no lookahead, reset on snapshot or `u=1`. Can only become ready after complete snapshot. 30s quarantine on source-stale/invalid sequence. A delta with a valid reconstructed uncrossed BBO is a fresh frame, not a new filled order. Missing snapshot cannot be inferred from future deltas.
- Optional 3s L1 diagnostic can be calculated posthoc but never substituted into binding A/B/C economics or promotion threshold.

## Bound and budget
Single GitHub-hosted public-only bounded capture of **600 seconds**, hard 660s timeout, <=64 MiB compressed raw, <=256 MiB uncompressed raw, and no new paid service. Standard public GitHub Actions runner only; if no workflow capacity / public endpoint access, preserve failed receipt and label `SOURCE_COMPARE_NOT_MEASURED`. No scheduled, repeat, paid or extra capture. One workflow with Linux capture and Windows/Linux offline tests within 15 runner-minutes planned; dependency `websockets==15.0.1`. Log all actual transport/heartbeat/parse/clock failures; no re-labeling failures as quiet markets.
- Both connections require successful ACK, independent app ping every 15s, pong <=35s and a valid book; <=1 bounded reconnect per venue, 30s quarantine on reset. If attempts unavailable, source is blocked, not falsified.
- MEXC full snapshot version strictly increasing; envelope timestamp and five-level book validated; receive freshness <=1000ms; publisher age in [0,1500]ms, future tolerance +250ms.
- Bybit independent L1 and L50 source timestamps in [receive-1500ms, receive+250ms]. L50 delta updates must be validated; `seq` and `u` strictly increase within a segment except an explicit new snapshot or u=1 reset. No requirement that non-full-depth `u` increments exactly by one. Reject malformed symbols/quantities/crossed BBO, never silently skip invalids.

## Frozen source metrics and verdict gate
Every complete 1-second grid boundary: for each A, B, C compare joint MEXC+Bybit status **as of that boundary**. All variants share the same captured MEXC and Bybit transport interruptions. Each candidate has separate stale/quarantine state; never use future events to certify past good seconds. Report paired good seconds, bad intervals, stale triggers, book frames, duplicate L1 unchanged republished snapshots, full snapshots and L50 deltas, errors, transport gaps, total duration, real raw hashes.

`SOURCE_COMPARE_CANDIDATE` iff >=600 complete seconds, C valid seconds >=95% and C beats A by >=5 percentage points on the SAME 1-second grid, no raw integrity violation, no fatal L50 sequence/crossed-book validation error and <=1 reconnect per venue. `SOURCE_COMPARE_NO_GAIN` for adequate valid test where C does not meet both comparative gates; `SOURCE_COMPARE_BLOCKED` for insufficient/uncertain source and irrecoverable integrity failures. Baseline A/B results never rewrote the historical 92.86% from the prior 2-hour session.

This small source-method study **cannot certify 2-hour/14-day reliability or economic edge**; even SOURCE_COMPARE_CANDIDATE means only a proposal for separately approved larger source-forward. No profitability/NO_EDGE, positions, fills or PnL will be computed; `ECONOMIC_INSUFFICIENT / NO_LIVE_GO` always.
If there is no actual captured result, final verdict must say `SOURCE_COMPARE_NOT_MEASURED`, not infer improvement from unit tests.

Reference: https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook
