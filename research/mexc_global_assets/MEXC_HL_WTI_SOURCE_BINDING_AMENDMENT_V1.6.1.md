# MEXC ↔ HYPERLIQUID WTI — SOURCE BINDING AMENDMENT V1.6.1

Date: 2026-10-04
Status: PRE-OUTCOME IDENTITY CORRECTION / OUTCOMES STILL CLOSED

## V1.6 result

Run 37202254864 returned:
`SOURCE_BLOCKED_HYPERLIQUID_WTI_TARGETED_PROOF`

The scanner opened zero historical outcomes.

It found several semantically plausible oil assets, but only one had a live order book and a contemporaneous price matching MEXC WTI:

`xyz:CL`

Captured source-only snapshot:
- MEXC `USOIL_USDT` index: 91.31
- Hyperliquid `xyz:CL` best bid/ask: 91.238 / 91.240
- Hyperliquid mid: 91.239
- MEXC index vs Hyperliquid mid: +7.78176 bps
- Hyperliquid max leverage metadata: 20x

## Independent identity resolution

Current independent public references identify the trade.xyz / Hyperliquid `CL` market as Crude Oil (WTI).

Therefore the source correction is:

`MEXC USOIL_USDT / OIL(WTI) -> Hyperliquid xyz:CL / Crude Oil (WTI)`

This amendment does not inspect historical returns and does not authorize a trading strategy.

## Targeted PASS proof

V1.6.1 must verify from live public/no-auth endpoints:

1. `xyz:CL` exists in the `xyz` HIP-3 universe;
2. it has a live public BBO;
3. MEXC `USOIL_USDT` still lists `HYPERLIQUID` in `indexOrigin`;
4. MEXC WTI index and `xyz:CL` mid differ by less than 250 bps;
5. zero historical outcomes are opened.

PASS verdict:
`HYPERLIQUID_WTI_SOURCE_PASS__XYZ_CL`

A PASS authorizes only a separate pre-outcome scientific freeze.
