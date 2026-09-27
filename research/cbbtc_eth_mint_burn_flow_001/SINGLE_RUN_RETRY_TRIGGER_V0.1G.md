# CBBTC-ETH-MINT-BURN-FLOW-001 — SINGLE-RUN RETRY TRIGGER V0.1G

Triggered: 2026-09-27

Supersedes queued V0.1F before V0.1F execution.

V0.1G contains ONLY transport hardening already frozen in:
- RPC_TIMEOUT_TRANSPORT_REMEDIATION_V0.1F
- FULL_CENSUS_RPC_TIMEOUT_REMEDIATION_V0.1G

Scientific authority and all gates remain unchanged.

Execution order:
1. exact frozen Source Gate;
2. only SOURCE_PASS -> full outcome-blind 2024-09-12 through 2025-12-31 flow census;
3. only census PASS -> frozen q10/q90 state calibration;
4. only calibration PASS -> H2-2025 outcome-blind transition sample gate;
5. only sample PASS -> frozen 2025 BTC 24h mechanism Discovery;
6. 2026 remains CLOSED after Discovery unless separately authorized.

Evaluated SOURCE_BLOCKED / census BLOCKED / insufficient sample / Discovery FAIL are terminal under the existing decision tree.

No PnL, orders, exchange/wallet mutation or main merge.

## Relaunch — 2026-09-27

Relaunch authorized after bounded transport hardening V0.1H, V0.1I and implementation correction V0.1J.
Scientific contract unchanged. This edit exists only to trigger the existing single-run workflow on the hardened branch head.

## Relaunch — V0.1R

Relaunch after digest-verified ordered log fallback: PublicNode -> BlockMachine -> MEVBlocker, fixed 10,000-block outer range. Scientific contract unchanged; promotion credit 0.

## Relaunch — V0.1S

Relaunch after probe-verified historical header failover. Header order: PublicNode -> BlockMachine -> 1RPC -> Flashbots. Log transport remains V0.1R. Scientific contract unchanged.

## Relaunch — V0.1U

Relaunch after exact Window-B historical eth_getCode crosscheck. CODE_RPCS: BlockMachine -> MEVBlocker -> PublicNode. Scientific contract unchanged.
