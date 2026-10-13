# CRYPTO LAB — PMR-001 INDEPENDENT SOURCE-FIRST VERDICT
Date: 2026-10-13
**STATUS: PUBLIC SOURCE PASS / EXTERNAL CASH INCENTIVE VERIFIED / PROFITABILITY UNPROVEN / NO LIVE GO.**

## Economic mechanism — genuinely new in this lab
Polymarket liquidity/rebate rewards pay makers for supplying competitive passive orders. Rewards are financed by sponsors/venue funds and taker fees. This differs from the prior POLY-COMBINATORIAL-ARB-001 arbitrage of all-YES package payout at resolution. No indicator-based prediction is assumed, but maker adverse selection is a first-order risk.

## Evidence: one independently pre-frozen Gamma source sample
Source https://gamma-api.polymarket.com/markets, `GET` only, public, no keys, fixed offsets 0 and 100, 100 per page, active and open, volume24hr descending. One GitHub Actions job:
- https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38404645524
- Job ID 115320957173, conclusion SUCCESS. Test fixtures 7/7 passed. Actual public source gate **SOURCE_PASS_REWARDS_EXIST_BUT_EDGE_UNPROVEN**.
- Snapshot UTC **2026-10-13T13:24:13.363378+00:00**.
- Returned markets: **200**; markets with accepting orders, positive active-dated clobRewards daily rate, positive min size and max spread and nonzero liquidity: **64**.
- Of 64, min quantity <=50 shares: **18**; <=100: **33**; <=200: **64**. Median qualified minimum: **100 shares**.
- Largest observed **single market total** daily program budget: **3,000 USDC/day**. Sum of selected qualified market-level daily programs: **32,415.002 USDC/day**. These are **market-wide advertised pools shared with competing makers**, NOT a reward claim, return forecast, user's expected earnings, user PnL, or cash obtainable by placing one order. No account score, competition weights, spreads on particular quote sides, fills, net portfolio return, or risk inventory were measured. Note the top-volume convenience sample may overstate access to reward programs relative to full market universe and includes varied outcome subjects, not only crypto.
- Snapshot showed some high-pool markets with 200-share min size. Select based on microcapital constraint rather than biggest headline prize.
- User expected net income: **UNKNOWN**; source does not show portfolio stakes or delivered share of program rewards. No account access, wallet or orders.

## Fee-funded maker rebate upper bound (conditional, not a simulated profit)
Official Polymarket currently lists Crypto taker fee parameter `0.07`, maker rebate share `20%`, zero nominal maker fee for eligible fee-enabled markets. At contract price p=0.5, a fully executed maker limit order of 100 shares represents **$50 traded notional**; fee-equivalent formula `100*0.07*0.5*(1-0.5) = $1.75`, *maximum nominal* rebate `20%*$1.75 = $0.35` = **70bps** of executed notional (if eligible fee pool fully applies to this fill; actual payouts depend on program details and market fee tier). A payout threshold of $1/day would need approximately 286 qualifying shares, or ~$143 executed, ignoring fees/risk and changes in probabilities. Maker rebates alone can be overwhelmed by even a ~70bps unfavorable price move; funded liquidity rewards also depend on relative score and the $1/day payout floor.
This calculation illustrates upper bound only; not PnL or an executable earning claim. Markets with different category fee rates have different percentages. Need verify account/venue eligibility before any deployment.

## Small capital: no quick GO
A 50 or 100-share minimum is a contract **quantity**, not a USDC minimum order nor affordable capital requirement. Underlying probabilities influence cost (price between $0 and $1); two-sided quoting can require holdings or collateral, size can exceed budget; competing order sizes dominate reward share; placing an eligible order does NOT guarantee $1/day or positive net after tail events.
Swiss CH not in published blocked-country table August 14 2026, but eligibility/regulation and KYC not verified; do not bypass geoblocks.

## Predefined next cheapest falsifier (requires new independent prospective freeze)
Without trading or wallets, pick at most 3 current markets with `rewardsMinSize<=100` by deterministic market ID ordering. For each, independently observe public executable bid/ask size, tightness and competing resting liquidity at **three scheduled consecutive snapshots**. Compute max hypothetical reward share under program's actual scoring, min side-specific required size and adverse fill impact under conservative price changes. Do not confuse orderbook snapshots with real competition-score payout data; if unavailable, report LIMITATION rather than invent. Keep false-positive guard: do not build bot until an independently causal, bounded net after-cost expectation exists and data access/legal eligibility are confirmed. No retroactive v0.1 modification or new Radar activation.

## FINAL
**SCORE: interesting source-accessible candidate for ONE prospective micro-cap cost/competition test, no capital authorization.** Maintain 0 active Radar motors. No main merge, no investment advice, no orders/exchange mutation/private endpoints.
First-party support:
- https://help.polymarket.com/en/articles/13364466-liquidity-rewards
- https://help.polymarket.com/en/articles/13364471-maker-rebates-program
- https://help.polymarket.com/en/articles/13364163-geographic-restrictions
