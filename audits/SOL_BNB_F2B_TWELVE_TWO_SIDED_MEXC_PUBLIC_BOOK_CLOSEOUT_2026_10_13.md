# SOL / BNB — F2B 12 SNAPSHOTS × TWO-SIDED PUBLIC MEXC DEPTH — FINAL VERDICT
Date 2026-10-13 UTC. Trading authority NONE. Frozen **before snapshots** at `research/convex_sol_bnb_gates_v01/F2B_TWOSIDED_12SNAPSHOT_PREOUTCOME_FREEZE.md`, commit `1f2071fc1a1543b1043b993e432758e178107d25`. This is execution *source-only* research, not actual order/fill evidence or economic forward alpha.
CI and real public sourcing: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38437485875 **SUCCESS** — 2/2 synthetic contract tests PASS, independent 12-timed-snapshot jobs per symbol SUCCESS; requests spaced >=5 monotonic seconds and 20 public book levels each side with raw JSON SHA256, valid source timestamp <=2s age and request latency <=3s.
SOL receipt: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38437485875/artifacts/11833787557
BNB receipt: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38437485875/artifacts/11833517721
No authentication, account/balance/positions, user fee lookup, wallets, orders, private endpoint, country eligibility, venue mutation or cash.

## Twelve observations per symbol, same frozen paper notionals
| Attribute | SOL_USDT | BNB_USDT |
|---|---:|---:|
| Public valid two-sided fresh books | 12/12 | 12/12 |
| Observed median ask-bid spread | **0.93127bps** | **1.34571bps** |
| Min / max spread | 0.93088 / 2.79369 bps | 1.34562 / 1.34617 bps |
| **100 USDT** paper order: sufficient visible *both ask and bid* 20-level quantities | **12/12** | **12/12** |
| **2,000 USDT** paper order: sufficient visible *both ask and bid* 20-level quantities | **0/12** | **0/12** |
| Hypothetical frozen BASE round-trip friction hurdle ≈ spread + two-sided 8bps taker fee + 2bps slippage per side at median spread | **20.93bps** | **21.35bps** |
| Hypothetical frozen STRESS friction hurdle ≈ spread + 16bps fee + 5bps slip per side | **26.93bps** | **27.35bps** |
These hurdles are illustrative cost algebra from mid price and visible quote, not real roundtrip fill costs; benchmark must also include realized slippage/impact on entry and exit, overnight funding, forced exits, depth fade, spread dynamics and rejections.
Book parsing source: MEXC public depth row [price, number_of_orders, CONTRACT_QUANTITY]; **third** field used, never count of orders as executable quantity. Contract size SOL .1 base/contract min 1 step 1; BNB .01 base/contract min 1 step 1. At initial sample paper 100 USDT round up to 10 SOL contracts ≈107.25 USDT at ask, 14 BNB contracts ≈104.16 USDT; 2k requires 187 SOL or 269 BNB contracts. First 20 public ask levels exposed 47 SOL and 51 BNB contracts at initial sample, insufficient for 2k, but not a claim of full orderbook or impossibility of 2k fills.

## Fees: deliberately unresolved user-specific API schedule
Same initial public MEXC `/contract/detail/country` returned reported takerFeeRate 0.0002 and makerFeeRate 0 at one instance, while published eligible API Futures June 1 2026 schedule states maker 0.06% / taker 0.08% and website/app promotions do not override API-specific fees. Source https://www.mexc.com/en-GB/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742 . Only public/anonymized source used. Without authenticated account fee schedule, frozen historical model **8bps taker each side** is NOT lowered to marketing/public contract fields after seeing favorable results.

## Scientific inference / blockers
The 100 USDT paper entry/exit target was visible on both sides of twelve sampled 20-level public books, suggesting mechanical minimum-contract feasibility for a small unlevered research position on **that source snapshot**, not account entitlement/exchange acceptance. An actual trade could be rejected or gap over stop; public visibility != queue priority or assured fill. The same publicly visible 20-level slice did not cover hypothetical 2k notional in any of the 12 samples. Do not infer route viability for large account without fuller orderbook / time-matched position size, forced exit and contract limits.
No guarantee these snapshots coincide with an actual V5 SOL1h/BNB4h LONG signal. No historical 2023–25 matched public bid/ask snapshots; these are October 13 2026 and cannot certify old hypothetical source prices. No spot and no API private requests. Nothing changed to 4% initial stop or 12% nonlatched trailing.

**Verdict: PUBLIC_TWO_SIDED_SOURCE_PASS_FOR_100_USDT_SIZE_ON_12_SNAPSHOTS / NO_TOP20_BOOK_COVERAGE_FOR_2K_USDT / NO_FILL_OR_FUTURE_ALPHA_PROOF / NO MICRO-LIVE GO.**
