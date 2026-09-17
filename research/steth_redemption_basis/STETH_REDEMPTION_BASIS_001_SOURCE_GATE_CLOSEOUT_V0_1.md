# STETH-REDEMPTION-BASIS-001 — SOURCE GATE CLOSEOUT V0.1

Date: 2026-09-17  
Branch: `empty-territory-hunt-v0.1`  
Stage: SOURCE-ONLY / OUTCOME-BLIND

## Verdict

**SOURCE_ACQUISITION_TECHNICAL_FAILURE**

This is **not** `NO_EDGE`, `DISCOVERY_FAIL`, or an economic-performance verdict.

No Discovery authority is opened by this closeout.

## Runs

### Initial public-RPC probe
- GitHub Actions run: `35209309821`
- Result: `SOURCE_ACQUISITION_TECHNICAL_FAILURE`
- Public transports attempted: 3
- Failure classes: deployment-receipt unavailable on two routes; HTTP 403 on one route.

### Transport-only remediation probe
- GitHub Actions run: `35209517522`
- Workflow-head commit: `a965e64738219f92616dc2f3bbedc2c3cb1c7b9c`
- Artifact id: `10491423396`
- Artifact digest: `sha256:404fe4968fc15ab85f1e17c3754b7b890dce64f0b506d9acb96974193b4bdc24`
- Result: `SOURCE_ACQUISITION_TECHNICAL_FAILURE`

Provider-level source-access failures recorded by the receipt:
- `ethereum-rpc.publicnode.com`: WithdrawalQueue deployment receipt unavailable;
- `eth.llamarpc.com`: HTTP 403;
- `rpc.flashbots.net`: WithdrawalQueue deployment receipt unavailable;
- `eth.drpc.org`: historical RPC call returned `execution reverted`;
- `1rpc.io`: WithdrawalQueue deployment receipt unavailable;
- `rpc.mevblocker.io`: historical RPC call returned `execution reverted`;
- `eth-mainnet.public.blastapi.io`: historical RPC call returned `execution reverted`.

The official Lido deployment manifest independently identifies the frozen WithdrawalQueue proxy and deploy transaction. The gate nevertheless requires the historical RPC route itself to reproduce all frozen provenance/state requirements, so the lab remains fail-closed.

## Safety receipt

Both source-probe receipts state:
- `price_outcomes_opened=false`
- `returns_opened=false`
- `pnl_opened=false`
- protected source end = `2024-12-31T23:59:59Z`
- max permitted Ethereum block = `21525890`

No 2025/2026 source traversal is authorized by this lab.

## Operational status

`STETH-REDEMPTION-BASIS-001` remains a **HIGH-INTEREST RESEARCH TARGET / SOURCE-BLOCKED**, not an edge.

Permitted next work is limited to legitimate historical-source access/provenance remediation that does not change the frozen economic definition, predictor, execution, costs, source window, or promotion gates.

A later source rerun requires a route capable of reproducing historical Ethereum contract receipts, bytecode, logs and `eth_call` state for the frozen 2023-05-15 through 2024-12-31 window. If such access requires credentials, the lab stops until those credentials/access are explicitly available.
