# ETH-BLOCKSPACE-STATE-TRANSITION-001 — SOURCE TRANSPORT AMENDMENT V0.1A

Date: 2026-09-27
Status: FROZEN BEFORE ANY SUCCESSOR MARKET OUTCOME ACCESS

## Scope
This amendment changes only source transport resilience. It does not change the signal, state definition, sampling schedule, warmup length, market target, direction, horizon, costs, forward boundary or adjudication.

## Qualified provider set
Primary/audit providers already source-schema qualified:
- https://eth.drpc.org
- https://rpc.flashbots.net

Additional public read-only transport fallback:
- https://public.1rpc.io/eth

The fallback may be used only when a primary provider fails or rate-limits. Returned blocks must satisfy the exact existing header schema and block-number identity checks.

## Cross-provider identity
At every predeclared audit point, two independently returned copies of the exact same block height must agree on block hash and timestamp. Provider choice may vary solely for transport availability.

## Reason
Two unchanged warmup attempts failed before collecting any samples with HTTP 429. No market prices, returns or PnL were opened. The failure is classified TECHNICAL_TRANSPORT_BLOCKED, not scientific evidence.

## Invariants
No sampling-density reduction.
No replacement of missing blocks with interpolation.
No protected parent holdout access.
No economic outcome access before the frozen forward boundary.
No post-outcome tuning.
