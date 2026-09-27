# CBBTC-ETH-MINT-BURN-FLOW-001 — VERIFIED MULTI-RPC LOG FALLBACK V0.1R

Frozen: 2026-09-27
Parent evidence: VERIFIED_10K_LOG_TRANSPORT_V0.1M + digest crosscheck V0.1P + span probe V0.1Q
Scope: TRANSPORT / PROVENANCE ONLY

## Trigger

The prior 10k BlockMachine source-gate run was cancelled before Gate 1 completed. Its progress log showed that Window A mint acquisition reached all 22 outer chunks but accumulated 2,184 unresolved subrange errors, indicating that a single public archive transport remained operationally brittle.

## Independent source-only crosscheck

Run #36339641212 compared the same frozen cbBTC contract, exact Transfer/zero-address filters and exact 10,000-block range across independent public RPC transports.

BlockMachine:
- MINT count 4; digest f3b6204bd06f1a94c744d5f59a83e9d2530c4a40ca069d8f3bac6d27548d7fc2
- BURN count 1; digest df90335e28c366a1eead422310255e16b81ec049f0bd24f62a5ae4d4bca44214

MEVBlocker:
- MINT count 4; exact same digest
- BURN count 1; exact same digest

Run #36339719510 additionally showed MEVBlocker can answer some larger historical ranges, but availability is not guaranteed. Therefore the frozen chunk remains 10,000 blocks; larger-range behavior receives zero authority.

## Transport decision

Historical eth_getLogs order:
1. original PublicNode attempt;
2. BlockMachine public/keyless archive fallback;
3. MEVBlocker public/keyless fallback.

The third route is used only if earlier transports fail. No event, block, day or range may be skipped, sampled, imputed or interpolated. Exact block hash, transaction hash, log index, topic and amount semantics remain unchanged.

Gate 2 uses the same 10,000-block outer chunk and the same ordered log fallback. Archive totalSupply remains bound to the pre-existing archive source and EIP-1898 blockHash anchors.

## Supersession note

BOUNDED_TRANSPORT_IMPLEMENTATION_CORRECTION_V0.1J was based on a stale static view that did not yet incorporate the completed V0.1M/P/Q transport evidence. V0.1R supersedes only J's transport-source/chunk implementation choice. It does not alter any scientific rule.

## Scientific invariants

UNCHANGED:
- Ethereum mainnet cbBTC contract;
- zero-address mint/burn definition;
- frozen probe windows;
- full census dates;
- source PASS criteria;
- supply reconciliation;
- q10/q90 calibration;
- H2-2025 sample gate;
- frozen BTC 24h Discovery;
- 2026 firewall;
- no PnL, live trading, orders, wallets, exchange mutation or main merge.

Promotion credit = 0.
