# BASE-KEEPER-001 — final fast economic/source verdict 2026-10-13

**Decision: SOURCE_BLOCKED / NO EXECUTABLE NET EDGE DEMONSTRATED / STOP ALL ENGINEERING.**

We tested a genuine economically distinct onchain trading mechanism: direct primary Aave V3 liquidation on Base, earning borrower-funded collateral liquidation bonus. The mechanism is NOT a proof of personal profit. Liquidator competition, gas, slippage, private MEV and recapture all remain material.

### Preregistered source attempt 1
Official Base public RPC `https://mainnet.base.org` (chainId accepted; tip accepted).
Frozen 24,000-block scan with 1,500-block chunk; **first `eth_getLogs` returned HTTPError**. Zero complete blocks and zero liquidation observations. Run 38402358388 / artifact 11815492270.
`SOURCE_BLOCKED`, rather than SOURCE_EMPTY or NO_EDGE.

### Separately frozen remediation attempt 2
PublicNode `https://base-rpc.publicnode.com`, same pool, topic, chunk size, cost and observation semantics. Source-only amendment frozen BEFORE V0.2 outcomes. ChainId and tip accepted, first `eth_getLogs` also returned HTTPError. Run 38402592577 / artifact 11815532602.
`SOURCE_BLOCKED`. No source-backed event count, liquidation-bonus calculation, liquidator concentration or realized profits exist.

Both workflows ran six synthetic ABI/gas regression tests PASS and uploaded a SOURCE_BLOCKED receipt. **CI SUCCESS means scientific classification test passed, not source or economic PASS.**

### Relevant public evidence
Aave protocol https://aave.com/blog/historical-liquidations (Feb 2026) documents aggregate history >310,000 liquidations / $4.65B repaid since inception across markets, and Chainlink SVR captured approx 73% of non-toxic liquidation MEV in supported Ethereum markets in first nine months. These are systemwide descriptive numbers NOT Base keeper opportunity/profitability and NOT a user profit estimate.
Aave official source https://www.aave.com/docs/aave-v3/overview says liquidation bonus per reserve, not fixed across assets.
Base official public RPC docs https://basehub.org/api-reference/rpc-overview/ acknowledge public rate limiting. PublicNode public endpoint documented at https://base.publicnode.com/.

### Conclusion
The idea is **not scientifically NO_EDGE**, but given no free reliable event source and strong specialist competition, the current low-capital/no-paid-data route is **NOT A DEPLOYABLE AUTOMATIC TRADING CANDIDATE**. Stop now; no paid infra, no bot code, no exchange API, no orders, no credentials. Do not add to Radar. Remain 0 active strategies.

### Engineering/economic lesson
Start with a named external payer (borrower's liquidation penalty), a measurable orderflow transfer, and the cheapest possible falsifier (public event/gas census). The experiment stopped immediately when both public sources failed — no weeks spent polishing an EXE. New materially different routes require fresh proposal; this exact transport path is closed.
