# MEXC ↔ HYPERLIQUID SP500 CROSS-VENUE — SOURCE GATE V0.3

Date: 2026-10-04
Status: SOURCE-ONLY / OUTCOMES CLOSED / RESEARCH-ONLY

## Trigger

The public MEXC `contract/detail` payload for `SPX500_USDT` captured in the successful V0.2 source gate reported:

- `apiAllowed=true`
- `isZeroFeeSymbol=true`
- `makerFeeRate=0`
- `takerFeeRate=0`
- `indexOrigin=["HYPERLIQUID"]`

The zero-fee fields are symbol metadata and MUST NOT be treated as authenticated API execution fees. MEXC separately publishes an API Futures fee schedule.

The `indexOrigin` field creates a new source-binding question: can a public Hyperliquid market-data stream be defensibly mapped to the MEXC SP500 index?

## Allowed

Public, unauthenticated market-data/source-discovery only:
- MEXC public Futures market endpoints;
- Hyperliquid public `/info` endpoint;
- Hyperliquid public WebSocket market-data feeds if needed.

## Prohibited

- historical directional outcome scoring;
- lead/lag outcome testing;
- private/account endpoints;
- wallet/address user-state reads;
- API keys;
- orders;
- trading;
- exchange mutation;
- live-trading authorization;
- parameter selection from outcomes.

## Source-gate questions

1. Enumerate all Hyperliquid perp DEXs.
2. Enumerate public perp metadata for each DEX.
3. Identify candidate assets whose semantic identity could plausibly represent the S&P 500 / SP500 / SPX500.
4. For any candidate, capture public `metaAndAssetCtxs` context and L2 book.
5. Capture contemporaneous MEXC SP500 index price.
6. Check only source identity/scale/timestamp plausibility. Do NOT calculate future returns or directional performance.

## PASS requirements

`HYPERLIQUID_SP500_SOURCE_PASS` requires ALL:
- a unique Hyperliquid asset candidate with defensible S&P 500 identity;
- public/no-auth market data available;
- live BBO/L2 or equivalent timestamped market data available;
- price scale consistent with the MEXC SP500 index at the source-probe instant;
- no account/wallet/private endpoint used.

If uniqueness or identity cannot be defended:
`SOURCE_BLOCKED_HYPERLIQUID_ASSET_IDENTITY`.

Even on PASS, historical outcomes stay CLOSED until a new pre-outcome lead/lag freeze is committed.
