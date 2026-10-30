# PMR-002 — POLYMARKET RESTING-LIQUIDITY COMPETITION V0.1
2026-10-30. FROZEN BEFORE ANY NEW MARKET SOURCE OBSERVATIONS. Separate from PMR-001 prior census.

Mechanism: Polymarket sponsor/venue pays liquidity rewards pro rata to qualifying competitive resting orders. PMR-001 existing real source, 13 October: 200 sampled top-volume markets, 64 active reward programs, 33 with <=100 share minimum. These are shared pools, NOT user earnings. Different from directional alpha/complete-set arbitrage. Source first and full adverse-selection risk later. Kalshi official rewards ineligible to non-US participants; do not pitch as accessible to Swiss retail.

Selection: exactly two public Gamma GET pages (active=true, closed=false, order=volume24hr descending, limit=100, offset=0 and 100) from https://gamma-api.polymarket.com/markets; one request per page, no retries. Filter active, not closed, acceptingOrders, enableOrderBook, active-dated clobRewards positive, rewardsMinSize strictly positive <=100 SHARES, rewardsMaxSpread positive, liquidity positive, exactly two valid decimal clobTokenIds. Sort by integer market ID ascending and select the FIRST THREE, not highest pools. Fewer than three -> SOURCE_INCOMPLETE. No replacement after results.

CLOB evidence: for chosen 3x2 exact tokens, three public GET rounds, starting at offsets 0,20,40 seconds after selection; sequential stable marketID/token order, 18 calls max, each only https://clob.polymarket.com/book?token_id=exact_token from Gamma, no auth, no POST, timeout 8sec, body max 1.5MB, HTTP200. Preserve UTC receive timestamp, original raw SHA256, bytes, public book hash and source timestamp, market+asset identity; no future prices or trading outcomes. Require bid & ask both present with strictly positive top size and 0<bid<ask<1. Record all blocked cases without replacing market or lower gate. Observations are NOT simultaneous or atomic.

Descriptive diagnostics ONLY: top bid, ask, spread cents, visible competing best bid/ask size, indicative 100-share limit order bid value, and 100/(100+visible existing best-bid size) as labeled VISIBLE-SIZE-FRACTION NOT REWARD SCORE, NOT REWARD SHARE, NOT EXECUTABLE EXPECTATION. Respect original rewardsMaxSpread reported units without inventing unit conversion. The displayed daily pool is shared across makers; never compute user ROI, guaranteed income or expected rewards from it. No paid payout/score evidence, no own account or fills. MinSize in shares is not invested capital or guaranteed earning.

Predeclared gate: SOURCE_COMPLETE_VISIBLE_COMPETITION_ONLY if exactly 3 eligible IDs and 3 rounds x 6 books all identity-valid with two-sided bids/asks and positive size. Else SOURCE_BLOCKED on transport/schema or SOURCE_INCOMPLETE on candidate/book shortage. In ALL cases ECONOMIC_EDGE_UNPROVEN, NO_LIVE_GO. No hindsight relaxation, no new asset selection, no posthoc cherry picking. Reward scoring needs real order-time, qualification, market rewards, relative maker participation, fills, adverse selection, inventory and fees; 3 snapshots cannot prove those. Switzerland does not appear in current platform restricted-country list but that is NOT proof of regional legal/account eligibility. No bypass geography.

Prior economic exclusions: Options V2.1 BTC 10x MARKET/MARKET NO-GO PR #202, signed 2025 OOS +5.04bps BASE10 vs 16bps reference taker/taker and exact profit sensitivity -0.79bps before spreads; NFP Surprise 2021 frozen sign-vote negative both BTC/ETH, no OOS extension. Do not relabel them as fresh discoveries.

Zero orders, trading, accounts, wallets, exchange mutations, sensitive endpoints, deposits, login, keys, funds, scheduling, main merge, protected 2026 data, NVIDIA overlap. One bounded public CI only.
Official refs:
https://help.polymarket.com/en/articles/13364466-liquidity-rewards
https://help.polymarket.com/en/articles/13364163-geographic-restrictions
https://institute.polymarket.com/data
https://help.kalshi.com/en/articles/13823851-liquidity-incentive-program
