# CBBTC-ETH-MINT-BURN-FLOW-001 — SOURCE TRANSPORT REMEDIATION V0.1A

Frozen: 2026-09-26
Parent: SOURCE_GATE_FREEZE_V0.1
Scope: transport-only remediation.

Initial run #36270469681:
- current symbol() = cbBTC;
- current decimals() = 8;
- fatal source transport error occurred before any fixed-window event census completed.

No source counts or price outcomes were opened.

## Split transport

Header + eth_getLogs authority:
https://ethereum-rpc.publicnode.com

Historical contract-code verification:
https://rpc-eth.blockmachine.io

Scientific source semantics remain identical:
- official Ethereum cbBTC contract;
- exact Transfer topic;
- exact zero-address mint/burn definition;
- exact fixed Window A and Window B;
- exact block boundaries resolved from Ethereum timestamps.

## Allowed change

Only historical eth_getCode is routed to the demonstrated public archive provider.

No change to:
- window dates;
- event topics;
- contract;
- network;
- PASS criteria;
- event counts;
- outcome closure.

If the rerun still fails, inspect the next exact transport blocker without altering scientific criteria.
