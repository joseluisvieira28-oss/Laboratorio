# MEXC ↔ HYPERLIQUID WTI — SOURCE GATE V1.6

Date: 2026-10-04
Status: SOURCE-ONLY / OUTCOMES CLOSED

## Motivation

Current MEXC public metadata for `USOIL_USDT` explicitly lists `HYPERLIQUID` among its index origins.

V1.6 asks only whether an exact public Hyperliquid WTI/oil perpetual can be bound defensibly to MEXC `USOIL_USDT`.

No historical return or lead/lag outcome may be opened in this gate.

## Allowed

Public/no-auth only:
- Hyperliquid `perpDexs`
- Hyperliquid per-dex `meta`
- Hyperliquid `metaAndAssetCtxs`
- Hyperliquid `l2Book`
- MEXC public contract detail and live index price

## Candidate identity

The scanner may recognize only semantically explicit WTI/oil identities:
- WTI
- USOIL
- crude/oil tokens with a unique live price matching MEXC WTI
- CL only if the surrounding asset metadata/source context makes crude-oil identity unique.

A similar live price alone is insufficient.

## PASS requirements

`HYPERLIQUID_WTI_SOURCE_PASS` requires:
1. MEXC exact `USOIL_USDT`;
2. MEXC indexOrigin contains HYPERLIQUID;
3. one unique strong Hyperliquid WTI/oil candidate;
4. public live BBO;
5. price scale within 250 bps of contemporaneous MEXC WTI index;
6. zero historical outcomes opened.

PASS authorizes only a new pre-outcome freeze.
