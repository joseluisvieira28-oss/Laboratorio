# MEME-DIAMANTE-005 — Mature Solana memecoins: executable-liquidity gate

**Frozen: 2026-11-18, before observing the ranked cohort.**
**Status: DATA RESEARCH GO; ECONOMIC NO-GO by default.**
No wallets, keys, signed transactions, purchases, orders, monitors, deposits or paid requests.

## Objective
Separate **eligible price/liquidity observation** from any claim of profitable trade execution. The prior reserve/flow policies lost on an optimistic quote proxy and never met economic gates. Do not reuse their wallet-count heuristic.

## Cohort and mandatory evidence
- Snapshot the **first 15** coins from CoinGecko's `solana-meme-coins` category, ranked by market cap at HTTP response time, without hindsight, handpicking or excluding weak entries silently.
- Fetch each official CoinGecko coin detail and extract its platform Solana **mint address**. Never identify tokens by ticker/name alone; missing mapping -> UNKNOWN.
- Retrieve matching mint-pairs from DEX Screener; identify highest-USD-liquidity pair **among pools actually involving the exact mint**, not the first pool. Capture all raw URLs/times/digests and aggregate summary. A known coin may have several concentrated-liquidity pools; one reported liquidity aggregate is NOT sell capacity.
- Read GeckoTerminal's pool endpoint once for each candidate (if mapping resolvable), compare pool address/price/liquidity when possible. Retain disagreement and all missingness.
- No coin name is a recommendation; ranking is merely a point-in-time observation.

## Fixed watchlist eligibility (not a buy signal)
- Age >= 7 days since chosen pool creation (not necessarily token creation).
- Single chosen pool's reported liquidity >= 150,000 USD and >= 50,000 USD 24h volume.
- At least 200 transactions (buys+sells) over last 24h if available; if missing, mark unknown.
- Stress-trade size: 100 USD. Size <=0.1% of displayed pool liquidity. **This is a screening rule, not a proof of actual price impact or executable depth.**
- A cross-source quote/pool-price comparison is diagnostic only; missing cross-source check is `UNVERIFIED`, not safe.
- Freeze all ranking/thresholds prior to run. Never optimize based on observed prices.

## Economic requirement that remains BLOCKED
The public DEX Screener and GeckoTerminal price, volume and USD TVL are **not** independent marketable executable buy/sell quotes. As of 18 Nov 2026 Jupiter's Swap V2 requires a developer API key for GET /order and GET /build; do not use credential workarounds.
A real GO needs source-authenticated as-of timestamped quotes for fixed size, actual route/venue fees, failure rate, MEV/slippage, gas/tips, **both** directions and a prospective 30-day held-out evaluation with >=200 executable signal/exit observations and positive lower confidence bound. A single snapshot does not reveal future returns.

## Sources
- https://www.coingecko.com/en/categories/solana-meme-coins
- https://docs.dexscreener.com/api/reference
- https://api.geckoterminal.com/docs/index.html
- https://github.com/jup-ag/docs/blob/main/swap/index.mdx
- https://arxiv.org/abs/2609.10246

Do not merge automatically, run scheduled jobs, present token recommendations, or claim profits.
