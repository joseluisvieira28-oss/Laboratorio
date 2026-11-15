# CBBTC-ETH-MINT-BURN-FLOW-001 — FULL CENSUS RPC TIMEOUT REMEDIATION V0.1G

Frozen: 2026-09-27
Parent: RPC_TIMEOUT_TRANSPORT_REMEDIATION_V0.1F
Scope: TRANSPORT ONLY — source gate + full outcome-blind census.

## Trigger

V0.1F source-gate remediation was prepared after the prior run stalled pre-Gate-1.
Before V0.1F received a runner, static audit found the downstream full 2024-09-12 through 2025-12-31 census still used network calls without explicit HTTP timeouts.

V0.1G supersedes the queued V0.1F before execution.

## Unchanged science

UNCHANGED:
- cbBTC Ethereum contract;
- zero-address Transfer mint/burn semantics;
- source windows;
- source PASS criteria;
- census start/end dates;
- exact UTC daily ledger;
- start/end totalSupply reconciliation;
- duplicate/decode/source error gates;
- supply-normalized predictor;
- calibration period and q10/q90;
- Discovery sample gate;
- frozen BTC outcome mechanism;
- 2026 firewall;
- no PnL / no live trading / no main merge.

## Transport hardening

For the full census only:
- timestamp-boundary block reads use raw eth_getBlockByNumber with explicit 30-second AbortSignal timeout;
- eth_getLogs uses raw JSON-RPC with explicit 30-second timeout to the SAME primary PublicNode endpoint;
- log response fields are normalized to the exact internal shape expected by the frozen decoder;
- batched block-header reads use the same endpoint with explicit 30-second timeout;
- EIP-1898 totalSupply archive calls use the SAME BlockMachine endpoint through raw JSON-RPC with explicit 30-second timeout;
- existing retry/backoff and exact midpoint splitting remain unchanged.

No endpoint, block, day, event or gate substitution is authorized.

## Run identity

V0.1G uses the existing single-run chain and same concurrency group.
The newer run supersedes queued V0.1F before any V0.1F scientific gate executes.

Promotion credit = 0.
