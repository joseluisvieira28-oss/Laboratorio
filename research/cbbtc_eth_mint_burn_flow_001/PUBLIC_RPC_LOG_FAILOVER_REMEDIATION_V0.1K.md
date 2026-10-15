# CBBTC-ETH-MINT-BURN-FLOW-001 — PUBLIC RPC LOG FAILOVER REMEDIATION V0.1K

Frozen: 2026-09-27
Parent: SOURCE_GATE_FULL_RPC_HARDENING_V0.1H
Scope: TRANSPORT ONLY — historical eth_getLogs acquisition.

## Trigger

Gate-1 run #36332630357 reached Window A but the frozen PublicNode route returned an archive-access refusal from the GitHub runner. The adaptive splitter therefore descended to single-block queries and accumulated 2,000 transport errors in the first 2,000-block chunk before the 45-minute runner limit.

A bounded capability probe against that exact historical chunk showed:
- PublicNode: archive access refused without personal token;
- 1RPC: public endpoint available but enforces a narrow block-range limit;
- BlockMachine: same exact 2,000-block eth_getLogs request succeeded;
- Flashbots: same exact 2,000-block eth_getLogs request succeeded.

## Allowed remediation

Preserve PublicNode as the first attempted route, then deterministically fail over to:
1. existing frozen archive endpoint BlockMachine;
2. public/keyless Flashbots RPC.

The same contract, block interval and topic filter must be sent unchanged to each route.
No event may be skipped, sampled, imputed or inferred.
The same failover order is applied to Gate 2 full-census eth_getLogs.

## Scientific contract unchanged

UNCHANGED:
- cbBTC Ethereum contract;
- zero-address Transfer mint/burn semantics;
- source windows;
- timestamp-derived block bounds;
- source PASS criteria;
- census period;
- supply normalization;
- q10/q90 calibration;
- Discovery sample gate;
- BTC outcome protocol;
- 2026 firewall;
- no PnL/live trading/main merge;
- promotion credit = 0.

This remediation can only change transport reachability, never scientific classification criteria.
