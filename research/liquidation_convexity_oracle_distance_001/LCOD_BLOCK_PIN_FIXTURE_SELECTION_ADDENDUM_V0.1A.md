# LCOD BLOCK-PIN FIXTURE DETERMINISTIC SELECTION ADDENDUM V0.1A

Frozen: 2026-09-24
Parent: LCOD_BLOCK_PIN_SNAPSHOT_GATE_FREEZE_V0.1.md
Outcomes: CLOSED

## Deterministic fixture selection

1. Aave MCP get_markets(version=v4, chainId=1).
2. Decode each opaque v4 reserveId as base64 text in the observed canonical
   form: chainId::spokeAddress::numericReserveId.
3. Keep valid Ethereum entries and sort by:
   spokeAddress lowercase, numericReserveId, opaque reserveId.
4. In that order call get_reserve_holders(side=borrow, limit=10, version=v4).
5. Within each non-empty holder page sort wallet addresses lexicographically.
6. Select the first candidate whose chosen spoke getUserAccountData at the
   frozen block N reports totalDebtValueRay > 0.

This uses source state only, not health-factor magnitude, price move, liquidation
outcome or market outcome.

## Block selection

N is Ethereum RPC finalized block at probe start.
No fallback to latest is allowed.

All contract reads used in the reconstruction and official comparison MUST
explicitly carry block_identifier=N.

## Integer reconstruction

Official pinned Aave V4 source commit:
40232a0a91150d8ee5cab42bd3ddd0baf4ffff9f

For every active collateral reserve:
- suppliedAssets = Spoke.getUserSuppliedAssets
- price = Oracle.getReservePrice
- collateralFactor = Spoke.getDynamicReserveConfig using the USER POSITION dynamicConfigKey
- collateralValue = suppliedAssets * price * 10^(18-decimals)
- weightedCollateral += collateralValue * collateralFactor

For every borrowed reserve:
- drawnShares = Spoke.getUserPosition.drawnShares
- drawnIndex = Hub.getAssetDrawnIndex(assetId)
- premiumDebtRay = Spoke.getUserPremiumDebtRay
- debtRay = drawnShares * drawnIndex + premiumDebtRay
- debtValueRay = debtRay * price * 10^(18-decimals)

Reconstructed health factor in WAD:
floor((weightedCollateral * 1e14) * 1e27 / totalDebtValueRay)

This mirrors the pinned V4 contract path.

PASS tolerance remains relative error <= 5e-5.

No raw wallet address may be written to durable evidence.
