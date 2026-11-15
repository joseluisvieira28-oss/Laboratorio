# CBBTC-ETH-MINT-BURN-FLOW-001 — SUPPLY BLOCKHASH BINDING ADDENDUM V0.1B

Frozen: 2026-09-27
Parent: SUPPLY_NORMALIZATION_ADDENDUM_V0.1A

Scope: provenance strengthening only.

The frozen supply normalization already requires historical totalSupply() at:
- start_block - 1;
- exact census end block.

This addendum strengthens the transport binding:

1. resolve canonical block number/hash/timestamp through the header RPC;
2. execute historical totalSupply() on the archive RPC using EIP-1898:
   {"blockHash": H, "requireCanonical": true};
3. retain both anchor block hashes in the census receipt;
4. no block-number-only fallback is permitted for the two supply anchors.

The supply values, census boundaries, reconciliation equality rule and predictor remain unchanged.

If blockHash-pinned archive state is unavailable, the census is blocked rather than silently falling back.

No market outcome, 2026 data, PnL or promotion credit is opened.
