# BASE KEEPER 001 — PUBLIC RPC source remediation V0.2 (before new observations)
Date 2026-10-13 UTC. Experimental market-science status: SOURCE_BLOCKED v0.1, not a strategy failure.
V0.1 workflow https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38402358388 produced SOURCE_BLOCKED at public Base RPC (HTTPError on first eth_getLogs query; 3 calls, zero complete coverage). Preserve V0.1 receipt, never retroactively call it PASS.

One final **source-only** transport remediation, no parameter optimization, no fee, signal or trading changes:
- Provider: https://base-rpc.publicnode.com (PublicNode official public Base RPC page https://base.publicnode.com/)
- Chain, Aave Pool, topic, 24,000 block frozen span, 1,500 block slices, 12 block safety lag, max 20 receipts, source validation all unchanged from V0.1.
- Separate full new current-time window; not an attempt to obtain a more favorable price sample, no economic outcomes calculated. No merging of V01 and V02 observations.
- One workflow invocation. If complete SOURCE_PASS, separately consider a *new* independent economic feasibility preregistration, without reconstructing profitability from these event counts.
- If SOURCE_BLOCKED, close as PUBLIC_SOURCE_UNAVAILABLE and stop source work; no paid API/keys/accounts.
- If SOURCE_EMPTY, close as ZERO_EVIDENCED_FREQUENCY.
- Public unauthenticated RPC only; one endpoint, do not switch during attempt.
- Never call a synthetic test PASS 'edge', never infer USD liquidation bonus from token integers or assume gas price alone captures private MEV tips.
- No orders, wallets, account access, exchange mutation, change to main or restored Radar.
