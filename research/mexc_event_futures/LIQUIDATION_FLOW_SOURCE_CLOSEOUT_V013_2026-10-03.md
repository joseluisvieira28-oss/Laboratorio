# LIQUIDATION-FLOW-FWD-001 initial public source gate

Verdict: NO_EVENTS_OBSERVED, not PASS and not NO_EDGE.
Run 37073818293 / job 111059114674 / source commit a277123b29ab2e7028a7b2858845170f6f583ac6.
600.954 seconds elapsed. Successful public subscription acknowledgement and heartbeat
pongs; no transport exceptions. Valid real liquidation records: BTCUSDT 0, ETHUSDT 0.
No real liquidation payload exists from which to verify required event field semantics,
timestamp freshness and hashes. Do not call a subscription acknowledgement a source PASS.
Do not interpret missing liquidation messages as a scientifically validated zero-flow series.

Artifact 11255353214, v013-public-source-liquidation.
ZIP SHA256 dd22bc831c7eca3be57d4d98d6c5a1fa679d98f7d48e276d4f5230abe5e46da0.
Independent verification: 30/30 preserved raw messages SHA256 + length PASS.
The separate local websocket attempt was SOURCE_BLOCKED (HTTP 200 instead of upgrade).
It is preserved separately and is not relabelled using runner results.

Family remains SOURCE_GATE_REQUIRED. No activation, direction labels, MEXC outcomes
or threshold estimation from this quiet 10-minute interval. Next: a separately frozen
longer public source-only window and, after real-data PASS, forward calibration.
