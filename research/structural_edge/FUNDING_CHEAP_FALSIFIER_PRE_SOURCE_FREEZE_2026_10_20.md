# CROSS-VENUE FUTURES FUNDING — ONE-SNAPSHOT CHEAP FALSIFIER FREEZE
2026-10-20; status PRE_SOURCE / PRE_OUTCOME; no 2026 historical holdout.
**Scope:** one currently-observable source-only scan of USDT linear perpetuals BTC, ETH, SOL, two venues: OKX and Bybit. This is a strictly limited source-recovery/feasibility replication of prior funding-carry concepts; **not** a new independent economic family nor an OOS strategy track record.

**Causal economic mechanism:** longs pay shorts at a positive funding rate; shorts pay longs at a negative rate. Hedged same-base perp long one venue and short another MAY collect a funding differential if both positions survive until settlement. Basis risks, marks, collateral, and exits can swamp the payout.

**Fixed venue instruments:** OKX BTC-USDT-SWAP / ETH-USDT-SWAP / SOL-USDT-SWAP; Bybit BTCUSDT/ETHUSDT/SOLUSDT, category=linear. Only endpoints: OKX GET `/api/v5/public/funding-rate`, `/api/v5/market/books?sz=5`, Bybit GET `/v5/market/tickers`, `/v5/market/orderbook?limit=5`, `/v5/market/instruments-info`, exclusively public read-only. No auth / account reads / POST.

**Predefined source checks:**
- full successful API status/schema, positive/uncrossed bid/ask top and positive sizes; OKX book ts and Bybit exchange response server time max age 30s vs UTC runner; six books acquired within 30s; no fallback sources;
- estimated/current funding rates available on BOTH venues, same future settlement timestamp within 2 minutes; both instruments must be 8h funding interval (OKX next − prev = 8h, Bybit fundingInterval=480 minutes);
- publish raw JSON only as private action artifact with SHA256, not public repository; derived sanitized receipt may contain prices/rates/times; tamper trace.
- if any source fails, mark that pair SOURCE_BLOCKED; never interpret empty source as zero funding or no economic opportunity.
- ONE observation only. No repeating until passing thresholds; no polling or selection of more favorable hours.

**Predetermined friction benchmark, expressly hypothetical:** 6bps taker each of 4 fills (entry & exit x 2 venues) = 24bps of equal per-leg notional, before bid/ask, spread, basis risk, FX, funding collateral and slippage. This is NOT certified user fee schedule and cannot certify a real GO. Add an illustrative top-of-book roundtrip spread cost = spread_okx/mid_okx + spread_bybit/mid_bybit (each in bps) with NO claim future exit books unchanged. This double-side roundtrip reference counts 4 crossing spreads at paired entry/exit.
- optimistic one-settlement funding differential (bps) = abs(rate_OKX - rate_Bybit)*10,000; sign assignment for hedged pair based on which has higher rate. Both venue next-settlement times must coincide.
- **screen margin** = optimistic predicted differential − (24bps + current roundtrip-spread proxy). Print in receipt; NO commissions/actual cashflows certified.
- If margin <=0: ONLY `SINGLE_INTERVAL_ESTIMATE_BELOW_FROZEN_HURDLE` for this instant, these assets and this conservative cost benchmark; never economic NO_EDGE for all markets.
- If margin >0: ONLY `SOURCE_SCREEN_POSITIVE_NOT_EDGE`; needs independent frozen prospective actual settled funding, executable bid/ask both entry and exit, consistent size, mark, exposure/hedge and account tier. NEVER LIVE GO.

**Primary result:** number of 3 pairs passing all source checks, number positive screen and minimum/maximum margin bps, with exact timestamp, SHA hashes, errors. No post-hoc changes to symbols, fee assumptions, data freshness, funding interval or exchange. Any change/new broader experiment demands new freeze BEFORE new data, and no historical holdout use.

No capital, wallets, logins, account reads, orders, exchange mutations, Render, main merge or 2026 protected historical holdout.
