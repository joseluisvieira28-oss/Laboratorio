# CCTP V1 HISTORICAL TRANSPORT SMOKE FREEZE V0.1

Date: 2026-09-24
Purpose: isolate historical RPC transport from full route-pairing logic.
No market outcomes.

Independent public documentation exposes historical V1 event examples:
- Avalanche TokenMessenger DepositForBurn at block 34152753, 2023-08-20.
- Ethereum TokenMessenger MintAndWithdraw at block 18433832, 2023-10-26.

These blocks are used only as positive source fixtures. They do not select a market outcome or an eventual trading signal.

PASS requires:
- Avalanche public RPC returns >=1 matching DepositForBurn log at exact block 34152753 from the frozen V1 TokenMessenger.
- Ethereum public RPC returns >=1 matching MintAndWithdraw log at exact block 18433832 from the frozen V1 TokenMessenger.
- returned tx/log evidence is hashed and persisted.

A mismatch is SOURCE_TRANSPORT_OR_FIXTURE_FAILURE, never NO_EDGE.
