# RETH-NAV-DISLOCATION-001 — SOURCE TRANSPORT REMEDIATION V0.1A

Frozen: 2026-09-26
Parent: SOURCE_GATE_FREEZE_V0.1
Scope: TRANSPORT-ONLY remediation.

The first source-gate run (#36263467992) proved:
- current finalized rETH getExchangeRate() is readable;
- three canonical Uniswap V3 rETH/WETH pools are discoverable;
- current slot0/liquidity is readable;
- the selected PublicNode endpoint does not provide the historical state required by the frozen sentinel calls.

This remediation may change ONLY the public Ethereum JSON-RPC endpoint.

Frozen and unchanged:
- rETH contract address;
- WETH address;
- Uniswap V3 factory;
- fee tiers 100/500/3000/10000;
- sentinel blocks 18,000,000 / 20,000,000 / 22,000,000 / 24,000,000;
- current finalized-block requirement;
- historical block-pinned eth_call requirement;
- token-order verification;
- source PASS/BLOCKED criteria;
- outcome closure.

Ordered public/keyless transport candidates:
1. https://rpcfree.com/ethereum-rpc
2. https://ethereum-rpc.blockreq.com/v1/rpc/public
3. https://rpc-eth.blockmachine.io
4. https://lb.routeme.sh/rpc/evm/1

No account creation, API key, paid archive service, changed sentinel, changed pool, changed gate, fallback-to-latest, or post-result source selection is authorized.

Interpretation:
- Any endpoint that satisfies the already-frozen SOURCE PASS criteria may establish historical-source feasibility.
- Individual endpoint failure is TECHNICAL_SOURCE_TRANSPORT_BLOCKED, not mechanism failure.
- If all four fail, close this exact source route as PUBLIC_FREE_ARCHIVE_SOURCE_BLOCKED.
- No returns, direction, thresholds, horizon, PnL, or trading may be opened.
