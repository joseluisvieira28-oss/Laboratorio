# MICROSTRUCTURE SCALPING LAB — COST GATE V0.1

Date: 2026-09-25
Status: PRE-OUTCOME ECONOMIC FREEZE

## Principle
A signal is irrelevant if its executable gross move cannot clear the venue-specific round-trip hurdle after fees, spread, slippage, adverse selection, latency and failed/partial fills.

## Published base/reference fees checked on 2026-09-25

### MEXC Futures API
Official update effective 2026-06-01:
- maker 0.06% = 6 bps per fill
- taker 0.08% = 8 bps per fill
- API fee schedule overrides web/app promotional rates

Fee-only round-trip:
- taker/taker: 16 bps
- maker/taker: 14 bps
- maker/maker: 12 bps

### Bybit perpetual/futures VIP 0 reference
Official base table:
- maker 0.0200% = 2 bps
- taker 0.0550% = 5.5 bps
Rates may vary by region/account.

Fee-only round-trip:
- taker/taker: 11 bps
- maker/taker: 7.5 bps
- maker/maker: 4 bps

### Binance USDS-M regular-user reference
Official fee calculation example states:
- maker 0.02% = 2 bps
- taker 0.05% = 5 bps
The fee page warns actual/current rates may differ and should be checked at execution time.

Fee-only round-trip reference:
- taker/taker: 10 bps
- maker/taker: 7 bps
- maker/maker: 4 bps

## Frozen economic rules
1. Report gross edge in bps.
2. Subtract entry fee + exit fee.
3. Subtract observed/estimated spread paid.
4. Apply slippage sensitivity.
5. Apply latency sensitivity.
6. Maker assumptions require a fill model and adverse-selection penalty; posting a limit order does NOT imply a fill.
7. No candidate can survive on fee rebates/promotions not proven available to the actual account/venue.
8. Any cross-venue historical discovery must be replicated on the intended execution venue before promotion.

## Immediate consequence
For MEXC API, a short-horizon taker/taker strategy needs >16 bps gross merely to pay fees. A credible target must clear materially more than 16 bps after spread/slippage/latency. Tiny 2–5 bps predictive moves are economically useless there.

This gate is frozen before any outcome analysis.
