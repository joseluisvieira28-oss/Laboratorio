# CBBTC-ETH-MINT-BURN-FLOW-001 — VERIFIED 10K LOG TRANSPORT V0.1M

Frozen: 2026-09-27
Parent: PUBLIC_RPC_LOG_FAILOVER_REMEDIATION V0.1K
Scope: TRANSPORT / PROVENANCE ONLY.

## Evidence

Capability run #36338257498 established:
- PublicNode historical eth_getLogs from the GitHub runner returns an archive-access refusal without a personal token.
- 1RPC public access is available but constrains eth_getLogs block ranges.

Range run #36338644061 then tested the exact frozen cbBTC contract/topic path on the same historical Window-A boundary:
- BlockMachine 2,000 blocks: PASS.
- BlockMachine 10,000 blocks: PASS and returned 4 matching mint logs.
- BlockMachine 20,000 / 50,000: explicit max-range rejection, max = 10,000.
- Flashbots accepted larger ranges but returned 0 where BlockMachine returned 4 for the same 10,000-block query.

## Provenance decision

Flashbots is excluded from the scientific fallback path because the source-only probe showed a silent historical-log discrepancy.

Gate 1 and Gate 2 historical log transport is therefore pinned to the deterministic order:
1. frozen PublicNode attempt;
2. existing BlockMachine public/keyless archive fallback.

Chunk size is 10,000 blocks inclusive maximum, exactly matching the proven BlockMachine limit.

## Unchanged science

No contract, network, event definition, source window, census period, threshold, normalization, sample gate, horizon, direction, cost, outcome rule, 2026 firewall or promotion rule changes.

No event is skipped, sampled, interpolated or imputed.
Promotion credit = 0.
