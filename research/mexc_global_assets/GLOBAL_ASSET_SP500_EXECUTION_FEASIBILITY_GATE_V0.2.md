# GLOBAL-ASSET-SP500-BASIS-001 — EXECUTION FEASIBILITY SOURCE GATE V0.2

Date: 2026-10-04
Status: SCIENTIFIC SIGNAL SURVIVES / STANDARD MEXC API EXECUTION FEE-BLOCKED

## Scientific input

Untouched September holdout:
- N = 654
- mean gross = +0.5177567737 bps per signal
- win rate = 54.4343%
- one-sided exact p = 0.0128735
- both chronological halves positive.

## Public execution evidence

The public MEXC contract-detail payload for `SPX500_USDT` reports:
- `apiAllowed=true`
- `isZeroFeeSymbol=true`
- `makerFeeRate=0`
- `takerFeeRate=0`

These fields describe public symbol metadata and must not be assumed to be the fee charged to authenticated API orders.

MEXC separately published an API Futures fee schedule effective 2026-06-01:
- API maker: 0.06% = 6 bps per side;
- API taker: 0.08% = 8 bps per side;
- API fee schedule takes precedence over web/app promotional rates;
- stated scope: all Futures pairs except Innovation Zone pairs.

The MEXC public SP500 contract page does not expose a concrete current maker/taker fee in the unauthenticated page.

## Standard API fee floor vs observed gross edge

Ignoring spread, slippage and funding:

- maker entry + maker exit = 12 bps round-trip;
- maker + taker = 14 bps;
- taker + taker = 16 bps.

The September gross edge was only +0.5178 bps.

Therefore the standard published API tariff alone exceeds the measured gross edge by more than an order of magnitude.

## Verdicts

Scientific signal:
`REPLICATED_SIGNAL_SURVIVOR`

Standard automated MEXC API route:
`EXECUTION_FEE_BLOCKED_STANDARD_API`

Web/app zero-fee or account-specific route:
`UNPROVEN_ACCOUNT_ROUTE__NO_ASSUMPTION`

The signal is NOT declared dead scientifically.
The current standard API execution route is NOT economically viable under the published tariff.

No account read was used to obtain a special/VIP/user-specific fee. No order was placed.

## Research response

Do not lower scientific gates to rescue execution.

Instead search for:
- a materially larger cross-venue gross edge;
- a defensible lower-cost execution route;
- or a structurally different Global Asset family.

Any route-specific execution promotion requires exact fee/spread/slippage authority before live use.
