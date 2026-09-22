# DEFI-LIQUIDATION-SHOCK-001 — KAMINO LENDING-MARKET INDEX REDUCTION FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Test whether indexing the historically explicit Kamino `lending_market` account can reduce official-RPC transport density versus indexing the global Kamino program ID, without changing the frozen liquidation event definition.

## Historical account authority

Official Kamino `klend` source commit:
`57074f4599a36ab0b433a71599b206c73efe1fd7`
dated 2023-11-17.

For `LiquidateObligationAndRedeemReserveCollateral`, the frozen historical account order begins:

0. liquidator
1. obligation
2. lending_market
3. lending_market_authority
4. repay_reserve
...

The event discriminator remains `b1479abce2854a37`.

## Allowed smoke audit

Use only the already-open 16 successful corrected Kamino smoke signatures from 2024-12-15.

For each signature:
1. fetch official public Solana `getTransaction`;
2. locate the exact Kamino instruction whose data begins with the frozen discriminator;
3. require outer instruction and compatible account ordering;
4. extract account index 2 only as `lending_market`;
5. count distinct lending markets across the 16 known events.

This is source topology analysis, not market/economic outcome analysis.

## Next routing

For each observed market, a separate feasibility probe may call official `getSignaturesForAddress` using the same fixed 2024-12-15 upper anchor and compare historical span per 1000 signatures against the already measured program-global span of 2277 seconds.

No observed market may be assumed to be historically exhaustive merely because it appears in the smoke. Historical market coverage must be separately established before any first-success boundary can be accepted.

## Firewall

No prices, returns, PnL, direction, amount-based filtering, protocol switching, trading, orders, wallets, exchange mutation, paid data, 2025/2026 market outcomes, or merge to main.
