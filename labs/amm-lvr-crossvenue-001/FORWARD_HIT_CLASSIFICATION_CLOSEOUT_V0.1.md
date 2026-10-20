# AMM-LVR-CROSSVENUE-001 — FORWARD HIT CLASSIFICATION CLOSEOUT V0.1

**Source hit set:** FORWARD_OBSERVABILITY_V0.2 / run 35821153542  
**Classifier run:** 35821948072  
**Artifact:** 10733292837  
**Artifact digest:** sha256:226ac84367de1919f28980f07a3e65a3bd78636c80f43cf62f6aa3a2d81da288

## Frozen population

17 registry touches were frozen before classification:
- Wintermute: 14
- Shen: 3

These were never assumed to be arbitrage.

## Classification result

All 17/17 were classified with successful current debug traces and zero classifier errors.

- 6 = FROZEN_MVE_DEX_ACTIVITY_OBSERVED
- 4 = UNISWAP_V3_ACTIVITY_OUTSIDE_FROZEN_MVE
- 7 = REGISTRY_TOUCH_NO_VALIDATED_UNISWAP_V3_SWAP
- 0 = CEX-DEX ARBITRAGE CONFIRMED

All six exact-MVE DEX activity observations were Wintermute transactions.

Uniswap V3 swaps were validated by:
1. canonical Swap event topic in the transaction receipt;
2. token0/token1/fee reads from the log-emitting contract;
3. exact pool identity returned by the canonical Uniswap V3 Factory.

## Builder/inclusion evidence

Current debug traces were available for 17/17 transactions through the no-key dRPC route.

11/17 transactions contained a positive direct native-value transfer to the block fee recipient in addition to the priority fee.

Observable builder payment was defined, consistently with the published CEX-DEX paper methodology, as:
priority payment + direct fee-recipient transfer.

This establishes that direct builder/fee-recipient transfer is an empirically observable and nonzero cost layer in the current searcher environment. It does NOT yet provide a complete cost model for our own hypothetical transaction.

## Scientific boundary

No CEX hedge leg was observed for these 17 transactions.

Therefore:
- DEX activity is proven for six exact-MVE touches;
- builder-payment observability is proven;
- CEX-DEX arbitrage is **not** confirmed by this classifier;
- no extracted-value or PnL claim is made;
- no promotion credit is created.

Next action remains the prospectively frozen read-only forward economic engine.
