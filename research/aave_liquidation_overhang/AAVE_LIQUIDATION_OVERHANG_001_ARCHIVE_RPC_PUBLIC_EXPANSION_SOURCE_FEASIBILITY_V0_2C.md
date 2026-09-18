# AAVE-LIQUIDATION-OVERHANG-001 — ARCHIVE RPC PUBLIC EXPANSION SOURCE FEASIBILITY V0.2C

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE NETWORK PROBE / SOURCE-ONLY / OUTCOME-BLIND**

## Lineage

V0.2B tested seven prospectively frozen public endpoints.
Result: `ARCHIVE_RPC_REPLACEMENT_SOURCE_INSUFFICIENT`.

Exactly one endpoint passed all four historical single calls plus JSON-RPC batch:
`https://eth-mainnet.public.blastapi.io`.

No R1 scaled-balance target calls were made in V0.2B.

## Purpose

Test the remaining public Ethereum RPC endpoints from the independently enumerated public-endpoint list available before this V0.2C execution.

No endpoint may be added after this file is committed.

## Frozen candidate endpoints

1. https://eth.leorpc.com/?api_key=FREE
2. https://ethereum-rpc.polkachu.com
3. https://g.w.lavanet.xyz:443/gateway/eth/rpc-http/f7ee0000000000000000000000000000
4. https://eth-mainnet-public.unifra.io
5. https://api.blockeden.xyz/eth/67nCBdZQSH9z3YqDDjdm
6. https://eth.rpc.hypersync.xyz/
7. https://eth.rpc.thirdweb.com/
8. https://eth.croswap.com/rpc
9. https://cloudflare-eth.com
10. https://rpc.mevblocker.io
11. https://eth.meowrpc.com
12. https://ethereum.blinklabs.xyz/
13. https://api.edennetwork.io/v1/rocket
14. https://ethereum-api.flare.network/
15. https://api.noderpc.xyz/rpc-mainnet/public
16. https://public-eth.nownodes.io/

## Frozen capability call

Same harmless V0.2B call only:
USDC `decimals()` (`0x313ce567`).

Historical blocks:
- 17,748,972
- 19,007,945
- 20,266,917
- 21,525,890

Returned data remain opaque; persist only success/error, byte length and SHA-256.

## Per-endpoint PASS

An endpoint passes only if:
- all 4 single historical `eth_call` requests return non-error hex results;
- one JSON-RPC batch with all 4 calls returns a list;
- all 4 batch items succeed;
- opaque single and batch result hashes agree for every block;
- no authenticated credential supplied by the user is required.

## Overall PASS

`ARCHIVE_RPC_PUBLIC_EXPANSION_PASS` requires at least **2** V0.2C endpoints to pass.

Together with the already-proven Blast endpoint from V0.2B, this would establish at least 3 independently reachable archive-capable providers before target validation.

If fewer than 2 pass:
`ARCHIVE_RPC_PUBLIC_EXPANSION_INSUFFICIENT`.

## Safety

No `scaledBalanceOf` target calls.
No health factor.
No liquidation overhang.
No market prices.
No returns/PnL.
No 2025/2026 market data.
No orders, wallets, exchange mutation, alerts/webhooks.
No merge to main.
