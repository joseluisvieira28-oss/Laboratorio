# CCTP V1 HISTORICAL TRANSPORT REMEDIATION V0.3

Date: 2026-09-24
Stage: SOURCE TRANSPORT ONLY

Prior results:
- V0.1 Avalanche official RPC: PASS; Ethereum PublicNode: HTTP 403.
- V0.2 Avalanche official RPC: PASS; Ethereum dRPC: HTTP 400.

V0.3 changes only Ethereum transport:
- to: https://ethereum-rpc.blockreq.com/v1/rpc/public

BlockReq publicly identifies its Ethereum Mainnet public RPC as archive-capable and no-key.

Unchanged:
- Ethereum block 18433832;
- V1 TokenMessenger 0xbd3fa81b58ba92a82136038b25adec7066af3155;
- MintAndWithdraw topic;
- Avalanche exact fixture;
- no market outcomes;
- no 2025/2026 access.

Stop rule:
If V0.3 cannot retrieve the frozen Ethereum exact-block fixture, classify the free Ethereum historical RPC path SOURCE_ACCESS_BLOCKED for this attack. Do not rotate further providers under this source-gate lineage.
