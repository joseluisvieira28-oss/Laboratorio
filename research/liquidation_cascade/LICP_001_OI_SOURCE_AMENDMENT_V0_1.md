# LICP-001 — OI SOURCE AMENDMENT V0.1

Date: 2026-09-26
Status: TECHNICAL SOURCE AMENDMENT BEFORE OUTCOMES

The first outcome-blind calibration run showed 177/177 attempted Binance USD-M OI REST calls failing from the GitHub runner.

No MEXC propagation outcomes had been opened and the trigger config remained UNFROZEN.

Therefore the OI context source is changed to the public Hyperliquid `metaAndAssetCtxs` info endpoint, which exposes current perpetual open interest without authentication.

Scope remains:
- BTC
- ETH
- SOL
- approximately 5-second polling

OI remains contextual only in trigger V0.1 and does not gate the trigger.

The second calibration window is extended from 5 to 10 minutes because the first window contained zero BTC/ETH/SOL liquidation events and was classified CALIBRATION_SPARSE.

No percentile rule, outcome horizon, fee assumption, or propagation logic is changed.
