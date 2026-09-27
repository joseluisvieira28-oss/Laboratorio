# CBBTC-ETH-MINT-BURN-FLOW-001 — RPC TIMEOUT TRANSPORT REMEDIATION V0.1F

Frozen: 2026-09-27
Status: PREPARED ONLY — DO NOT TRIGGER WHILE RUN #36276732156 IS ACTIVE
Scope: transport timeout / response-shape normalization only.

## Trigger condition

Use this remediation only if the authoritative single-run #36276732156 terminates before a valid Gate-1 verdict because an RPC request hangs, times out, or otherwise fails at the transport layer.

Do NOT use it to rescue a scientifically evaluated SOURCE_BLOCKED result.

## Technical change only

Unchanged:
- cbBTC contract;
- two frozen source windows;
- timestamp boundaries;
- Transfer topic;
- zero-address mint/burn definition;
- exact block coverage;
- adaptive interval splitting;
- decode and duplicate rules;
- SOURCE_PASS criteria;
- no outcomes / no 2026 / no PnL.

Transport hardening:
- every raw eth_getBlockByNumber HTTP request gets an explicit 30-second timeout;
- every eth_getLogs HTTP request to the same frozen primary source gets an explicit 30-second timeout;
- raw JSON-RPC log fields are normalized to the exact shape previously supplied by ethers before decode;
- deterministic retry/backoff and exact midpoint splitting remain unchanged.

No endpoint change is authorized by this addendum.

## Governance

If #36276732156 completes with source_gate_evaluated=true, this remediation is not used.
If #36276732156 completes SOURCE_PASS, downstream frozen gates continue normally.
If #36276732156 completes evaluated SOURCE_BLOCKED, the exact lab closes with no rescue.

Promotion credit = 0.
