# CCTP V1 HISTORICAL TRANSPORT REMEDIATION V0.2

Date: 2026-09-24
Stage: SOURCE TRANSPORT ONLY

V0.1 result:
- Avalanche exact-block historical RPC: PASS.
- Ethereum exact-block via ethereum-rpc.publicnode.com: HTTP 403 from GitHub runner.

This is SOURCE TRANSPORT failure, not protocol/source-semantic failure.

V0.2 changes only Ethereum transport:
- from: https://ethereum-rpc.publicnode.com
- to: https://eth.drpc.org/

dRPC publicly documents this keyless Ethereum endpoint and archive-data support.

Unchanged:
- Ethereum block 18433832;
- V1 TokenMessenger 0xbd3fa81b58ba92a82136038b25adec7066af3155;
- MintAndWithdraw topic;
- Avalanche fixture;
- no market outcomes;
- no 2025/2026 access.
