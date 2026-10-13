# PMR-001 — V0.2 PROSPECTIVE THREE BOOKS / MICROCAP FALSIFICATION FREEZE
Date 2026-10-13. Created BEFORE access to new CLOB books. Research-only. NO ORDERS, no wallet, no login, no private reads, no live authority, no money.

## Parent
V0.1 PR #206 and 2026-10-13 UTC 13:24:13 immutable sample: 200 Gamma markets, 64 public positive liquidity incentive configurations, 33 <=100 share min, 18 <=50 share min. It **does not** establish capital feasibility, individual score allocation or profit.

## One-shot selection, frozen before results
1. NEW independent prospective source refresh, exactly 2 GET https://gamma-api.polymarket.com/markets requests, each active=true&closed=false, order=volume24hr descending, limit=100, offsets 0 and 100.
2. Filter with V0.1 qualification AND rewardsMinSize <=100 shares; check acceptingOrders true, enableOrderBook true, fresh active positive clobRewards daily program, liquidity>0. Require two parseable clobTokenIds, expected conditionId. Sort qualifying by numeric Gamma market id ascending, take EXACT FIRST THREE. **No substitution** if token book unavailable, regardless of result.
3. For 3 selected market IDs: precisely THREE publicly unauthenticated POST https://clob.polymarket.com/books, each with both YES/NO token IDs of all 3 markets (6 tokens), at target T0,+10sec,+20sec, no retries, max 120sec total; no signing or order endpoint. HTTP max 12 sec, max 2MB JSON response per call. POST /books is read-only market data.
4. Validate CLOB identity per market and asset token, book hash/timestamp, positive tick size, parseable bids/asks. Record any gap as incomplete source (not zero opportunities). Preserve all three timepoints, no best-only selection. Never infer a filled order from quoted depth.
5. Per market/timepoint, capture YES and NO top best bid/ask, spread in cents, summed top-3 displayed bid quantities, provider timestamps and hash; calculate hypothetical cost to place a minimum-sized YES bid and NO bid at each best bid. Each limit quote is *counterfactual*: it was never on the book and never accrued a single reward. Mark present executable ask depth separately. This simple two-sided buy quote is a capital proxy only, NOT the exact Polymarket combined YES/NO/short inventory scoring/collateral requirement. If best bid/ask missing or crossed, fail closed for that market/timepoint.
6. Market-wide daily rewards are pro-rata across maker accounts and paid only if individual daily total >=$1. Full reward pool per market is NEVER individual revenue. Since public order books expose no maker owner IDs, no exact scoring share, actual order survival probability, fill rate or adverse selection, leave estimated individual revenue and expected net profit NULL; no invented equal-share assumption, spread capture, 24h extrapolation or fill probability.
7. No actual inventory, capital, wallets, trades, contracts, exchange mutation, onchain interaction, protected outcome data, fee-tier assumptions or postoutcome tuning. Market-maker rebates require actual qualifying FILLS and are NOT credited to orders simply resting. Do not combine rebate credit with resting-liquidity reward without matched historical fills.

## Decision rule
- If public Gamma or all 3 book batches fail: `SOURCE_BLOCKED`.
- If no >=3 qualified fresh Gamma IDs: `INSUFFICIENT_MICROCAP_MARKET_SAMPLE`; stop without opportunistic resampling.
- If at least one selected market has all 3 books valid: `BOOK_COMPETITION_VISIBLE_NET_UNPROVEN`; show 3 snapshots and USDC capital proxies. Mixed partial valid sources are visibly flagged; NO claiming full 3/3 observation coverage if not.
- If no market has complete paired YES/NO book at all 3 times: `CLOB_BOOK_ACCESS_OR_IDENTITY_BLOCKED`.
- If a 2-sided min-share bid proxy requires >100 USDC collateral in all observed selected market/timepoint pairs, flag `MICROCAP_100_USDC_INFEASIBLE_IN_SAMPLE`. This is illustrative only; no buyer affordability claim from reward shares alone.
- If any selected market has a reasonable cost proxy, STILL **NO LIVE GO / NO PROVEN EDGE** due missing user reward scoring and maker-fill adverse selection.
- Always keep `profitability_verdict=UNPROVEN`, `user_daily_reward_usdc=null`, `user_net_pnl_usdc=null`, `trading_authority=NONE`. 0 Radar motors.

## Clauses for economically meaningful follow-up
Before any capital simulation: independent pre-registered resting maker order survival/competitor quote movement measurement, account-level payout scoring visibility with authorized source if necessary, probable exposure inventory mark-to-market under stress, executable unwind and actual collateral constraints; local regulatory/geographic eligibility must be checked. Failure to observe these means **do not build a bot**.

Official source methodology:
https://help.polymarket.com/en/articles/13364466-liquidity-rewards
https://help.polymarket.com/en/articles/13364471-maker-rebates-program
CLOB docs POST public books https://www.polytest.io/docs/polymarket-api/clob/post-books (secondary reference; verify runtime schema, not unquestioned authority).
