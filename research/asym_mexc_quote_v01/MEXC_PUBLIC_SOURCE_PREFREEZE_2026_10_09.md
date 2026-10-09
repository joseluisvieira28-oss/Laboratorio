# ASYMMETRIC PAYOFF LAB — MEXC FUTURES QUOTE SOURCE GATE V0.1
Date: 2026-10-09
State: PRE-SAMPLE FREEZE / SOURCE_ONLY / RESEARCH.
Independent family of venue/source feasibility, NOT a replacement for BINANCE BTC-CONVEX V0.2 and NOT a transfer/validation of a trading mechanism.
Binance V0.3 USD-M official-depth source received HTTP 451 from GitHub Actions; remains SOURCE_BLOCKED, no alternative-host bypass attempted.

## Source and frozen universe
Public, no-auth read-only MEXC CONTRACT data at https://contract.mexc.com :
GET /api/v1/contract/ping (time); GET /api/v1/contract/detail?symbol=<symbol> (contract size, minVol, volUnit etc); GET /api/v1/contract/depth/<symbol>?limit=20 (price, CONTRACT COUNT, snapshot timestamp).
BTC_USDT, ETH_USDT, SOL_USDT, BNB_USDT only. No replacement assets or endpoints after results. Official docs https://mexcdevelop.github.io/apidocs/contract_v1_en/ and https://www.mexc.io/api-docs/futures/market-endpoints/get-contract-order-book-depth .
No spot/futures conflation; MEXC futures price levels are in USDT per BASE asset and depth quantities are CONTRACT UNITS. Thus NOTIONAL = contracts * contractSize (base/contract) * price. A '10' volume order is 10 contracts, NOT 10 BTC or 10 dollars.

## Source/data gate
Before first observation freeze: four independent GET depth snapshots, one per symbol. Local UTC request and receive time and provider snapshot timestamp must both be logged; if latency >2000 ms, age outside [0,2000] ms, crossed/non-descending bids/non-ascending asks, nonpositive sizes, unknown contractSize, minVol, volUnit, min quantity, contract status or incompatible timestamp, fail-closed.
Economic *feasibility-only* scenarios: 10,25,50,100 USDT hypothetical long entry notionals, no leverage, market BUY at ASK and SELL at BID using same-snapshot depth.
For each scenario, quantize contract count to declared volume unit, check minimum volume/max and observed top-20 depth, compute BUY/SELL VWAP, same-snapshot spread/crossing cost. If contract metadata fields unavailable, leave outcome SOURCE_BLOCKED; never guess contract size from price.
No fees claimed as real or zero. Original BTC Convex Binance cost model not portable. Record SOURCE-ONLY bid/ask book crossing costs; MEXC taker fee tier, fills, funding, slippage not independently bound. No executable NET edge claim.

## Classification and next gates
SOURCE_SAMPLE_PASS if authenticated-free public clock, detailed contract filters, timely valid depth and all fixed small-size scenarios succeed for all four contracts. Otherwise SOURCE_BLOCKED with detailed reasons.
Any PASS means merely PUBLIC_SOURCE_FEASIBLE, no market access/trade permission or historical cross-venue transfer.
A later *new scientific* MEXC-specific strategy requires a distinct frozen signal/cost/exit/funding contract, quote-at-decision timestamps, order-size feasible risk limits, append-only point-in-time logs, clean OOS and forward, independent actual-fee schedule. No retrofit based on known Binance strategy results.
No orders, private reads, exchange mutation, capital, login, credential, main merge, or Render changes.
