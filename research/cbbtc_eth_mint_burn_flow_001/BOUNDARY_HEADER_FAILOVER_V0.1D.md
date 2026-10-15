# CBBTC-ETH-MINT-BURN-FLOW-001 — BOUNDARY HEADER FAILOVER V0.1D

Frozen: 2026-09-27
Parent: SOURCE_GATE_FREEZE_V0.1 + BOUNDARY_RESOLUTION_TECHNICAL_REMEDIATION_V0.1A
Scope: transport/provenance only.

## Trigger

Single-run #36276278243 failed before either frozen source window was evaluated.

Exact failure:
BOUNDARY_MID_FAILED_A_START_13032310: could not coalesce error

The current cbBTC identity check had already passed:
- symbol = cbBTC
- decimals = 8

No mint/burn window counts, market outcomes, 2026 data or PnL were opened.

Therefore this is NOT a scientific SOURCE_BLOCKED verdict.
It is a boundary-header transport failure.

## Permitted remediation

For timestamp→block binary search and exact boundary metadata only:

Primary header RPC:
https://ethereum-rpc.publicnode.com

Fallback header RPC:
https://rpc-eth.blockmachine.io

Use raw JSON-RPC eth_getBlockByNumber instead of ethers provider.getBlock so provider-wrapper coalescing cannot hide the exact transport error.

For every requested block tag:
1. attempt primary with bounded retry/backoff;
2. if exhausted, attempt fallback with bounded retry/backoff;
3. retain the endpoint that supplied the header;
4. preserve exact block number/hash/timestamp;
5. no block/date substitution.

The source event/log authority and scientific semantics are unchanged.

## Gate-evaluation distinction

The source receipt must explicitly record whether the two frozen source windows were actually evaluated.

If execution dies BEFORE both windows are completed:
classification remains SOURCE_BLOCKED at process level for fail-closed execution, but
source_gate_evaluated = false
and the operational verdict is TECHNICAL_SOURCE_TRANSPORT_BLOCKED.

Such a failure is NOT terminal under the scientific decision tree.

Only when:
source_gate_evaluated = true

may SOURCE_BLOCKED be treated as the terminal Gate-1 scientific result.

## Unchanged

- Ethereum cbBTC contract;
- zero-address Transfer mint/burn definition;
- fixed windows;
- log coverage;
- decode/duplicate gates;
- SOURCE_PASS criteria;
- no 2026;
- no market outcomes;
- no PnL/trading;
- no main merge.

Promotion credit = 0.
