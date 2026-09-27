# CBBTC-ETH-MINT-BURN-FLOW-001 — HISTORICAL HEADER FAILOVER V0.1S

Frozen: 2026-09-27
Parent: VERIFIED_MULTI_RPC_LOG_FALLBACK_V0.1R
Scope: TRANSPORT / HEADER RESOLUTION ONLY

## Trigger

Canonical run #36341577535 completed Window A cleanly:
- 21 mints
- 7 burns
- 28 zero-address events
- zero log-range errors

Gate 1 then stopped before Window B evaluation because timestamp-boundary binary search requested historical block 13,035,327. PublicNode reported pruned history and BlockMachine returned HTTP 429. Receipt state was source_gate_evaluated=false, completed_window_count=1; therefore this is a technical transport blocker, not SOURCE_BLOCKED and not NO_EDGE.

## Pre-existing source-only evidence

Historical header capability run #36338930351 (V0.1N) queried the same historical block-header method and showed successful block number/hash/timestamp responses from:
- PublicNode
- BlockMachine
- 1RPC public Ethereum
- Flashbots RPC

## Remediation

Header-only fallback order becomes:
1. PublicNode
2. BlockMachine
3. 1RPC
4. Flashbots

The full census uses the same verified order for timestamp-boundary header resolution.

Historical eth_getLogs transport remains separately governed by V0.1R:
PublicNode -> BlockMachine -> MEVBlocker, 10,000-block maximum outer range.

No log provider, event definition, source window or scientific gate is changed by this header remediation.

## Scientific invariants

UNCHANGED:
- cbBTC official Ethereum contract;
- zero-address mint/burn definition;
- exact frozen windows;
- timestamp-derived boundaries;
- full census dates;
- source PASS criteria;
- supply reconciliation;
- q10/q90 calibration;
- H2-2025 sample gate;
- frozen BTC 24h Discovery;
- 2026 firewall;
- no PnL/live trading/orders/wallet/exchange mutation/main merge.

Promotion credit = 0.
