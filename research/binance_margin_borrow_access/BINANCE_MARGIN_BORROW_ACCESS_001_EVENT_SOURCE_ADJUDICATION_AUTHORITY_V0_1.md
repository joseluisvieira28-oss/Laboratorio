# BINANCE-MARGIN-BORROW-ACCESS-001 — EVENT SOURCE ADJUDICATION AUTHORITY V0.1

Date: 2026-09-17  
Status: **FROZEN / SOURCE-ONLY / OUTCOME-BLIND**  
Precondition: `SOURCE_CENSUS_PASS` from V0.4.

## Purpose

Convert the reproducible V0.4 structural source universe into an event-level, point-in-time candidate universe suitable for a later separately frozen Discovery protocol, while preserving the mechanism exactly as originally defined: relaxation of short-sale/hedging constraints when an already Binance-Spot-traded asset becomes newly borrowable on Binance Cross Margin.

## Still forbidden

No market prices, returns, basis, abnormal returns, borrow rates, borrow inventory, PnL, win rate, PF, drawdown, 2025/2026 scientific data, authenticated Binance account/API access, orders, wallets, alerts/webhooks, exchange mutation, live trading, or outcome-based filtering.

## Required event-level fields

For every source-census structural article that could describe new Cross Margin borrow access, recover before outcomes:

- canonical article code;
- official publish timestamp;
- exact asset symbol(s) explicitly described as newly borrowable on Cross Margin;
- event-information timestamp and explicit effective timestamp when stated;
- same-announcement Cross Margin pair addition flag;
- same-announcement Isolated Margin access/borrowing flag;
- same-announcement Spot listing/trading-start flag;
- same-announcement Convert/Earn/Buy Crypto/Futures/perpetual flag;
- direction semantic: ADD / REMOVE / OTHER;
- source evidence snippet/hash sufficient to audit the structural classification.

## Prospectively frozen structural eligibility

An event can survive to the prior-Spot proof stage only if:

1. direction is **ADD**;
2. official text explicitly states one or more new **borrowable assets on Cross Margin**;
3. the asset identity is unambiguous;
4. the same announcement does not inseparably introduce initial Spot trading for that asset.

Removal/delist notices are not adverse-price events for this hypothesis and are excluded structurally before outcomes.

An announcement that bundles Earn, Convert, Buy Crypto, Futures, Isolated Margin or new Cross Margin pairs is retained with explicit confound flags; those flags are not hidden or tuned later. Same-announcement initial Spot listing is prospectively `ACCESS_CONFOUND` and excluded from the clean mechanism universe.

## Prior-Spot proof

For each structurally surviving asset/event, a point-in-time official Binance source must establish that Spot trading/listing began strictly before the borrow-access information time.

Admissible proof:
- earlier official Binance Support listing/trading announcement; or
- an independently canonical Binance historical representation with timestamp strictly before the access event.

Current exchange metadata is not historical proof. Search-engine result ordering is not an event definition. If no admissible prior-Spot proof is recovered, the asset/event fails closed for the clean candidate universe.

## Execution-cost provenance status

No credentials are authorized in this gate. Historical margin borrow interest/inventory may be classified only as:

- `PUBLIC_HISTORICAL_SOURCE_AVAILABLE`, if reproducible unauthenticated point-in-time history is proven;
- `CREDENTIAL_BOUND`, if the legitimate historical route requires authenticated USER_DATA/account credentials;
- `UNAVAILABLE`, if no legitimate historical route can be established.

Current margin rates or current inventory must never be substituted as historical launch-time costs/availability.

`CREDENTIAL_BOUND` does not create an executable strategy claim. It may allow a later explicitly **non-executable research Discovery** protocol, but no after-cost/live promotion can occur without a separate cost-resolution gate.

## Source-schema step

Before writing a production event parser, perform a deterministic source-schema census on the already-qualified structural articles only. This census may inspect official article body structure and short evidence snippets around source phrases, but no market outcome. Parsing rules are frozen only after this schema census.

## Terminal classifications

- `EVENT_SOURCE_ADJUDICATION_PASS`
- `EVENT_SAMPLE_INSUFFICIENT_AFTER_ADJUDICATION`
- `PRIOR_SPOT_PROVENANCE_FAILURE`
- `SOURCE_ACQUISITION_TECHNICAL_FAILURE`
- `PROVENANCE_FAILURE`

A pass does not authorize Discovery automatically. It permits only creation of a separately frozen Discovery protocol.

`NO_EDGE` remains forbidden in this gate.