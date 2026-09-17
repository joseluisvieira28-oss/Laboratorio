# STETH-REDEMPTION-BASIS-001 — SOURCE GATE V0.1

Status: **AUTHORIZED SOURCE-ONLY PROBE**  
Date: **2026-09-17**

This gate inherits `STETH_REDEMPTION_BASIS_001_PRE_SOURCE_AUTHORITY_V0_1.md`.

## Gate A — identity and provenance

PASS only if:
- Ethereum chain id is `1`;
- Lido WithdrawalQueueERC721 and stETH bytecode are non-empty at relevant historical blocks;
- Curve legacy ETH/stETH pool bytecode is non-empty at relevant historical blocks;
- Lido withdrawal queue deployment transaction receipt is retrievable and predates/equal the frozen source start.

## Gate B — historical state access

At historical blocks near both the beginning and end of the frozen period, PASS only if RPC transport supports non-empty successful `eth_call` responses for:
- Curve `get_dy(int128,int128,uint256)`;
- Curve `fee()`;
- Lido WithdrawalQueue `getLastRequestId()`;
- Lido WithdrawalQueue `getLastFinalizedRequestId()`;
- Lido WithdrawalQueue `unfinalizedStETH()`.

Values must not be printed or interpreted in this source-only run. Only accessibility/schema/non-empty response may be recorded.

## Gate C — event retrieval

Bounded historical log probes must succeed for:
- Lido `WithdrawalRequested(uint256,address,address,uint256,uint256)`;
- Lido `WithdrawalsFinalized(uint256,uint256,uint256,uint256,uint256)`;
- Lido `WithdrawalClaimed(uint256,address,address,uint256)`;
- stETH `TokenRebased(uint256,uint256,uint256,uint256,uint256,uint256,uint256)`;
- Curve `TokenExchange(address,int128,uint256,int128,uint256)`.

Probe windows are source-only samples around early and late frozen-period blocks. Event payload values are not to be printed. Record only event counts and content hashes sufficient to demonstrate reproducibility.

## Gate D — timestamp / identifier integrity

PASS only if:
- UTC target timestamps can be mapped deterministically to the first block at/after target time using historical block headers;
- returned logs expose block number/hash, transaction hash and log index;
- duplicate identifiers are zero inside each bounded probe;
- every returned log block lies inside the requested block range.

## Gate E — protected-period firewall

The probe must reject any requested target timestamp after `2024-12-31T23:59:59Z`.

No 2025/2026 block search, logs, state call, market price, return or PnL request is permitted.

## Gate F — source-sample feasibility

Later Discovery is defined on 597 fixed daily 12:00 UTC snapshots over 2023-05-15 through 2024-12-31. Source feasibility requires historical state access on both edge periods and event/state identifiers sufficient to reconstruct those snapshots.

This gate does not compute the predictor, does not enumerate profitable signals, and does not estimate performance.

## Terminal rule

`SOURCE_DATA_PASS` requires A+B+C+D+E+F all PASS on at least one reproducible public archival transport route.

If no transport route passes, classify the most specific non-economic failure. Do not inspect outcomes to rescue the source.
