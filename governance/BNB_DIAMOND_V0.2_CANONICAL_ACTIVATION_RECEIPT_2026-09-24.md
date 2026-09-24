# BNB DIAMOND V0.2 — CANONICAL ACTIVATION RECEIPT — 2026-09-24

Status: CODE_STAGED_CANONICAL__CI_REQUIRED_BEFORE_RENDER_DEPLOY

Canonical branch: crypto-edge-radar-postgres-v0.5
Atomic sidecar commit: 8346c0716edd661e13b063276bfe13bb5e08b955

Pre-activation live runtime facts:
- canonical deployed commit before sidecar: 627f595e80011de817bebd6fe45811066b2f9629
- health: OK
- evidence chain: verified 744 events via Postgres
- BNB eligible prospective events visible: 0
- BNB prospective clusters: 0
- BNB paper selections: 0
- BNB resolutions: 0
- BNB missed prospective observations: 0

Activation content:
- frozen BNB Diamond V0.2 measurement contract
- measurement-only public Binance Spot 1m sidecar
- parent-selection-only binding
- first-25 causal gate
- Diamond Board visibility
- parent reconciliation remains mandatory

Parent scientific rule unchanged:
LONG BNBBTC; <=60m clustering; one active trade; first 15m open strictly after signal; 24h hold; BASE20/STRESS30; no stop; no target; no leverage.

Safety:
no authenticated exchange API
no orders
no wallets
no exchange mutation
no capital
no automatic promotion
no main merge

Render deployment is forbidden until the canonical CI/soak triggered by this receipt passes.
