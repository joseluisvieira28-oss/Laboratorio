# PMR-001 — THREE PUBLIC ORDER BOOKS: SHORT ECONOMIC VERDICT

Date/time: 2026-10-13 14:22:58–14:23:18 UTC. Protocol frozen BEFORE NEW CLOB observations.
Research only; no orders, user account, wallet, live trading, protected outcome use, mutation or main merge.

## Verified source and method
- Parent one-shot V0.1: [run #38404645524](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38404645524), public market rewards 64/200 markets, 33 with min <=100 shares, 18 <=50 shares; source PASS, profit UNPROVEN.
- Freeze V0.2 `PMR001_V02_THREE_BOOKS_PROSPECTIVE_FREEZE_2026-10-13.md` published on commit `da56dd84bfe28a7b4d82403708616f14c605a707` BEFORE new book observations. Deterministic 3 lowest numeric market IDs from a fresh 2x100 Gamma source sample with min reward shares <=100. No switching markets after reading price.
- [Real public market book run #38412840289](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38412840289), job #115349380532, SUCCESS. 13 offline tests PASS. Output artifact `PMR001_V02_THREE_PUBLIC_BOOKS_20261013` ID `11823072553`, SHA256 `3673314307f775162b3aa82b82541ff1132b04fd7e415a49f709ff14835ead4a` (artifact zip digest), no live receipts.
- 3 CLOB POST /books public read-only snapshots at UTC 14:22:58.237857, 14:23:08.205596, 14:23:18.224688; 3 market pairs YES+NO in each snapshot (9/9 valid pairs, no substitutes). All provider hashes/timestamps included in raw CI artifact. Real order execution: **0**.

## Summary, measured at T0 and invariant best bid/ask across all 3 snapshots

| Market | Slug | Shared market pool USDC/day, NOT our payout | Min shares per side | YES top bid/ask | NO top bid/ask | Counterfactual 50-share YES + NO bid capital | Top3 YES bid shares | Top3 NO bid shares |
|---|---|---:|---:|---|---|---:|---:|---:|
| 562802 | Democratic Party control House after 2026 midterms | 222 | 50 | .90/.91 | .09/.10 | 49.50 USDC | 2,203,498.29 | 3,402,006.69 |
| 562803 | Republican Party control House after 2026 midterms | 278 | 50 | .09/.10 | .90/.91 | 49.50 USDC | 3,445,585.44 | 2,160,501.05 |
| 608545 | Lamine Yamal Ballon d'Or 2026 | 9 | 50 | .303/.307 | .693/.697 | 49.80 USDC | 624.97 | 92.16 |

NB: top-three book levels are **aggregate displayed liquidity**, not distinct competing maker identities or exact reward-scoring positions. YES+NO book sides can mirror economic exposures; sizes should not be summed across token books as independent competitor inventories. Prices unchanged during the 20-second window; some book hashes changed. None of these are evidence of price stability for 24h.

## Hard economic reality
- Market 562802 and 562803: millions of displayed shares at first three top bid prices vs our hypothetical **50 shares**. Heavy quoted depth is a competition risk, not measured opponent reward score. The two markets are politically correlated, not two diversified edges. Their YES midpoints (~0.905 and ~0.095 respectively) are in the probability extremes where Polymarket official help requires **orders on both sides** for liquidity rewards, raising inventory/collateral and adverse-execution requirements.
- Market 608545: less visibly crowded, but total daily market payout is only **9 USDC to ALL makers**. Merely to cross $1 payout threshold from *that market alone*, participant must secure >11.11% of its distributed daily pool; actual individual score UNKNOWN. The visible top3 quantity on one side is 624.97 YES shares and 92.16 NO shares; exact normalized score cannot be determined from anonymized price levels.
- Hypothetical bid/bid both tokens require ~49.50–49.80 USDC of submitted buy limit capacity if both accepted. This is NOT a safe, guaranteed-loss-limited box, an execution guarantee, actual collateral, or actual total working capital; only one leg filling leaves unhedged outcome exposure. No maker rebate without actual taker taking our liquidity; no free implied reward per order.
- Visible YES/NO best bid totals 0.99 (first two) and .996 (third). If BOTH hypothetical passive bids filled at their limits in equal quantities, the resulting paired settlement payout arithmetic would generate up to 0.50 or 0.20 USDC **gross theoretical pair-completion margin** per 50-shares before other costs. But independent conditional fills are not assured, not atomic, and leg risk can greatly exceed this margin. This is a counterfactual, not a positive expected return claim. Note prior complete-set pricing arbitrage had execution fragility; do not rebrand this as a proven arbitrage edge.
- Individual maker payout, expected realized PnL, probability that both orders fill, inventory liquidation cost, adverse selection, owner-level weights, quote uptime, geographic/account eligibility and actual wallet cash availability: **all UNOBSERVED**.

## Adjudication
- Source: **BOOK_COMPETITION_VISIBLE_NET_UNPROVEN** and **all_source_complete=true**; PASS for accessing live public books only.
- Small-size basic order placement capital proxy: **<100 USDC** in the observed sample, not live feasibility.
- Economically defensible automated income: **NO DEMONSTRATED POSITIVE NET EXPECTANCY**. This implementation has insufficient evidence to warrant any bot, new Radar motor, capital or persistent monitor.
- Stop further source-only tweaking and infrastructure building; the only meaningful continuation would involve directly observing user-level real reward score and fill/adverse-selection distribution through a newly authorized independent study. **Do not ask user for wallet access or spend money absent separate explicit consent.**
- Distinguish **NO CAPITAL GO** from **SCIENTIFIC NO-EDGE**: the observed sample does not establish that Polymarket reward making is unprofitable for all participants. Do not claim that.

## Official rules
https://help.polymarket.com/en/articles/13364466-liquidity-rewards — daily reward only paid if individual accrual >=$1; outside 0.10–0.90 midpoint requires both sides.
https://help.polymarket.com/en/articles/13364471-maker-rebates-program — maker rebates need an actual matched maker fill and per-market execution share.
