# MEXC ↔ HYPERLIQUID NAS100 — SOURCE GATE V0.5

Date: 2026-10-04
Status: SOURCE-ONLY / OUTCOMES CLOSED / RESEARCH-ONLY

## Trigger

MEXC public `contract/detail` for `NAS100_USDT` reports:

- `indexOrigin=["HYPERLIQUID"]`
- `apiAllowed=true`
- `isZeroFeeSymbol=true`

This creates a source-binding question independent of any trading outcome.

## Mission

Identify the exact public Hyperliquid perp whose price semantics and live scale plausibly feed the MEXC NAS100 index.

Candidate aliases may include:
- NAS100
- US100
- USTECH
- NDX
- NASDAQ / NASDAQ100
- TECH100

## Allowed

Public/no-auth:
- MEXC Futures market endpoints;
- Hyperliquid `/info` metadata;
- public Hyperliquid L2/BBO and asset context.

## Prohibited

- historical return/outcome scoring;
- lead/lag testing;
- API keys;
- account/wallet/private reads;
- orders;
- mutation;
- live trading;
- choosing a source candidate because it later produces better returns.

## PASS rule

`HYPERLIQUID_NAS100_SOURCE_PASS` requires a unique candidate whose:
1. semantic identity is defensible as Nasdaq-100 / US tech-100;
2. public live market data is available;
3. numerical scale is consistent with the contemporaneous MEXC NAS100 index;
4. source identity is materially less ambiguous than alternatives.

If two or more candidates remain equally plausible:
`SOURCE_BLOCKED_HYPERLIQUID_NAS100_IDENTITY_AMBIGUOUS`.

Even on PASS, outcomes remain CLOSED until a separate pre-outcome freeze is committed.
