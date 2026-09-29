# CCTP V1 ETHEREUM ARCHIVE-DATALAKE REMEDIATION V0.4

Date: 2026-09-24
Stage: SOURCE TRANSPORT ONLY

## Why V0.4 is allowed

V0.1-V0.3 exhausted the prospectively bounded free historical RPC route:
- PublicNode: HTTP 403.
- dRPC: HTTP 400.
- BlockReq public: explicitly recent-block-only; archive requires registration.

The RPC route is now closed as SOURCE_ACCESS_BLOCKED.

V0.4 is a materially different source transport: SQD/Subsquid Ethereum archive data lake.
SQD documents historical EVM log filtering by contract address + topic0 and exact block ranges.

## Frozen fixture

Unchanged historical semantic fixture:
- Ethereum block 18433832
- CCTP V1 TokenMessenger 0xbd3fa81b58ba92a82136038b25adec7066af3155
- MintAndWithdraw topic 0x1b2a7ff080b8cb6ff436ce0372e399692bbfb6d4ae5766fd8d58a7b8cc6142e6

## Candidate archive routes

Try in fixed order:
1. current Portal dataset endpoint:
   https://portal.sqd.dev/datasets/ethereum-mainnet/stream
2. legacy documented v2 archive router:
   https://v2.archive.subsquid.io/network/eth-mainnet/<block>/worker

These are transport probes of the same immutable event fixture. No market outcome is involved.

## PASS

At least one SQD route must return >=1 exact log matching block, address and topic0.
The raw response is hashed and the selected route is recorded.

## STOP

If both fail, classify:
SOURCE_ACCESS_BLOCKED_FREE_ETHEREUM_ARCHIVE_DATALAKE

No additional free historical transport families are authorized under CCLM-001 without a new source-remediation authority.
