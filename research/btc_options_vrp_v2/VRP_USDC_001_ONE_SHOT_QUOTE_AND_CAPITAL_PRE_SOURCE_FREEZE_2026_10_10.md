# BTC-OPTIONS-VRP-001 V2 — BTC_USDC 0.01 PAIR QUOTE, REALISTIC ENTRY COST & CAPITAL SOURCE GATE
2026-10-10. Frozen SOURCE-ONLY prior to querying fresh public Deribit option BBO. Original 192-week +10.43 IV-RV vol-point VRP discovery is not a trade-PnL result. Existing V2 return activation was explicitly UNDERPOWERED_PRE and revoked; no outcomes, settlement, future path or PnL permitted here.

## Immutable sampling and source selection
- Only Deribit public unauthenticated BTC_USDC linear options `public/get_instruments?currency=USDC&kind=option&expired=false` plus `public/get_index_price?index_name=btc_usdc`.
- Original route from source bank V0.1: **14–60 DTE**, select expiry **closest to 30D** (earlier expiry tie-break), then same-strike call/put nearest log-moneyness to index. Fixed **0.01 contract each leg**. No market, strike or expiration changes to rescue missing quotes. Selection made from current **instrument universe only**, without inspecting option premiums/outcomes.
- Public `public/get_order_book?instrument_name=<name>&depth=5` for **only selected call and put** and `BTC_USDC-PERPETUAL` price/hedge witness; for bid SELL executable proof require bid size >=0.01 in **each** option and for hypothetical immediate BUY exit require ask size >=0.01, prices finite, bestbid<=ask, source timestamp fresh within 30s **at response receipt**, no quote crossing. Record request start/end timestamps and raw SHA, not postfilled historical quote.
- This is a SATURDAY one-shot **diagnostic**; DO NOT claim that it satisfies the frozen THURSDAY 08:05 UTC prospective forward entry bank or write into `data/vrp_usdc_forward`. No reply on actual Thursday is fabricated.

## Pre-declared economics without outcomes
- Deribit official STANDARD options 3 basis points **of index underlying** per side, with each option fee capped at 12.5% of premium. BTC_USDC linear option leg marketable-entry SELL fee = `min(0.0003*index_price,0.125*option_bid_price)*0.01` USDC; quote premium received = bid*0.01. The hypothetical immediate cross-spread gross for unwinding same snapshot = `(option_ask-option_bid)*0.01` USDC. An illustrative immediate BUY-back roundtrip fee = `min(0.0003*index,0.125*option_ask)*0.01` USDC; **this is instant roundtrip microstructure friction**, not future exit PnL, not proof the original VRP is profitable.
- We do not assume combo fee discounts, post-only maker fills, user discounts, funding rebates, or known future option buyback price. At actual expiry fee may be different: official delivery fee 1.5bps underlying capped 12.5% option value. Do not claim a precise 30D strategy PnL or amount of time-weighted hedge funding from one snapshot.
- Frozen Standard Margin estimates, separately computed from current public MARK prices, index/underlying and strike, as previous V2 source baseline: **Call short IM** `max(0.15 - max(K-U,0)/U,0.10)*Index + CallMark` × .01; **Put short IM** `max((0.15-max(U-K,0)/U)*Index, 0.10*K)+PutMark` × .01. Sum is indicative gross leg margin, not verified joint portfolio portfolio-margin offset, cannot be equated to a hard worst loss, and must separately annotate missing perp hedge margin & slippage/funding.
- Source-only materiality outputs: call/put raw BBO, minutes-to-expiry, spreads USDC and percent of bid premium, quote-level min-size, entry premium and fee, instant unwind spread and fee, gross modeled initial margin and `margin/entry_premium`. **No profit, annualized return, option selling recommendation, future RV or implied edge.**
- Strict denominators: if positive quotes missing, crossed, outdated, below min lot or non-finite, mark `BLOCKED_QUOTE` and economic comparables UNKNOWN, not zero; if Deribit network API restricted, `SOURCE_ACCESS_BLOCKED` not no liquidity.

## Frozen sample power / promotion
- One valid source snapshot implies `PAIRED_ENTRY_BBO_SOURCE_PASS_ONLY`, NOT edge or MICRO-LIVE GO.
- Historical last known 2025 USDC trade tape: 0/52 strict 30D SELL+SELL anchors, 1/52 any-direction two-leg witness, direct simple weekly capital-normalized proof underpowered pre-outcome. Neither result is reset by new snapshot.
- To promote further: get independent outcome-blind multiple weeks of complete paired 0.01-depth snapshots and hedge quote from frozen Thursday bank, then freeze a new **capital-normalized execution/power estimand** before opening any future outcome. If not feasible, classify `DATA/CAPITAL_BLOCKED` and stop.

## Safety
Public GET only, no exchanges private API, no account reads, no wallets, orders, changes to balance, payments or live trading, 2026 future settlement/holdout opening, main merge, output-based selection, parameter changes.
Sources: https://support.deribit.com/hc/en-us/articles/25944746248989-Fees
https://support.deribit.com/hc/en-us/articles/31424932728093-Linear-USDC-Options
Original frozen bank `research/btc_options_vrp_v2/LINEAR_USDC_FORWARD_ENTRY_SOURCE_BANK_V0.1.md`.
