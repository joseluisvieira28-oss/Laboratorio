# SOURCE GATE V0.1 — INITIAL AUDIT

Date: 2026-09-25
Status: PARTIAL / FAIL-CLOSED

## Findings

### Binance official public archive
Official binance/binance-public-data documents daily/monthly archives for Spot and Futures trades, aggTrades and klines. These are useful for event-level executed-flow research. Futures trade timestamps are documented in milliseconds in the archive examples.

### Historical L2
Binance's historical futures order-book documentation distinguishes T_DEPTH (tick-by-tick L2 fetched from API, explicitly may have gaps), S_DEPTH (temporary snapshot solution historically limited), and T_DEPTH_BACKFILL (backfilled internal logs; documentation notes production limitations). Access historically involved an application/download workflow.

Therefore deterministic full-book replay is NOT yet proven from the ordinary free public archive.

### Current public depth
Public market-data APIs/WebSockets expose current depth without authentication, useful for forward collection, but current streams do not by themselves establish historical replayability.

## Consequence
- Trade-flow-only historical feasibility: PROVISIONALLY AVAILABLE.
- Full historical queue/cancel/L2 reconstruction: NOT PROVEN.
- 100ms/500ms labels: BLOCKED unless a source with defensible timestamp resolution and replay integrity is established.
- Do not substitute aggTrades for order-book events.
- Do not infer cancellations from missing snapshots unless source semantics justify it.

## Data-quality warning
Recent official public-data issue reports include bookDepth archive anomalies. Any bookDepth source must be checksum/version pinned and independently integrity-tested before scientific use.

## Next source-gate actions
1. Probe exact Binance USD-M BTCUSDT/ETHUSDT historical bookDepth archive schema and coverage.
2. Determine whether snapshots permit only depth-band features or event-level queue reconstruction.
3. Audit official alternative venues for downloadable historical L2 with sequence IDs.
4. Freeze the first feasible dataset before any outcome inspection.
