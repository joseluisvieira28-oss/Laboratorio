# CBBTC-ETH-MINT-BURN-FLOW-001 — HISTORICAL CODE FALLBACK V0.1U

Frozen: 2026-09-27
Parent: HISTORICAL_HEADER_FAILOVER V0.1S
Scope: TRANSPORT / HISTORICAL CONTRACT-CODE PROVENANCE ONLY

## Trigger

After V0.1S, Gate 1 completed Window A cleanly but stopped before Window B logs because the frozen historical contract-code check at the Window-B ending block could not complete through the existing two-route transport.

Observed blocker:
- BlockMachine: HTTP 429
- PublicNode: archive request requires personal token
- source_gate_evaluated=false
- completed_window_count=1

This was technical transport failure, not SOURCE_BLOCKED and not NO_EDGE.

## Exact-block source probe

Run #36341961990 resolved the frozen Window-B exclusive end boundary:
- first block at/after 2025-07-01 00:00:00 UTC = 22,820,674
- ending block = 22,820,673
- ending timestamp = 2025-06-30 23:59:59 UTC

Historical eth_getCode at block 22,820,673:
- BlockMachine: PASS, code present, 1,550 bytes
- MEVBlocker: PASS, code present, 1,550 bytes
- SHA-256 on both = 7bac213090f4f3785394eb9912cef518b76f1272fd224bc6ddae4ecfe3859cad
- PublicNode: archive token required
- 1RPC: historical state unavailable
- Flashbots: HTTP 504

## Transport decision

Historical contract-code check order:
1. BlockMachine
2. MEVBlocker
3. PublicNode

MEVBlocker is admitted only because the exact frozen Window-B ending block produced byte-identical contract code to BlockMachine.

No scientific contract changes.

## Scientific invariants

UNCHANGED:
- official Ethereum cbBTC contract;
- zero-address mint/burn definition;
- exact frozen source windows;
- exact block boundaries;
- Source PASS criteria;
- full census dates;
- supply reconciliation;
- q10/q90 calibration;
- H2-2025 sample gate;
- frozen BTC 24h Discovery;
- 2026 firewall;
- no PnL/live trading/orders/wallet/exchange mutation/main merge.

Promotion credit = 0.
