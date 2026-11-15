# CBBTC-ETH-MINT-BURN-FLOW-001 — SINGLE-RUN RETRY TRIGGER V0.1F

Triggered: 2026-09-27

Authority:
- SOURCE_GATE_FREEZE_V0.1
- ADAPTIVE_GETLOGS_TRANSPORT_REMEDIATION_V0.1C
- BOUNDARY_HEADER_FAILOVER_V0.1D
- RPC_TIMEOUT_TRANSPORT_REMEDIATION_V0.1F
- all previously frozen downstream predictor/state/sample/mechanism gates.

Reason:
Run #36276732156 was cancelled after remaining for hours inside the pre-Gate-1 source step with no source receipt persisted. The original transport lacked explicit HTTP timeouts. No frozen source window completed and no market outcome was opened.

This retry changes transport handling only:
- same cbBTC contract;
- same source windows;
- same zero-address Transfer mint/burn semantics;
- same exact boundary logic;
- same adaptive getLogs coverage;
- same source/decode/duplicate gates;
- same downstream scientific freezes.

Hard rules:
- evaluated SOURCE_BLOCKED is terminal;
- SOURCE_PASS may continue only through the already-frozen chain;
- 2026 remains closed unless separately authorized by the frozen governance path;
- PnL/live trading/mutation remain forbidden;
- no main merge.
