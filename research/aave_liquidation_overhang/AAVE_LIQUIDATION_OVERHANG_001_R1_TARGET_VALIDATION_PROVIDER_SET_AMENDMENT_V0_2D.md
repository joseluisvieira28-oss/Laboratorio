# AAVE-LIQUIDATION-OVERHANG-001 — R1 TARGET VALIDATION PROVIDER-SET AMENDMENT V0.2D

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE TARGET REVALIDATION / SOURCE-ONLY / OUTCOME-BLIND**

## Upstream immutable evidence

R1 Sharded Audit V0.2A:
- workflow run: `35375172202`
- head SHA: `d2d67f5bf55e7f91d3dae19cad640f99fbc82637`
- canonical audit artifact: `AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_2A`
- artifact ID: `10560482339`
- artifact digest: `sha256:172012d26dc6d4a6f0ea2a534f039f6ce2f73c2361e7975414067c25d6686f9b`
- deterministic validation targets: exactly **77**
- upstream classification: `RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE`
- upstream target failures: 77/77 `INSUFFICIENT_ARCHIVE_RPC_QUORUM`

No health factor, liquidation-overhang predictor, market prices, returns, PnL, or 2025/2026 market outcomes were opened.

## Source-feasibility lineage

V0.2B run `35377623033` proved one full-pass public archive endpoint:
- `https://eth-mainnet.public.blastapi.io`

V0.2C run `35377963528` proved two additional full-pass public archive endpoints:
- `https://rpc.mevblocker.io`
- `https://ethereum.blinklabs.xyz/`

V0.2C classification:
`ARCHIVE_RPC_PUBLIC_EXPANSION_PASS`

These three endpoints are the complete frozen V0.2D provider set. No endpoint may be added, removed, substituted or ranked after target results are observed.

## Exact authorized rerun

Rerun **only** the frozen target-validation stage against the exact 77 targets embedded in the immutable V0.2A artifact.

Before any RPC target call, the runner MUST:
1. bind to run `35375172202` and artifact `10560482339`;
2. require upstream target count = 77;
3. recompute the canonical target digest from
   `block|user|token|replayed_scaled_balance`;
4. require that recomputed digest equals the upstream receipt's `target_digest_sha256`;
5. require every upstream target failure to be `INSUFFICIENT_ARCHIVE_RPC_QUORUM`.

No borrower census, sample ranking, delta replay, reserve mapping, audit block, arithmetic or target may be recomputed or changed.

## Validation semantics — unchanged

For every frozen target:
- call `scaledBalanceOf(user)` at the exact frozen historical block;
- collect usable results from the frozen three-provider set;
- require at least **2** independent usable provider values;
- if <2 usable values: `INSUFFICIENT_ARCHIVE_RPC_QUORUM`;
- if usable values disagree: `ARCHIVE_RPC_DISAGREEMENT`;
- if the exact agreed value differs from the frozen replayed value: `REPLAY_MISMATCH`;
- only zero failures across all 77 targets yields `R1_AUDIT_PASS`.

Quorum remains 2. Equality remains exact. No majority vote, tolerance, dropping of targets, endpoint rescue, retry-based target selection or scientific-rule change is authorized.

## Safety

Still forbidden:
- health factor;
- liquidation overhang;
- market prices;
- future liquidation outcome;
- returns/PnL/PF/win-rate/drawdown;
- 2025/2026 market outcome access;
- wallets, orders, exchange mutation, alerts/webhooks;
- live trading;
- merge to main.

A V0.2D `R1_AUDIT_PASS` permits only the already-frozen reconstruction continuation. It does not establish an economic edge.
