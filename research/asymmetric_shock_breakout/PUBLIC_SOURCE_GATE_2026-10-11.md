# SHOCK-BREAKOUT-ASYM-001 — MEXC PUBLIC SOURCE/DATA GATE
Date: 2026-10-11
Status: DOC_ENDPOINTS_VERIFIED / DATA_RUNTIME_UNVERIFIED / EXECUTION_HISTORY_BLOCKED
Scope: Public, unauthenticated API documentation only. No outcome prices read.

## Official MEXC Futures public endpoints

1. GET /api/v1/contract/depth/{symbol}
   - Docs: https://www.mexc.com/api-docs/futures/market-endpoints/get-contract-order-book-depth
   - Rate limit documented: 10 calls per 2 seconds.
   - bids/asks, version, system timestamp; returns a CURRENT snapshot.
   - Can support future shadow execution with a timestamped intake IF actual
     public reachability, freshness, continuity, position-size/liquidity and
     operational durability are confirmed.

2. GET /api/v1/contract/depth_commits/{symbol}/{limit}
   - Docs: https://www.mexc.com/api-docs/futures/market-endpoints/get-the-last-n-depth-snapshots
   - Rate limit: 20 calls / 2 seconds; returns most recent depth versions,
     not an assured years-long timestamped historical BBO archive.
   - No safe inference that a future quote was fillable in the past.

3. GET /api/v1/contract/kline/{symbol}
   - Docs: https://www.mexc.com/api-docs/futures/market-endpoints/get-candlestick-data
   - Public, 20 calls / 2 seconds, up to 2000 bars/request.
   - interval Min1, Min5, Min15, Min30, Min60 and longer.
   - start/end parameters are documented as UNIX SECONDS, NOT milliseconds.
     (Reject alternate timestamp units until real transport has been tested.)
   - OHLC may prove broad price displacement or event occurrence, but cannot
     establish live bid/ask execution, intra-bar stop-first ordering,
     fillable size, jump-through-stop loss, or cancellation latency.

4. https://www.mexc.com/api-docs/futures/market-endpoints/
   - Documents that Market module endpoints do not require authentication.
   - No authenticated APIs needed for the source gate.

## Fee authority and execution gap

https://www.mexc.com/en-GB/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742
API maker 0.06%/side and taker 0.08%/side effective June 1, 2026;
different from website/app fees. Conservative taker/taker = 16 bps RT
before additional execution costs. Fee availability and exact pair/account/
region need separate authority before real execution; prohibited here.

## Gate results

- PUBLIC_MARKET_ENDPOINTS_DOCUMENTED: PASS.
- PUBLIC_KLINE_SCHEMA_DOCUMENTED: PASS.
- BBO_LIVE_READ_ONLY_REACHABILITY: UNTESTED.
- BBO_HISTORICAL_DATE_RANGE: UNVERIFIED / not documented as complete.
- BBO_STOP_TP_PATH_RECONSTRUCTION: BLOCKED with OHLC alone.
- SYMBOL_RULES_AND_LIQUIDITY_VS_SIZE: UNTESTED.
- SOURCE_TIMESTAMP_FRESHNESS: UNTESTED.
- OFFICIAL_SHOCK_EVENT_TIMESTAMP: SOURCE-TO-BE-SELECTED.
- PRE-OUTCOME_TRIGGER_AND_EXIT_FREEZE: NOT CREATED (source feasibility first).
- OUTCOME_TEST: NOT AUTHORIZED / NOT RUN.

Conclusion: SOURCE_GATE_PARTIAL; do not promote or present an
OHLC-only simulated 4R result as executable strategy PnL.
To proceed: demonstrate exact real-time public BBO intake and immutable
forward receipt durability, choose one official shock source,
then PRE-FREEZE a single causal protocol before reading any future
outcome. Do not steal event observations from LICP or sealed 2026 holdouts.
