# PMR-001 — Polymarket remunerated limit-order liquidity — single cheap source gate

Date 2026-10-13. Operator wants a new **TRADING** income mechanism that is economically distinct from failed Crypto Lab edge-fishing.
Research only: no orders, capital, wallet, login, private requests, automations, Render, main merge, changes to 8 retired Radar motors, Windows process or outcome-peeking.

## Causal payer
1. Sponsor/Polymarket-funded **Liquidity Rewards**: a daily incentive pool is distributed to qualifying passive orders, conditional on min-size/spread and *relative score* vs rival makers. Resting is insufficient if daily individual award < $1, which is forfeited rather than rolled forward.
2. **Maker Rebates**: qualifying filled passive orders receive a fee-funded fraction of taker fees; for crypto category currently 20%, with $1 per-day minimum, not a guaranteed flat percentage for every passive trade. Formula official: `fee_equivalent=C*0.07*p*(1-p)`; at `p=0.5`, max crypto rebate at 20% = $0.0035 per share or **70 bps of $0.50 fill notional**. Thus a 0.70% adverse fill plus liquidation/unwind exposure, spread, gas or other costs can erase this gross incentive. All numbers subject to market fee schedule.
3. Maker earnings must be compared with realised adverse selection, asymmetric news price moves, inventory held to settlement, unfilled/cancelled orders, market availability, gas and platform settlement. Never equate a positive incentive with net edge.

This is *not* POLY-COMBINATORIAL-ARB-001 V0.8: that searched a price underpayment vs 1 USDC maturity across all YES outcomes, paying taker fees and suffering multi-leg legging. PMR-001 is a sponsor/venue-funded rebate mechanism earned by making liquidity.

## Eligibility
As of 2026-08-14 Switzerland (CH) is absent from the platform's published 39 wholly blocked countries, but live account and legal eligibility is NOT proved; country restrictions and local law/KYC can change. No geographic circumvention.

## First read-only MVE — frozen BEFORE reading samples
Data: at most **two public Gamma API `GET /markets` batches**, both `active=true&closed=false`, sorted by `volume24hr` descending, `limit=100`, `offset=0,100`. This is a top-volume convenience sample, **not a representative market census**, never a full profitability claim.
No private CLOB rewards/account endpoints, API credentials, authentication or other data sources in this frozen test.
For each row require active, not closed, acceptingOrders, clobRewards with positive active-dated `rewardsDailyRate`, numeric `rewardsMinSize>0`, `rewardsMaxSpread>0`, nonzero liquidity, and meaningful spread. If schedule dates cannot be parsed -> schema blocked, don't silently treat as valid.
Count:
- returned markets, qualifying positive-reward configured programs, configured minSize share distribution, maximum recorded per-market daily payout and mean/median market-level payout.
- flag `minSize <=50`, `<=100`, `<=200` **in shares**, indicative only. These are NOT account minimum cash/margin; satisfying minSize does not guarantee rewards due to relative score and two-sided quote burden.
- rewards that appear high are market-wide pools shared pro-rata with competing makers, NOT user expected earnings. A zero allocation is possible.
- do not infer bid/ask executable price from a quote aggregate; no order book snapshots in v0.1.
Response size cap 3MB, hard timeout per call 10s, one attempt per page, no automatic retry.

## Decision labels
- `SOURCE_BLOCKED`: transport or schema failure; stop. CI success means only accurate classification.
- `SAMPLE_ZERO_ACTIVE_REWARDS`: public sample complete but no qualified active reward programs.
- `SOURCE_PASS_REWARDS_EXIST_BUT_EDGE_UNPROVEN`: at least one qualifying active program; next *distinct preregistered* independent CLOB liquidity/score/fill-adverse-selection test necessary before even micro-live; **NO GO** for capital.
- High share minimum >100 in ALL qualifying markets => `MICROCAP_100SHARES_NOT_ELIGIBLE_IN_SAMPLE`.
- In every outcome, `profitability_verdict=UNPROVEN`, `orders_created=false`, `trading_authority=NONE`.
- **Hard stop after one current sample**. No paid API, no wallet, no trading.

## Primary first-party sources
- https://help.polymarket.com/en/articles/13364466-liquidity-rewards
- https://help.polymarket.com/en/articles/13364471-maker-rebates-program
- https://help.polymarket.com/en/articles/13364163-geographic-restrictions
- https://github.com/Polymarket/py-sdk/blob/main/src/polymarket/models/gamma/market.py — public response fields.
- https://gamma-api.polymarket.com/markets (public market metadata; sample only).
