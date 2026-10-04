# BITGET MAKER MICROSTRUCTURE — SOURCE GATE V0.1

Date: 2026-10-05
Status: SOURCE-ONLY / PRE-MICROSTRUCTURE-OUTCOME

Parent scientific authority:
- Binance ↔ Bitget stock lead-lag V0.1
- run 37239207816
- family artifact SHA256: 8ff31989d819783091bccac08f73936cfd7c942f19c23e02205c8c51d0171358
- verdict: MAKER_ONLY_FEE_SURVIVORS_FOUND__FILL_MODEL_REQUIRED

Frozen candidate set:
- HOODUSDT
- COINUSDT
- ARMUSDT
- AAPLUSDT

All four candidates are carried forward. No candidate may be removed based on microstructure outcomes.

Burned source-verification date:
2026-09-16

Source-only objectives:
1. Verify public Bitget historical transaction transport for each candidate using the public futures market fills-history endpoint.
2. Discover/verify Bitget's official futures historical depth/order-book download surface.
3. Record schemas, HTTP status, row counts, timestamp coverage and immutable hashes only.

Forbidden at this stage:
- no passive fill classification;
- no queue simulation;
- no signal/outcome join;
- no PnL;
- no execution-rule tuning;
- no private endpoints or account reads;
- no orders, wallets, exchange mutation or live trading.

A separate pre-outcome execution-model freeze is mandatory before any historical depth/trade data are joined to signal times.
