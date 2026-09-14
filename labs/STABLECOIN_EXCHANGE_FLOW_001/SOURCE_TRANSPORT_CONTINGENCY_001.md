# STABLECOIN-EXCHANGE-FLOW-001 — SOURCE TRANSPORT CONTINGENCY 001

STATUS: **FROZEN PRE-OUTCOME**

This file is a technical contingency only. It changes no address, source date, balance definition, net-flow arithmetic, hypothesis, direction, outcome timing, cost or statistical rule.

Primary full source build remains dRPC (`https://eth.drpc.org`) with MEV Blocker independent QA.

A source-only probe performed before any BTC outcome access showed that MEV Blocker accepts a nine-call historical `eth_call` JSON-RPC batch for the frozen basket (`MEV_BATCH_PASS`).

If and only if the primary full dRPC build ends in a transport/runtime failure or timeout (not a semantic/data mismatch), a remediation run may:

1. use MEV Blocker batched `balanceOf()` as the transport for the exact same 780 frozen boundary blocks;
2. preserve the same integer USDT balances and net-flow arithmetic;
3. independently reconcile the prospectively fixed QA subset against dRPC individual calls;
4. remain source-only and keep all BTC outcomes closed;
5. classify any cross-provider state mismatch as `DATA_FAILURE`.

This contingency may not be invoked to alter source values after seeing BTC outcomes.
