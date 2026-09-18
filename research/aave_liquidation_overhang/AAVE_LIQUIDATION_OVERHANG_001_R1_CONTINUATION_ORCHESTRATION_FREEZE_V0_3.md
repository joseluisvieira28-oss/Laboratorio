# AAVE-LIQUIDATION-OVERHANG-001 — R1 CONTINUATION ORCHESTRATION FREEZE V0.3

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE V0.3 DOWNSTREAM SOURCE ACCESS / OUTCOME-BLIND**

## Lineage and closed prior path

Continuation V0.2 remains historically closed under its own authority because its exact pinned monolithic audit did not complete as `R1_AUDIT_PASS`. V0.3 does not rewrite that result.

Subsequent prospectively frozen technical remediation produced a new canonical audit chain without opening economic outcomes:

1. R1 Sharded Audit V0.2A — deterministic corpus and exact 77 validation targets.
2. Archive RPC Source Feasibility V0.2B — one full-pass archive provider.
3. Archive RPC Public Expansion V0.2C — two additional full-pass archive providers.
4. R1 Target Validation V0.2D — `R1_AUDIT_PASS`, 77/77 targets, quorum 2.
5. R1 Audit Reconciliation V0.2E — canonical `R1_AUDIT_PASS` receipt combining immutable V0.2A corpus with V0.2D target validation.

## Exact admissible audit

Only:
- run: `35378692311`
- artifact: `AAVE_R1_AUDIT_CANONICAL_V0_2E`
- artifact ID: `10561601020`
- artifact digest: `sha256:be88c486a5f6b3892bf909696710e4a191a15d2ac1b583e0be2c473c7941a004`
- classification: `R1_AUDIT_PASS`
- sample size: 16
- validation targets: 77
- validated targets: 77
- validation failures: 0
- target digest: `eb5a5e929ec7479989bdb5a4eabc478cce2404b443d67990b44a6b6a14483510`

## Frozen archive provider set for V0.3 historical state calls

Exactly:
1. `https://eth-mainnet.public.blastapi.io`
2. `https://rpc.mevblocker.io`
3. `https://ethereum.blinklabs.xyz/`

This set was fixed by V0.2B/V0.2C before R1 target results were reopened through it.

For the global-state/oracle historical-price validation:
- same exact audit blocks;
- same exact reserve universe;
- at least 2 independently usable provider values per target;
- all usable values must agree exactly;
- value must be strictly positive;
- no target, reserve, block or provider may be dropped after observation;
- no majority vote or tolerance is allowed.

## Downstream sequence

If and only if the exact V0.2E audit artifact passes the frozen gate:

1. exact global state/oracle gate using the frozen V0.3 archive provider set;
2. exactly eight reserve replay shards ids 0..7 using the existing frozen V0.2 semantics;
3. exact canonical aggregate using the V0.2E audit, canonical R0 bootstrap, all eight reserve shards and global-state receipt.

Only the aggregate may emit `RECONSTRUCTION_DATA_PASS`.

## Unchanged scientific contract

No change to:
- Ethereum mainnet;
- block envelope 16,490,000 .. 21,525,890 inclusive;
- 37-reserve universe;
- borrower identity/ranking/sample size 16;
- scaled-token Mint/Burn/BalanceTransfer semantics;
- ray arithmetic;
- audit blocks;
- reserve replay;
- eMode logic;
- provider/oracle transition logic;
- Aave oracle price validation semantics;
- quorum=2;
- exact equality;
- all ten Reconstruction Gate tests;
- protected-period firewall.

## Safety

Still forbidden:
- health factor;
- liquidation-overhang predictor;
- adverse-shock threshold;
- future liquidation outcomes;
- market-return prices;
- returns/PnL/PF/win-rate/drawdown;
- 2025/2026 market outcome access;
- live trading/orders/wallets/exchange mutation;
- alerts/webhooks;
- merge to main.

A V0.3 `RECONSTRUCTION_DATA_PASS` may authorize only the separately frozen next pre-Discovery stage. It does not authorize Discovery automatically.
