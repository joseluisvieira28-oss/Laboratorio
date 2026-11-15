# LCOD BORROW-EVENT TRANSPORT REMEDIATION V0.2

Frozen: 2026-09-25
Science change: NONE
Outcomes: CLOSED

## What failed

The V0.1 population gate sent one very broad SQD query:
- 13 lending Spokes;
- Borrow topic0;
- from Ethereum genesis through current head.

It returned zero Borrow logs.

That result is known to be a transport/query-shape failure, not an absence of
Borrow events:
- an exact frozen fixture at block 25,398,769 on BLUECHIP_SPOKE returns the same
  Borrow event through both Blast archive RPC and SQD;
- the transaction hash and topic0 match exactly across both transports.

Therefore the production-debt invariant remains unchanged.

## V0.2 remediation

1. Discover each pinned Spoke's first code block by binary-searching
   eth_getCode against Blast archive RPC.
2. Query Borrow history per Spoke from its deployment block to finalized N.
3. Use bounded block chunks, never one all-history / all-address mega-query.
4. Record per-Spoke chunk counts, raw response hashes and any unresolved range.
5. Deduplicate by (Spoke,user).
6. Apply the unchanged current-MCP contradiction check.
7. Apply the unchanged block-N active-debt filter.

## Fail-closed

No missing chunk may be skipped.
No deployment block may be guessed.
No 13-Spoke subset may be accepted as complete.
No MCP pair missing from event history may be imputed.
No market/liquidation outcome may be opened.

The scientific PASS rule from V0.1 remains unchanged.
