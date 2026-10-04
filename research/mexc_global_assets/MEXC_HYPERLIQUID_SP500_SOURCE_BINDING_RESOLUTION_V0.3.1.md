# MEXC ↔ HYPERLIQUID SP500 — SOURCE BINDING RESOLUTION V0.3.1

Date: 2026-10-04
Source-gate run: 37192085133
Artifact SHA256: `325f5e15e8a9ae70ca13b6be2b69e1e7b1f96e057d1542f7342611ab3fbffbfd`

## Initial verdict

The automated first-pass gate returned:

`SOURCE_BLOCKED_HYPERLIQUID_ASSET_IDENTITY_AMBIGUOUS`

This was a conservative source-only verdict. No historical outcomes or lead/lag performance were opened.

## Evidence captured before resolution

MEXC `SPX500_USDT` public contract metadata:
- `indexOrigin=["HYPERLIQUID"]`
- `apiAllowed=true`
- `isZeroFeeSymbol=true`

Hyperliquid public metadata scan:
- 11 perp DEXs;
- 533 perp assets;
- candidate `xyz:SP500` — exact SP500 token, 50x, live mid ~7731.3;
- candidate `km:US500` — no live BBO in the probe, mark ~750.97;
- candidate `mkts:US500` — live mid ~770.965;
- primary-dex `SPX` — live mid ~0.4462;
- other USA500 aliases with lower semantic specificity.

Contemporaneous MEXC SP500 index price:
- ~7719.6

The exact-name candidate `xyz:SP500` differed from the contemporaneous MEXC index by about -15.13 bps in the probe snapshot, while the other live semantic candidates were on different numerical scales.

## Identity rule

Source identity is resolved by source semantics and scale, NOT by future return performance.

The defensible binding is:

`MEXC SPX500_USDT index origin HYPERLIQUID -> Hyperliquid HIP-3 xyz:SP500`

Reasons:
1. MEXC explicitly declares Hyperliquid as the index origin.
2. Hyperliquid metadata exposes an exact `SP500` contract on DEX `xyz`.
3. `xyz:SP500` is uniquely on the same S&P-500 index-level numerical scale as the MEXC index.
4. The XYZ protocol is a HIP-3 DEX designed for equities, indices/ETFs and commodities.
5. Public Hyperliquid market data provides timestamped candles and L2/BBO for this exact coin.

## Resolved source verdict

`HYPERLIQUID_SP500_SOURCE_PASS__XYZ_SP500`

This is a SOURCE PASS only.

Historical lead/lag outcomes remain CLOSED until a separate pre-outcome rule freeze is committed.

No accounts, wallets, private endpoints, API keys, orders, exchange mutations or live trading were used or authorized.
