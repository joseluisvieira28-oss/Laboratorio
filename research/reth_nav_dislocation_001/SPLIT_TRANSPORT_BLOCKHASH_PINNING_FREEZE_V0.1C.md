# RETH-NAV-DISLOCATION-001 — SPLIT TRANSPORT + BLOCKHASH PINNING FREEZE V0.1C

Frozen: 2026-09-26
Scope: TRANSPORT / PROVENANCE ONLY.
Scientific universe, blocks, pool, predictor and gates remain unchanged.

## Motivation

The only public archive route that passed the frozen historical source gate, BlockMachine, exhibits a deterministic request-quota pattern under repeated direct calls.

The scientific state requires four contract reads plus block metadata at each exact block. Those four reads are already proven candidates for Multicall3 compression.

## Split transport

Header / block metadata transport:
https://ethereum-rpc.publicnode.com

Archive state transport:
https://rpc-eth.blockmachine.io

Canonical Multicall3:
0xcA11bde05977b3631167028862bE2a173976CA11

PublicNode is used ONLY for block number/hash/timestamp.
It is not an authority for historical contract state.

BlockMachine remains the historical state authority.

## Strong block binding

For every census point:
1. resolve block N on the header transport;
2. retain exact block hash H and timestamp;
3. execute the Multicall3 historical eth_call on BlockMachine using EIP-1898:
   {"blockHash": H, "requireCanonical": true}

No number-only fallback is permitted in the census.

If EIP-1898 blockHash historical calls are unsupported, the split transport is BLOCKED.

## Mandatory equivalence

At blocks:
20,000,000
22,000,000
24,000,000

require ALL:
- PublicNode block hash equals BlockMachine block hash;
- four direct BlockMachine calls by block number succeed;
- one Multicall3 call by block number succeeds;
- one Multicall3 call by EIP-1898 blockHash succeeds;
- direct return bytes equal Multicall-by-number return bytes;
- Multicall-by-number return bytes equal Multicall-by-hash return bytes;
- all four subcalls match exactly.

That is 12 exact scientific-return comparisons plus 3 block-hash equality checks.

## Census transport

After equivalence PASS, each frozen census point uses:
- one header lookup on PublicNode;
- one Multicall3 historical state call on BlockMachine pinned by exact blockHash.

The original 556 blocks and 100% coverage gate are unchanged.

## Boundary

This remediation:
- does not alter any scientific field;
- does not alter q05/q95;
- does not open future outcomes;
- earns zero promotion credit.
